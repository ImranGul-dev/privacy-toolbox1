from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta, timezone
import json
import mimetypes
import aiofiles
from fastapi import Request, Response
from app.core.config import settings
from app.core.security import random_id, safe_filename, validate_ext, validate_file_signature, validate_id, token_for, verify_token

BASE = settings.storage_dir
UPLOADS = BASE / 'uploads'
OUTPUTS = BASE / 'outputs'
JOBS = BASE / 'jobs'
for p in (UPLOADS, OUTPUTS, JOBS):
    p.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def upload_session_from_request(request: Request | None) -> str:
    if request is None:
        return ''
    value = request.cookies.get(settings.upload_session_cookie_name, '')
    try:
        return validate_id(value, label='upload session')
    except ValueError:
        return ''


def ensure_upload_session(request: Request | None, response: Response | None = None) -> str:
    sid = upload_session_from_request(request)
    if not sid:
        sid = random_id('anon')
        if response is not None:
            response.set_cookie(
                settings.upload_session_cookie_name,
                sid,
                httponly=True,
                secure=settings.auth_cookie_secure,
                samesite='lax',
                max_age=60 * 60 * 24,
                path='/',
            )
    return sid


def owner_id_for(user: dict | None, request: Request | None = None, response: Response | None = None) -> str:
    if user and user.get('id'):
        return f"user:{validate_id(str(user['id']), label='user id')}"
    return f"guest:{ensure_upload_session(request, response)}"


def _upload_meta_path(file_id: str) -> Path:
    return UPLOADS / f'{validate_id(file_id, label="file id")}.json'


def _write_json_atomic(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, default=str, indent=2, sort_keys=True), encoding='utf-8')
    tmp.replace(path)


def _write_upload_meta(file_id: str, meta: dict):
    _write_json_atomic(_upload_meta_path(file_id), meta)


def _read_upload_meta(file_id: str) -> dict:
    p = _upload_meta_path(file_id)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {}


async def save_upload(file, *, owner_id: str = ''):
    original_name = file.filename or 'file'
    validate_ext(original_name)
    fid = random_id('file')
    name = safe_filename(original_name)
    validate_ext(name)
    dest = UPLOADS / f'{fid}_{name}'
    size = 0
    try:
        async with aiofiles.open(dest, 'wb') as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > settings.max_upload_mb * 1024 * 1024:
                    dest.unlink(missing_ok=True)
                    raise ValueError('File exceeds configured size limit')
                await f.write(chunk)
        validate_file_signature(dest, name)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    meta = {
        'file_id': fid,
        'filename': name,
        'original_filename': safe_filename(original_name),
        'file_size': size,
        'path': str(dest),
        'content_type': file.content_type,
        'owner_id': owner_id,
        'uploaded_at': now_iso(),
        'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=settings.job_ttl_minutes)).isoformat(),
    }
    _write_upload_meta(fid, meta)
    # Never return server filesystem paths to the browser.
    return {'file_id': fid, 'filename': name, 'file_size': size, 'content_type': file.content_type, 'expires_at': meta['expires_at']}


def find_upload(file_id: str) -> Path:
    meta = _read_upload_meta(file_id)
    path_text = str(meta.get('path') or '')
    if not path_text:
        matches = [p for p in UPLOADS.glob(f'{validate_id(file_id, label="file id")}_*') if p.is_file()]
        if not matches:
            raise FileNotFoundError('Upload not found or expired')
        path = matches[0]
    else:
        path = Path(path_text)
    try:
        path.relative_to(UPLOADS)
    except ValueError as exc:
        raise ValueError('Invalid upload storage path.') from exc
    if not path.exists() or not path.is_file():
        raise FileNotFoundError('Upload not found or expired')
    return path


def upload_meta(file_id: str) -> dict:
    return _read_upload_meta(file_id)


def original_filename(file_id: str, fallback_path: Path | None = None) -> str:
    meta = _read_upload_meta(file_id)
    name = meta.get('original_filename') or meta.get('filename')
    if name:
        return safe_filename(str(name))
    if fallback_path:
        prefix = f'{file_id}_'
        fname = fallback_path.name
        if fname.startswith(prefix):
            return safe_filename(fname[len(prefix):])
        return safe_filename(fname)
    return 'file'


def output_path(job_id: str, filename: str) -> Path:
    return OUTPUTS / f'{validate_id(job_id, label="job id")}_{safe_filename(filename)}'


def job_path(job_id: str) -> Path:
    return JOBS / f'{validate_id(job_id, label="job id")}.json'


def save_job(job: dict):
    _write_json_atomic(job_path(job['id']), job)


def load_job(job_id: str) -> dict:
    p = job_path(job_id)
    if not p.exists():
        raise FileNotFoundError('Job not found')
    return json.loads(p.read_text(encoding='utf-8'))


def is_admin(user: dict | None) -> bool:
    return bool(user and user.get('role') == 'admin')


def can_access_owner(owner_id: str, user: dict | None, request: Request | None = None) -> bool:
    if not owner_id:
        return True  # legacy compatibility for existing local jobs only
    if is_admin(user):
        return True
    if user and owner_id == f"user:{user.get('id')}":
        return True
    sid = upload_session_from_request(request)
    return bool(sid and owner_id == f'guest:{sid}')


def assert_can_access_upload(file_id: str, user: dict | None, request: Request | None = None) -> dict:
    meta = upload_meta(file_id)
    if not meta:
        raise FileNotFoundError('Upload not found or expired')
    if not can_access_owner(str(meta.get('owner_id') or ''), user, request):
        raise PermissionError('You do not have access to this upload.')
    return meta


def assert_can_access_job(job_id: str, user: dict | None, request: Request | None = None) -> dict:
    job = load_job(job_id)
    if not can_access_owner(str(job.get('owner_id') or ''), user, request):
        raise PermissionError('You do not have access to this job.')
    return job


def make_download_token(path: Path, filename: str | None = None, *, owner_id: str = '', job_id: str = '') -> str:
    return token_for({'path': str(path), 'filename': safe_filename(filename or path.name), 'owner_id': owner_id, 'job_id': job_id})


def _resolve_download_payload(token: str) -> dict:
    payload = verify_token(token, settings.download_token_ttl_minutes * 60)
    if isinstance(payload, dict):
        return payload
    return {'path': str(payload), 'filename': Path(str(payload)).name, 'owner_id': '', 'job_id': ''}


def resolve_download_info(token: str) -> tuple[Path, str]:
    payload = _resolve_download_payload(token)
    path = Path(str(payload.get('path', '')))
    filename = safe_filename(str(payload.get('filename') or path.name))
    if not path.exists() or not path.is_file():
        raise FileNotFoundError('Download expired')
    try:
        path.relative_to(OUTPUTS)
    except ValueError as exc:
        raise ValueError('Invalid download target') from exc
    return path, filename


def resolve_download_for_request(token: str, user: dict | None, request: Request | None = None) -> tuple[Path, str]:
    payload = _resolve_download_payload(token)
    owner_id = str(payload.get('owner_id') or '')
    if not can_access_owner(owner_id, user, request):
        raise PermissionError('You do not have access to this download.')
    path = Path(str(payload.get('path', '')))
    filename = safe_filename(str(payload.get('filename') or path.name))
    if not path.exists() or not path.is_file():
        raise FileNotFoundError('Download expired')
    try:
        path.relative_to(OUTPUTS)
    except ValueError as exc:
        raise ValueError('Invalid download target') from exc
    return path, filename


def resolve_download(token: str) -> Path:
    path, _ = resolve_download_info(token)
    return path


def media_type_for(path: Path, filename: str | None = None) -> str:
    guess, _ = mimetypes.guess_type(filename or path.name)
    return guess or 'application/octet-stream'


def delete_job_files(job_id: str):
    job = None
    try:
        job = load_job(job_id)
    except Exception:
        pass
    if job and job.get('input_path'):
        try:
            input_path = Path(job['input_path'])
            input_path.relative_to(UPLOADS)
            input_path.unlink(missing_ok=True)
        except Exception:
            pass
    for p in OUTPUTS.glob(f'{validate_id(job_id, label="job id")}_*'):
        p.unlink(missing_ok=True)
    job_path(job_id).unlink(missing_ok=True)


def cleanup_expired():
    """Delete old completed/failed job artifacts without interrupting queued/processing jobs."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.job_ttl_minutes)
    active_inputs: set[str] = set()
    old_jobs: list[Path] = []

    for jp in JOBS.glob('*.json'):
        try:
            job = json.loads(jp.read_text(encoding='utf-8'))
            status = str(job.get('status') or '')
            input_path = str(job.get('input_path') or '')
            if status in {'queued', 'processing'}:
                if input_path:
                    active_inputs.add(input_path)
                continue
            if datetime.fromtimestamp(jp.stat().st_mtime, timezone.utc) < cutoff:
                old_jobs.append(jp)
                if input_path:
                    active_inputs.add(input_path)
        except Exception:
            if datetime.fromtimestamp(jp.stat().st_mtime, timezone.utc) < cutoff:
                old_jobs.append(jp)

    for jp in old_jobs:
        try:
            job_id = jp.stem
            delete_job_files(job_id)
        except Exception:
            try:
                jp.unlink(missing_ok=True)
            except Exception:
                pass

    for p in list(UPLOADS.glob('*')) + list(OUTPUTS.glob('*')):
        try:
            if str(p) in active_inputs:
                continue
            if datetime.fromtimestamp(p.stat().st_mtime, timezone.utc) < cutoff:
                p.unlink(missing_ok=True)
        except Exception:
            pass
