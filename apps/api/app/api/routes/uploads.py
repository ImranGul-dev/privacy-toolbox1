from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request, Response
from app.api.routes.auth import current_user
from app.core.rate_limit import allow, client_ip
from app.services.storage_service import save_upload, owner_id_for

router = APIRouter(prefix='/api')

@router.post('/uploads')
async def upload(request: Request, response: Response, file: UploadFile = File(...), user: dict | None = Depends(current_user)):
    if not allow(f"upload:{(user or {}).get('id') or client_ip(request)}", limit=30, window=60):
        raise HTTPException(status_code=429, detail='Too many uploads. Please wait and try again.')
    try:
        owner_id = owner_id_for(user, request, response)
        return await save_upload(file, owner_id=owner_id)
    except Exception as e:
        raise HTTPException(400, str(e))
