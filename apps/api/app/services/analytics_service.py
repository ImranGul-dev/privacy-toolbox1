from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Request
from app.core.config import settings
from app.services import metrics_service

ANALYTICS_DIR = settings.storage_dir / 'analytics'
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_FILE = ANALYTICS_DIR / 'events.jsonl'
MAX_EVENTS_READ = 20000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _country_from_request(request: Request | None) -> str:
    if not request:
        return 'Unknown'
    headers = request.headers
    for key in ['cf-ipcountry', 'x-vercel-ip-country', 'x-appengine-country']:
        value = headers.get(key)
        if value:
            return value.upper()
    return 'Local/Unknown'


def _source_from_payload(payload: dict[str, Any]) -> str:
    explicit = str(payload.get('source') or '').strip()
    if explicit:
        return explicit[:80]
    referrer = str(payload.get('referrer') or '').lower()
    if not referrer:
        return 'direct'
    if 'google.' in referrer:
        return 'google'
    if 'bing.' in referrer:
        return 'bing'
    if 'chatgpt.com' in referrer or 'openai.com' in referrer:
        return 'chatgpt'
    if 'perplexity.ai' in referrer:
        return 'perplexity'
    if 'facebook.' in referrer or 'instagram.' in referrer:
        return 'social'
    if 'youtube.' in referrer:
        return 'youtube'
    return 'referral'


def record_event(payload: dict[str, Any], request: Request | None = None, user: dict | None = None) -> dict[str, Any]:
    event = {
        'ts': _now(),
        'event': str(payload.get('event') or 'event')[:80],
        'path': str(payload.get('path') or '')[:300],
        'tool_slug': str(payload.get('tool_slug') or '')[:120],
        'session_id': str(payload.get('session_id') or '')[:120],
        'source': _source_from_payload(payload),
        'referrer': str(payload.get('referrer') or '')[:500],
        'utm_source': str(payload.get('utm_source') or '')[:120],
        'utm_campaign': str(payload.get('utm_campaign') or '')[:120],
        'country': _country_from_request(request),
        'user_agent': str(request.headers.get('user-agent') if request else '')[:400],
        'duration_seconds': int(float(payload.get('duration_seconds') or 0)),
        'user_id': (user or {}).get('id'),
    }
    with EVENTS_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return {'ok': True}


def _read_events() -> list[dict[str, Any]]:
    if not EVENTS_FILE.exists():
        return []
    lines = EVENTS_FILE.read_text(encoding='utf-8', errors='ignore').splitlines()[-MAX_EVENTS_READ:]
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except Exception:
            continue
    return events


def _parse_ts(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except Exception:
        return None


def _filter_days(events: list[dict[str, Any]], days: int) -> list[dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [e for e in events if (_parse_ts(e.get('ts', '')) or cutoff) >= cutoff]


def _counts(items: list[str]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        key = item or 'unknown'
        counts[key] = counts.get(key, 0) + 1
    return [{'label': k, 'count': v} for k, v in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:20]]


def analytics_summary(tool_definitions: list[dict[str, Any]]) -> dict[str, Any]:
    events = _read_events()
    last_7 = _filter_days(events, 7)
    last_30 = _filter_days(events, 30)
    sessions: dict[str, int] = {}
    for e in last_30:
        sid = e.get('session_id') or ''
        dur = int(e.get('duration_seconds') or 0)
        if sid and dur:
            sessions[sid] = max(sessions.get(sid, 0), min(dur, 60 * 60 * 4))
    avg_session = int(sum(sessions.values()) / max(1, len(sessions))) if sessions else 0

    # Combine real tool jobs from metrics with frontend tool views where available.
    metric_data = metrics_service._read()  # internal durable local metrics store
    jobs_by_tool = metric_data.get('tools', {})
    tool_titles = {d.get('slug'): d.get('title') for d in tool_definitions}
    job_rows = []
    for slug, rec in jobs_by_tool.items():
        job_rows.append({
            'slug': slug,
            'title': tool_titles.get(slug, slug),
            'total_jobs': int(rec.get('total_jobs', 0)),
            'success_jobs': int(rec.get('success_jobs', 0)),
            'failed_jobs': int(rec.get('failed_jobs', 0)),
            'last_used_at': rec.get('last_used_at'),
        })
    job_rows.sort(key=lambda x: x['total_jobs'], reverse=True)

    return {
        'generated_at': _now(),
        'overview': {
            'page_views_7d': len([e for e in last_7 if e.get('event') == 'page_view']),
            'page_views_30d': len([e for e in last_30 if e.get('event') == 'page_view']),
            'unique_sessions_30d': len(set(e.get('session_id') for e in last_30 if e.get('session_id'))),
            'average_session_seconds_30d': avg_session,
        },
        'traffic_sources_30d': _counts([e.get('utm_source') or e.get('source') for e in last_30 if e.get('event') == 'page_view']),
        'locations_30d': _counts([e.get('country') for e in last_30 if e.get('event') == 'page_view']),
        'top_pages_30d': _counts([e.get('path') for e in last_30 if e.get('event') == 'page_view']),
        'top_tool_views_7d': _counts([e.get('tool_slug') for e in last_7 if e.get('event') == 'tool_view' and e.get('tool_slug')]),
        'top_tool_views_30d': _counts([e.get('tool_slug') for e in last_30 if e.get('event') == 'tool_view' and e.get('tool_slug')]),
        'tool_jobs': job_rows[:30],
    }
