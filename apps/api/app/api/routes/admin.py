from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.api.routes.auth import require_admin
from app.services.metrics_service import admin_summary
from app.services.analytics_service import analytics_summary
from app.services import admin_config_service, user_service, contact_service
from app.tools.registry import list_tools

router = APIRouter(prefix="/api/admin", tags=["admin"])


class SettingsPayload(BaseModel):
    settings: dict


class PromoPayload(BaseModel):
    percent: int = Field(ge=0, le=95)
    days: int = Field(ge=1, le=365)
    headline: str = 'Limited-time privacy toolkit offer'
    message: str = 'Save {percent}% on Pro and Team plans for the next {days} days.'
    coupon_code: str = 'LAUNCH'
    affiliate_url: str = ''


class CouponPayload(BaseModel):
    code: str
    percent: int = Field(ge=0, le=95)
    applies_to: list[str] = ['pro', 'team']
    starts_at: str = ''
    ends_at: str = ''
    max_redemptions: int = 0
    notes: str = ''
    enabled: bool = True


class AffiliatePayload(BaseModel):
    label: str
    url: str
    notes: str = ''
    enabled: bool = True


class AdminUserPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10)
    name: str = ''
    plan: str = 'free'
    role: str = 'user'
    plan_grant_reason: str = 'Manual admin grant'
    plan_expires_at: str = ''
    email_verified: bool = True
    requires_password_change: bool = False


class AdminUserUpdatePayload(BaseModel):
    email: EmailStr
    password: str = ''
    name: str = ''
    plan: str = ''
    role: str = ''
    plan_grant_reason: str = ''
    plan_expires_at: str = ''
    email_verified: bool | None = None
    requires_password_change: bool | None = None


@router.get("/tool-performance")
def tool_performance(user: dict = Depends(require_admin)):
    definitions = [plugin.definition.model_dump() for plugin in list_tools()]
    return admin_summary(definitions)


@router.get('/overview')
def admin_overview(user: dict = Depends(require_admin)):
    definitions = [plugin.definition.model_dump() for plugin in list_tools()]
    return {
        'settings': admin_config_service.read_settings(),
        'public_config': admin_config_service.public_config(),
        'tools': admin_summary(definitions),
        'analytics': analytics_summary(definitions),
        'users': user_service.list_users(),
        'contact_messages': contact_service.list_messages(),
    }


@router.get('/settings')
def get_settings(user: dict = Depends(require_admin)):
    return admin_config_service.read_settings()


@router.put('/settings')
def put_settings(payload: SettingsPayload, user: dict = Depends(require_admin)):
    return admin_config_service.update_settings(payload.settings)


@router.post('/promo')
def set_promo(payload: PromoPayload, user: dict = Depends(require_admin)):
    return admin_config_service.set_promo_percent_days(
        percent=payload.percent,
        days=payload.days,
        headline=payload.headline,
        message=payload.message,
        coupon_code=payload.coupon_code,
        affiliate_url=payload.affiliate_url,
    )


@router.post('/coupons')
def create_coupon(payload: CouponPayload, user: dict = Depends(require_admin)):
    try:
        return admin_config_service.add_coupon(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete('/coupons/{coupon_id}')
def delete_coupon(coupon_id: str, user: dict = Depends(require_admin)):
    admin_config_service.remove_coupon(coupon_id)
    return {'ok': True}


@router.post('/affiliates')
def create_affiliate(payload: AffiliatePayload, user: dict = Depends(require_admin)):
    try:
        return admin_config_service.add_affiliate(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete('/affiliates/{link_id}')
def delete_affiliate(link_id: str, user: dict = Depends(require_admin)):
    admin_config_service.remove_affiliate(link_id)
    return {'ok': True}


@router.get('/users')
def get_users(user: dict = Depends(require_admin)):
    return {'users': user_service.list_users()}


@router.post('/users')
def create_user(payload: AdminUserPayload, user: dict = Depends(require_admin)):
    try:
        return user_service.create_user_by_admin(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put('/users')
def update_user(payload: AdminUserUpdatePayload, user: dict = Depends(require_admin)):
    data = payload.model_dump()
    email = data.pop('email')
    patch = {k: v for k, v in data.items() if v not in ('', None, [])}
    try:
        return user_service.update_user_by_admin(str(email), patch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get('/analytics')
def analytics(user: dict = Depends(require_admin)):
    definitions = [plugin.definition.model_dump() for plugin in list_tools()]
    return analytics_summary(definitions)


@router.get('/contact-messages')
def contact_messages(user: dict = Depends(require_admin)):
    return {'messages': contact_service.list_messages()}

@router.post('/contact-messages/{message_id}/read')
def mark_contact_message_read(message_id: str, user: dict = Depends(require_admin)):
    try:
        return contact_service.mark_message(message_id, 'read')
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post('/contact-messages/{message_id}/unread')
def mark_contact_message_unread(message_id: str, user: dict = Depends(require_admin)):
    try:
        return contact_service.mark_message(message_id, 'new')
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
