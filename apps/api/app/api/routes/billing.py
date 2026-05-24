from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from app.api.routes.auth import require_user
from app.services import billing_service

router = APIRouter(prefix='/api/billing', tags=['billing'])


class CheckoutPayload(BaseModel):
    plan: str
    interval: str = 'monthly'


@router.get('/status')
def status():
    return billing_service.public_status()


@router.post('/checkout')
def checkout(payload: CheckoutPayload, user: dict = Depends(require_user)):
    try:
        return billing_service.create_checkout_session(user, payload.plan, payload.interval)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post('/customer-portal')
def customer_portal(user: dict = Depends(require_user)):
    try:
        return billing_service.create_customer_portal_session(user)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post('/webhook')
async def webhook(request: Request, stripe_signature: str | None = Header(default=None, alias='Stripe-Signature')):
    payload = await request.body()
    try:
        event = billing_service.construct_webhook_event(payload, stripe_signature)
        event_type = str(event.get('type') or '')
        obj = event.get('data', {}).get('object', {})
        if event_type == 'checkout.session.completed':
            return billing_service.handle_checkout_completed(obj)
        if event_type in {'customer.subscription.created', 'customer.subscription.updated', 'customer.subscription.deleted'}:
            return billing_service.handle_subscription_event(obj)
        return {'ok': True, 'ignored': event_type}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail='Invalid Stripe webhook payload or signature.')
