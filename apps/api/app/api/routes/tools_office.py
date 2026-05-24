from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix='/api/jobs', tags=['legacy-disabled'])

@router.api_route('/{path:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def legacy_jobs_disabled(path: str):
    raise HTTPException(
        status_code=410,
        detail='Legacy job routes are disabled. Use /api/tools/{tool_id}/{action}, which enforces auth, ownership, plan limits, and quotas.',
    )
