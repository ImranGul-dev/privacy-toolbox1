from datetime import datetime, timedelta, timezone
from pathlib import Path
from app.core.config import settings
from app.core.security import random_id, safe_filename
from app.services import storage_service as st
from app.services import metrics_service


def make_job(tool_type: str, file_path: str, job_id: str | None = None, original_filename: str | None = None):
    now = datetime.now(timezone.utc)
    p = Path(file_path)
    jid = job_id or random_id('job')
    display_name = safe_filename(original_filename or p.name)
    job = {
        'id': jid,
        'status': 'queued',
        'tool_type': tool_type,
        'input_filename': display_name,
        'input_path': str(p),
        'output_filename': None,
        'download_filename': None,
        'file_type': Path(display_name).suffix.lower() or p.suffix.lower(),
        'file_size': p.stat().st_size,
        'progress': 5,
        'current_step': 'queued',
        'report': {},
        'download_token': None,
        'expires_at': (now + timedelta(minutes=settings.job_ttl_minutes)).isoformat(),
        'created_at': now.isoformat(),
        'updated_at': now.isoformat(),
        'error_message': None,
    }
    st.save_job(job)
    metrics_service.record_job_created(job)
    return job


def load(job_id: str):
    return st.load_job(job_id)


def update(job, **kw):
    job.update(kw)
    job['updated_at'] = datetime.now(timezone.utc).isoformat()
    st.save_job(job)
    return job


def cleaned_display_name(job: dict, suffix: str | None = None) -> str:
    source_name = safe_filename(job.get('input_filename') or 'file')
    source = Path(source_name)
    ext = suffix or source.suffix or job.get('file_type') or ''
    stem = source.stem or 'file'
    reserve = len('-cleaned') + len(ext)
    max_stem = max(20, 140 - reserve)
    stem = stem[:max_stem].rstrip('.-_') or 'file'
    return safe_filename(f'{stem}-cleaned{ext}')


def output_for(job, suffix=None):
    return st.output_path(job['id'], cleaned_display_name(job, suffix))
