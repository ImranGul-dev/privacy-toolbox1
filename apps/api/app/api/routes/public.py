from __future__ import annotations

from fastapi import APIRouter
from app.services.admin_config_service import public_config

router = APIRouter(prefix='/api/public', tags=['public'])

@router.get('/config')
def get_public_config():
    return public_config()
