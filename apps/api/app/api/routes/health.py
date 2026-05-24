from __future__ import annotations

import shutil
import time
from pathlib import Path

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get('/health')
def health():
    return {'ok': True, 'service': 'privacy-toolbox-api'}


@router.get('/ready')
def ready():
    checks: dict[str, object] = {'storage': False, 'redis': False, 'disk_free_mb': 0}
    ok = True

    try:
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        probe = settings.storage_dir / f'.health-{int(time.time())}'
        probe.write_text('ok', encoding='utf-8')
        probe.unlink(missing_ok=True)
        checks['storage'] = True
        usage = shutil.disk_usage(settings.storage_dir)
        checks['disk_free_mb'] = int(usage.free / 1024 / 1024)
        if usage.free < 1024 * 1024 * 1024:
            ok = False
            checks['storage_warning'] = 'Less than 1GB free disk space.'
    except Exception as exc:
        ok = False
        checks['storage_error'] = str(exc)

    try:
        import redis
        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        checks['redis'] = bool(client.ping())
    except Exception as exc:
        ok = False
        checks['redis_error'] = str(exc)

    return {'ok': ok, 'service': 'privacy-toolbox-api', 'checks': checks}
