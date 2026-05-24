from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix='/api/api-keys', tags=['api-keys'])

@router.get('/status')
def status():
    return {
        'status': 'disabled',
        'message': 'API key product is intentionally disabled until persistent key storage, hashing, scopes, rotation, and abuse limits are implemented.',
    }
