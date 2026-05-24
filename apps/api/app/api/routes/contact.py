from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from app.services import contact_service
from app.core.rate_limit import allow, client_ip

router = APIRouter(prefix='/api/contact', tags=['contact'])

class ContactPayload(BaseModel):
    first_name: str = ''
    last_name: str = ''
    email: EmailStr
    subject: str = Field(min_length=2, max_length=160)
    message: str = Field(min_length=10, max_length=5000)

@router.post('')
def submit_contact(payload: ContactPayload, request: Request):
    if not allow(f'contact:{client_ip(request)}', limit=5, window=3600):
        raise HTTPException(status_code=429, detail='Too many contact submissions. Please try again later.')
    try:
        meta = {'ip': request.headers.get('x-forwarded-for') or (request.client.host if request.client else ''), 'user_agent': request.headers.get('user-agent', '')[:300]}
        return contact_service.create_message(payload.model_dump(), meta)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
