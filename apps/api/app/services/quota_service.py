from __future__ import annotations

import json
import fcntl
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.plans import ACTION_COST, get_plan

USAGE_DIR = settings.storage_dir / 'usage'
USAGE_DIR.mkdir(parents=True, exist_ok=True)
USAGE_FILE = USAGE_DIR / 'usage.json'


def _load() -> dict[str, Any]:
    if not USAGE_FILE.exists():
        return {}
    try:
        return json.loads(USAGE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _save(data: dict[str, Any]) -> None:
    tmp = USAGE_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
    tmp.replace(USAGE_FILE)


def _with_lock(fn):
    USAGE_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = USAGE_DIR / 'usage.lock'
    with lock_path.open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            return fn()
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def actor_id(user: dict | None, actor_override: str | None = None) -> str:
    if actor_override:
        return actor_override
    return f"user:{user.get('id')}" if user else 'guest:anonymous'


def check_and_consume(user: dict | None, plan_name: str, action: str, actor_override: str | None = None) -> dict[str, Any]:
    def _consume():
        plan = get_plan(plan_name)
        now = datetime.now(timezone.utc)
        today = now.strftime('%Y-%m-%d')
        month = now.strftime('%Y-%m')
        actor = actor_id(user, actor_override)
        kind = ACTION_COST.get(action, 'scan')
        data = _load()
        bucket = data.setdefault(actor, {'days': {}, 'months': {}})
        day = bucket['days'].setdefault(today, {'scan': 0, 'clean': 0})
        mon = bucket['months'].setdefault(month, {'files': 0})

        day_limit = plan.daily_cleans if kind == 'clean' else plan.daily_scans
        if day.get(kind, 0) >= day_limit:
            raise ValueError(f'{plan.label} plan daily {kind} limit reached. Upgrade or try again tomorrow.')
        if mon.get('files', 0) >= plan.monthly_files:
            raise ValueError(f'{plan.label} plan monthly file limit reached. Upgrade for more files this month.')

        day[kind] = day.get(kind, 0) + 1
        mon['files'] = mon.get('files', 0) + 1
        bucket['last_used_at'] = now.isoformat()
        data[actor] = bucket
        _save(data)
        return {'actor': actor, 'day': day, 'month': mon, 'plan': plan.name}
    return _with_lock(_consume)


def refund(actor: str, action: str, plan_name: str | None = None) -> None:
    """Best-effort rollback when a queued job fails before producing a result."""
    if not actor:
        return
    def _refund():
        now = datetime.now(timezone.utc)
        today = now.strftime('%Y-%m-%d')
        month = now.strftime('%Y-%m')
        kind = ACTION_COST.get(action, 'scan')
        data = _load()
        bucket = data.get(actor)
        if not bucket:
            return
        day = bucket.get('days', {}).get(today, {})
        mon = bucket.get('months', {}).get(month, {})
        if day.get(kind, 0) > 0:
            day[kind] -= 1
        if mon.get('files', 0) > 0:
            mon['files'] -= 1
        bucket['last_refund_at'] = now.isoformat()
        data[actor] = bucket
        _save(data)
    _with_lock(_refund)
