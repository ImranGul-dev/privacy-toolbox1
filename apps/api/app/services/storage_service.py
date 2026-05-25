from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta, timezone
import json
import mimetypes
import os
from typing import Any

import aiofiles
from fastapi import Request, Response

from app.core.config import settings
from app.core.security import (
    random_id,
    safe_filename,
    validate_ext,
    validate_file_signature,
    validate_id,
    token_for,
    verify_token,
)

BASE = settings.storage_dir
UPLOADS = BASE / "uploads"
OUTPUTS = BASE / "outputs"
JOBS = BASE / "jobs"

for p in (UPLOADS, OUTPUTS, JOBS):
    p.mkdir(parents=True, exist_ok=True)


# PostgreSQL processing_jobs fields that exist in your current DB model/table.
PG_JOB_FIELDS = [
    "id",
    "status",
    "tool_type",
    "input_filename",
    "output_filename",
    "file_type",
    "file_size",
    "progress",
    "current_step",
    "report",
    "download_token",
    "expires_at",
    "created_at",
    "updated_at",
    "error_message",
]


def _database_url() -> str:
    return str(getattr(settings, "database_url", "") or os.getenv("DATABASE_URL", "") or "")


def _use_postgres_jobs() -> bool:
    return bool(_database_url()) and str(getattr(settings, "user_storage_backend", "")).lower() == "postgres"


def _require_postgres_jobs() -> bool:
    return str(getattr(settings, "user_storage_backend", "")).lower() == "postgres"


def _pg_connect():
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(_database_url(), row_factory=dict_row)


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value, default=str)
        return value
    except Exception:
        return str(value)


def _clean_report(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return _json_safe(value)
    if value in (None, ""):
        return {}
    return {"value": str(value)}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(value)
    except Exception:
        return default


def _job_value(job: dict, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in job and job.get(key) is not None:
            return job.get(key)
    return default


def _job_pg_values(job: dict) -> dict:
    now = now_iso()

    job_id = validate_id(str(job.get("id") or ""), label="job id")

    created_at = _job_value(job, "created_at", default=now)
    updated_at = now
    expires_at = _job_value(
        job,
        "expires_at",
        default=(datetime.now(timezone.utc) + timedelta(minutes=settings.job_ttl_minutes)).isoformat(),
    )

    input_filename = _job_value(
        job,
        "input_filename",
        "original_filename",
        "filename",
        default="",
    )

    output_filename = _job_value(
        job,
        "output_filename",
        "download_filename",
        default="",
    )

    tool_type = _job_value(
        job,
        "tool_type",
        "tool_slug",
        "tool",
        "plugin",
        "action",
        default="unknown",
    )

    file_type = _job_value(
        job,
        "file_type",
        "content_type",
        default="",
    )

    return {
        "id": job_id,
        "status": str(_job_value(job, "status", default="queued") or "queued"),
        "tool_type": str(tool_type or "unknown"),
        "input_filename": safe_filename(str(input_filename or "")) if input_filename else "",
        "output_filename": safe_filename(str(output_filename or "")) if output_filename else "",
        "file_type": str(file_type or ""),
        "file_size": _safe_int(_job_value(job, "file_size", "size", default=0)),
        "progress": _safe_int(_job_value(job, "progress", default=0)),
        "current_step": str(_job_value(job, "current_step", "step", default="queued") or "queued"),
        "report": _clean_report(_job_value(job, "report", default={})),
        "download_token": str(_job_value(job, "download_token", default="") or ""),
        "expires_at": expires_at,
        "created_at": created_at,
        "updated_at": updated_at,
        "error_message": str(_job_value(job, "error_message", "error", default="") or ""),
    }


def _save_job_postgres(job: dict) -> None:
    from psycopg.types.json import Jsonb

    values = _job_pg_values(job)

    sql = """
    INSERT INTO public.processing_jobs (
        id,
        status,
        tool_type,
        input_filename,
        output_filename,
        file_type,
        file_size,
        progress,
        current_step,
        report,
        download_token,
        expires_at,
        created_at,
        updated_at,
        error_message
    )
    VALUES (
        %(id)s,
        %(status)s,
        %(tool_type)s,
        %(input_filename)s,
        %(output_filename)s,
        %(file_type)s,
        %(file_size)s,
        %(progress)s,
        %(current_step)s,
        %(report)s,
        %(download_token)s,
        %(expires_at)s,
        %(created_at)s,
        %(updated_at)s,
        %(error_message)s
    )
    ON CONFLICT (id) DO UPDATE SET
        status = EXCLUDED.status,
        tool_type = COALESCE(NULLIF(EXCLUDED.tool_type, ''), processing_jobs.tool_type),
        input_filename = COALESCE(NULLIF(EXCLUDED.input_filename, ''), processing_jobs.input_filename),
        output_filename = COALESCE(NULLIF(EXCLUDED.output_filename, ''), processing_jobs.output_filename),
        file_type = COALESCE(NULLIF(EXCLUDED.file_type, ''), processing_jobs.file_type),
        file_size = CASE
            WHEN EXCLUDED.file_size > 0 THEN EXCLUDED.file_size
            ELSE processing_jobs.file_size
        END,
        progress = EXCLUDED.progress,
        current_step = EXCLUDED.current_step,
        report = EXCLUDED.report,
        download_token = COALESCE(NULLIF(EXCLUDED.download_token, ''), processing_jobs.download_token),
        expires_at = COALESCE(EXCLUDED.expires_at, processing_jobs.expires_at),
        updated_at = EXCLUDED.updated_at,
        error_message = EXCLUDED.error_message
    """

    values["report"] = Jsonb(values["report"])

    with _pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, values)
        conn.commit()


def _load_job_postgres(job_id: str) -> dict:
    safe_id = validate_id(job_id, label="job id")

    sql = """
    SELECT
        id,
        status,
        tool_type,
        input_filename,
        output_filename,
        file_type,
        file_size,
        progress,
        current_step,
        report,
        download_token,
        expires_at,
        created_at,
        updated_at,
        error_message
    FROM public.processing_jobs
    WHERE id = %s
    LIMIT 1
    """

    with _pg_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (safe_id,))
            row = cur.fetchone()

    if not row:
        return {}

    data = dict(row)
    for key in ("created_at", "updated_at", "expires_at"):
        if data.get(key) is not None and hasattr(data[key], "isoformat"):
            data[key] = data[key].isoformat()
    if data.get("report") is None:
        data["report"] = {}

    return data


def _use_s3() -> bool:
    return settings.storage_backend.lower() == "s3"


def _s3_client():
    import boto3  # imported lazily so local MVP deployments do not need AWS credentials

    return boto3.client("s3", region_name=settings.aws_region)


def _put_json_s3(key: str, data: dict) -> None:
    _s3_client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=json.dumps(data, default=str, indent=2, sort_keys=True).encode("utf-8"),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )


def _get_json_s3(key: str) -> dict:
    try:
        obj = _s3_client().get_object(Bucket=settings.s3_bucket, Key=key)
        return json.loads(obj["Body"].read().decode("utf-8"))
    except Exception:
        return {}


def _delete_s3_key(key: str) -> None:
    if key:
        try:
            _s3_client().delete_object(Bucket=settings.s3_bucket, Key=key)
        except Exception:
            pass


def _upload_key(file_id: str, name: str) -> str:
    return f"{settings.s3_upload_prefix.rstrip('/')}/{validate_id(file_id, label='file id')}_{safe_filename(name)}"


def _upload_meta_key(file_id: str) -> str:
    return f"{settings.s3_upload_prefix.rstrip('/')}/{validate_id(file_id, label='file id')}.json"


def _job_key(job_id: str) -> str:
    return f"jobs/{validate_id(job_id, label='job id')}.json"


def _output_key(job_id: str, filename: str) -> str:
    return f"{settings.s3_output_prefix.rstrip('/')}/{validate_id(job_id, label='job id')}_{safe_filename(filename)}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def upload_session_from_request(request: Request | None) -> str:
    if request is None:
        return ""
    value = request.cookies.get(settings.upload_session_cookie_name, "")
    try:
        return validate_id(value, label="upload session")
    except ValueError:
        return ""


def ensure_upload_session(request: Request | None, response: Response | None = None) -> str:
    sid = upload_session_from_request(request)
    if not sid:
        sid = random_id("anon")
        if response is not None:
            response.set_cookie(
                settings.upload_session_cookie_name,
                sid,
                httponly=True,
                secure=settings.auth_cookie_secure,
                samesite="lax",
                max_age=60 * 60 * 24,
                path="/",
            )
    return sid


def owner_id_for(user: dict | None, request: Request | None = None, response: Response | None = None) -> str:
    if user and user.get("id"):
        return f"user:{validate_id(str(user['id']), label='user id')}"
    return f"guest:{ensure_upload_session(request, response)}"


def _upload_meta_path(file_id: str) -> Path:
    return UPLOADS / f'{validate_id(file_id, label="file id")}.json'


def _write_json_atomic(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, default=str, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _write_upload_meta(file_id: str, meta: dict):
    if _use_s3():
        _put_json_s3(_upload_meta_key(file_id), meta)
        return
    _write_json_atomic(_upload_meta_path(file_id), meta)


def _read_upload_meta(file_id: str) -> dict:
    if _use_s3():
        return _get_json_s3(_upload_meta_key(file_id))
    p = _upload_meta_path(file_id)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


async def save_upload(file, *, owner_id: str = ""):
    original_name = file.filename or "file"
    validate_ext(original_name)
    fid = random_id("file")
    name = safe_filename(original_name)
    validate_ext(name)
    dest = UPLOADS / f"{fid}_{name}"
    size = 0

    try:
        async with aiofiles.open(dest, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > settings.max_upload_mb * 1024 * 1024:
                    dest.unlink(missing_ok=True)
                    raise ValueError("File exceeds configured size limit")
                await f.write(chunk)

        validate_file_signature(dest, name)

        s3_key = ""
        if _use_s3():
            s3_key = _upload_key(fid, name)
            _s3_client().upload_file(
                str(dest),
                settings.s3_bucket,
                s3_key,
                ExtraArgs={
                    "ServerSideEncryption": "AES256",
                    "ContentType": file.content_type or media_type_for(dest, name),
                    "Metadata": {"owner-id": owner_id[:128], "file-id": fid},
                },
            )
    except Exception:
        dest.unlink(missing_ok=True)
        raise

    meta = {
        "file_id": fid,
        "filename": name,
        "original_filename": safe_filename(original_name),
        "file_size": size,
        "path": str(dest),
        "s3_key": s3_key if _use_s3() else "",
        "storage_backend": settings.storage_backend.lower(),
        "content_type": file.content_type,
        "owner_id": owner_id,
        "uploaded_at": now_iso(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=settings.job_ttl_minutes)).isoformat(),
    }

    _write_upload_meta(fid, meta)

    # Never return server filesystem paths or S3 object keys to the browser.
    return {
        "file_id": fid,
        "filename": name,
        "file_size": size,
        "content_type": file.content_type,
        "expires_at": meta["expires_at"],
    }


def _download_s3_to_cache(s3_key: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        _s3_client().download_file(settings.s3_bucket, s3_key, str(dest))
    return dest


def find_upload(file_id: str) -> Path:
    meta = _read_upload_meta(file_id)
    if _use_s3() and meta.get("s3_key"):
        filename = safe_filename(str(meta.get("filename") or "upload.bin"))
        return _download_s3_to_cache(
            str(meta["s3_key"]),
            UPLOADS / f'{validate_id(file_id, label="file id")}_{filename}',
        )

    path_text = str(meta.get("path") or "")
    if not path_text:
        matches = [p for p in UPLOADS.glob(f'{validate_id(file_id, label="file id")}_*') if p.is_file()]
        if not matches:
            raise FileNotFoundError("Upload not found or expired")
        path = matches[0]
    else:
        path = Path(path_text)

    try:
        path.relative_to(UPLOADS)
    except ValueError as exc:
        raise ValueError("Invalid upload storage path.") from exc

    if not path.exists() or not path.is_file():
        raise FileNotFoundError("Upload not found or expired")

    return path


def upload_meta(file_id: str) -> dict:
    return _read_upload_meta(file_id)


def original_filename(file_id: str, fallback_path: Path | None = None) -> str:
    meta = _read_upload_meta(file_id)
    name = meta.get("original_filename") or meta.get("filename")
    if name:
        return safe_filename(str(name))
    if fallback_path:
        prefix = f"{file_id}_"
        fname = fallback_path.name
        if fname.startswith(prefix):
            return safe_filename(fname[len(prefix):])
        return safe_filename(fname)
    return "file"


def output_path(job_id: str, filename: str) -> Path:
    return OUTPUTS / f'{validate_id(job_id, label="job id")}_{safe_filename(filename)}'


def job_path(job_id: str) -> Path:
    return JOBS / f'{validate_id(job_id, label="job id")}.json'


def save_job(job: dict):
    """
    Durable job save.

    In AWS production mode:
    - PostgreSQL public.processing_jobs becomes the durable job index.
    - S3 JSON job files are still written as compatibility/fallback metadata.
    """
    if not job.get("id"):
        raise ValueError("Job id is required")

    pg_error: Exception | None = None

    if _use_postgres_jobs():
        try:
            _save_job_postgres(job)
        except Exception as exc:
            pg_error = exc

    if _use_s3():
        _put_json_s3(_job_key(job["id"]), job)
    else:
        _write_json_atomic(job_path(job["id"]), job)

    if pg_error and _require_postgres_jobs():
        raise RuntimeError(f"Failed to save job to PostgreSQL: {type(pg_error).__name__}") from pg_error


def load_job(job_id: str) -> dict:
    """
    Load PostgreSQL job first, then merge S3/local JSON metadata when available.

    PostgreSQL stores stable job tracking fields.
    S3/local JSON keeps compatibility fields such as owner_id, file_id, input_path, output_s3_key.
    """
    pg_job: dict = {}
    json_job: dict = {}

    if _use_postgres_jobs():
        try:
            pg_job = _load_job_postgres(job_id)
        except Exception:
            pg_job = {}

    if _use_s3():
        json_job = _get_json_s3(_job_key(job_id))
    else:
        p = job_path(job_id)
        if p.exists():
            try:
                json_job = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                json_job = {}

    if pg_job or json_job:
        merged = {}
        merged.update(json_job)
        merged.update(pg_job)
        return merged

    raise FileNotFoundError("Job not found")


def update(job: dict, **changes) -> dict:
    """
    Convenience helper used by workers/routes.

    Updates an in-memory job dict and persists it through save_job().
    """
    if not isinstance(job, dict):
        raise ValueError("job must be a dictionary")

    job.update(changes)
    job["updated_at"] = now_iso()
    save_job(job)
    return job


def is_admin(user: dict | None) -> bool:
    return bool(user and user.get("role") == "admin")


def can_access_owner(owner_id: str, user: dict | None, request: Request | None = None) -> bool:
    if not owner_id:
        return True  # legacy compatibility for existing local jobs only
    if is_admin(user):
        return True
    if user and owner_id == f"user:{user.get('id')}":
        return True
    sid = upload_session_from_request(request)
    return bool(sid and owner_id == f"guest:{sid}")


def assert_can_access_upload(file_id: str, user: dict | None, request: Request | None = None) -> dict:
    meta = upload_meta(file_id)
    if not meta:
        raise FileNotFoundError("Upload not found or expired")
    if not can_access_owner(str(meta.get("owner_id") or ""), user, request):
        raise PermissionError("You do not have access to this upload.")
    return meta


def assert_can_access_job(job_id: str, user: dict | None, request: Request | None = None) -> dict:
    job = load_job(job_id)
    if not can_access_owner(str(job.get("owner_id") or ""), user, request):
        raise PermissionError("You do not have access to this job.")
    return job


def make_download_token(
    path: Path,
    filename: str | None = None,
    *,
    owner_id: str = "",
    job_id: str = "",
    s3_key: str = "",
) -> str:
    payload = {"filename": safe_filename(filename or path.name), "owner_id": owner_id, "job_id": job_id}
    if s3_key:
        payload["s3_key"] = s3_key
    else:
        payload["path"] = str(path)
    return token_for(payload)


def persist_output(job_id: str, path: Path, filename: str, *, owner_id: str = "") -> tuple[str, str]:
    """Persist a cleaned output and return (download_token, s3_key)."""
    if _use_s3():
        key = _output_key(job_id, filename)
        _s3_client().upload_file(
            str(path),
            settings.s3_bucket,
            key,
            ExtraArgs={
                "ServerSideEncryption": "AES256",
                "ContentType": media_type_for(path, filename),
                "Metadata": {"owner-id": owner_id[:128], "job-id": job_id},
            },
        )
        token = make_download_token(path, filename=filename, owner_id=owner_id, job_id=job_id, s3_key=key)

        try:
            job = load_job(job_id)
            job["output_filename"] = safe_filename(filename)
            job["download_filename"] = safe_filename(filename)
            job["download_token"] = token
            job["output_s3_key"] = key
            job["updated_at"] = now_iso()
            save_job(job)
        except Exception:
            pass

        return token, key

    token = make_download_token(path, filename=filename, owner_id=owner_id, job_id=job_id)

    try:
        job = load_job(job_id)
        job["output_filename"] = safe_filename(filename)
        job["download_filename"] = safe_filename(filename)
        job["download_token"] = token
        job["updated_at"] = now_iso()
        save_job(job)
    except Exception:
        pass

    return token, ""


def _resolve_download_payload(token: str) -> dict:
    payload = verify_token(token, settings.download_token_ttl_minutes * 60)
    if isinstance(payload, dict):
        return payload
    return {"path": str(payload), "filename": Path(str(payload)).name, "owner_id": "", "job_id": ""}


def _resolve_local_download_from_payload(payload: dict) -> tuple[Path, str]:
    filename = safe_filename(str(payload.get("filename") or "download.bin"))
    if payload.get("s3_key"):
        cache_name = safe_filename(Path(str(payload["s3_key"])).name)
        return _download_s3_to_cache(str(payload["s3_key"]), OUTPUTS / cache_name), filename

    path = Path(str(payload.get("path", "")))
    if not path.exists() or not path.is_file():
        raise FileNotFoundError("Download expired")

    try:
        path.relative_to(OUTPUTS)
    except ValueError as exc:
        raise ValueError("Invalid download target") from exc

    return path, filename


def resolve_download_info(token: str) -> tuple[Path, str]:
    return _resolve_local_download_from_payload(_resolve_download_payload(token))


def resolve_download_for_request(token: str, user: dict | None, request: Request | None = None) -> tuple[Path, str]:
    payload = _resolve_download_payload(token)
    owner_id = str(payload.get("owner_id") or "")
    if not can_access_owner(owner_id, user, request):
        raise PermissionError("You do not have access to this download.")
    return _resolve_local_download_from_payload(payload)


def resolve_download(token: str) -> Path:
    path, _ = resolve_download_info(token)
    return path


def media_type_for(path: Path, filename: str | None = None) -> str:
    guess, _ = mimetypes.guess_type(filename or path.name)
    return guess or "application/octet-stream"


def delete_job_files(job_id: str):
    job = None
    try:
        job = load_job(job_id)
    except Exception:
        pass

    if _use_s3():
        if job and job.get("output_s3_key"):
            _delete_s3_key(str(job.get("output_s3_key")))

        if job and job.get("file_id"):
            meta = upload_meta(str(job.get("file_id")))
            if meta.get("s3_key"):
                _delete_s3_key(str(meta.get("s3_key")))
            _delete_s3_key(_upload_meta_key(str(job.get("file_id"))))

        _delete_s3_key(_job_key(job_id))
    else:
        if job and job.get("input_path"):
            try:
                input_path = Path(job["input_path"])
                input_path.relative_to(UPLOADS)
                input_path.unlink(missing_ok=True)
            except Exception:
                pass

        for p in OUTPUTS.glob(f'{validate_id(job_id, label="job id")}_*'):
            p.unlink(missing_ok=True)

        job_path(job_id).unlink(missing_ok=True)


def cleanup_expired():
    """Delete old completed/failed job artifacts without interrupting queued/processing jobs."""
    if _use_s3():
        # S3 lifecycle rules are the source of truth in autoscaling mode. Local caches
        # created for processing/downloads can still be cleaned from the task filesystem.
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.job_ttl_minutes)
        for p in list(UPLOADS.glob("*")) + list(OUTPUTS.glob("*")):
            try:
                if datetime.fromtimestamp(p.stat().st_mtime, timezone.utc) < cutoff:
                    p.unlink(missing_ok=True)
            except Exception:
                pass
        return

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.job_ttl_minutes)
    active_inputs: set[str] = set()
    old_jobs: list[Path] = []

    for jp in JOBS.glob("*.json"):
        try:
            job = json.loads(jp.read_text(encoding="utf-8"))
            status = str(job.get("status") or "")
            input_path = str(job.get("input_path") or "")
            if status in {"queued", "processing"}:
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

    for p in list(UPLOADS.glob("*")) + list(OUTPUTS.glob("*")):
        try:
            if str(p) in active_inputs:
                continue
            if datetime.fromtimestamp(p.stat().st_mtime, timezone.utc) < cutoff:
                p.unlink(missing_ok=True)
        except Exception:
            pass