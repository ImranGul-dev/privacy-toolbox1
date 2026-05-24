from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.api.routes.auth import current_user
from app.services.analytics_service import record_event
from app.core.rate_limit import allow, client_ip

router = APIRouter(prefix='/api/analytics', tags=['analytics'])

class AnalyticsEvent(BaseModel):
    event: str
    path: str = ''
    tool_slug: str = ''
    session_id: str = ''
    source: str = ''
    referrer: str = ''
    utm_source: str = ''
    utm_campaign: str = ''
    duration_seconds: int = 0

@router.post('/event')
def event(payload: AnalyticsEvent, request: Request, user: dict | None = Depends(current_user)):
    actor = (user or {}).get('id') or client_ip(request)
    if not allow(f'analytics:{actor}', limit=120, window=60):
        return {'ok': False, 'rate_limited': True}
    return record_event(payload.model_dump(), request, user)
