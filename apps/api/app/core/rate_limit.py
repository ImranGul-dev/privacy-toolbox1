from __future__ import annotations

import time
from typing import Optional

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - redis may not be installed in unit test env
    redis = None

from app.core.config import settings

_hits: dict[str, list[float]] = {}
_client = None


def _redis():
    global _client
    if _client is not None:
        return _client
    if redis is None:
        return None
    try:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=1, socket_timeout=1)
        _client.ping()
        return _client
    except Exception:
        _client = False
        return None


def allow(key: str, limit: int = 60, window: int = 60) -> bool:
    key = f'rl:{settings.app_env}:{key}'[:240]
    r = _redis()
    if r:
        try:
            count = r.incr(key)
            if count == 1:
                r.expire(key, window)
            return int(count) <= limit
        except Exception:
            pass

    now = time.time()
    bucket = [t for t in _hits.get(key, []) if now - t < window]
    if len(bucket) >= limit:
        _hits[key] = bucket
        return False
    bucket.append(now)
    _hits[key] = bucket
    return True


def client_ip(request) -> str:
    forwarded = request.headers.get('x-forwarded-for', '') if request else ''
    if forwarded:
        return forwarded.split(',')[0].strip()[:80]
    return (request.client.host if request and request.client else 'unknown')[:80]
