from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

try:
    import stripe  # type: ignore
except Exception:  # pragma: no cover - allows non-billing test environments without Stripe installed
    stripe = None  # type: ignore

from app.core.config import settings
from app.services import admin_config_service, user_service

PAID_PLANS = {'pro', 'team', 'business'}
INTERVALS = {'monthly', 'yearly'}
ACTIVE_SUBSCRIPTION_STATUSES = {'active', 'trialing', 'past_due'}


def stripe_is_configured() -> bool:
    return bool(settings.stripe_secret_key)


def _stripe() -> None:
    if not settings.stripe_secret_key:
        raise RuntimeError('Stripe is not configured. Add STRIPE_SECRET_KEY before enabling billing.')
    if stripe is None:
        raise RuntimeError('Stripe Python package is not installed. Rebuild the API image after updating requirements.txt.')
    stripe.api_key = settings.stripe_secret_key


def _front_url(path: str) -> str:
    base = settings.frontend_url.rstrip('/') + '/'
    path = path.lstrip('/')
    return urljoin(base, path)


def price_id_for(plan: str, interval: str) -> str:
    plan = (plan or '').lower().strip()
    interval = (interval or 'monthly').lower().strip()
    if plan not in PAID_PLANS:
        raise ValueError('Select a paid plan: pro, team, or business.')
    if interval not in INTERVALS:
        raise ValueError('Billing interval must be monthly or yearly.')
    cfg = admin_config_service.effective_plan(plan)
    from_admin = str(cfg.get(f'stripe_price_id_{interval}') or '')
    return from_admin or settings.stripe_price_id(plan, interval)


def public_status() -> dict[str, Any]:
    ready = stripe_is_configured()
    prices = {f'{plan}_{interval}': bool(price_id_for(plan, interval)) for plan in PAID_PLANS for interval in INTERVALS}
    return {
        'status': 'configured' if ready else 'disabled',
        'stripe_configured': ready,
        'webhook_secret_configured': bool(settings.stripe_webhook_secret),
        'checkout_enabled': bool(ready and any(prices.values())),
        'configured_prices': prices,
    }


def create_checkout_session(user: dict[str, Any], plan: str, interval: str = 'monthly') -> dict[str, Any]:
    _stripe()
    plan = plan.lower().strip()
    interval = interval.lower().strip()
    price_id = price_id_for(plan, interval)
    if not price_id:
        raise RuntimeError(f'Stripe price ID is missing for {plan} {interval}. Add it in .env.production or the admin pricing settings.')

    user_id = str(user.get('id') or '')
    email = str(user.get('email') or '')
    metadata = {'user_id': user_id, 'user_email': email, 'plan': plan, 'interval': interval}

    success_url = _front_url(settings.stripe_success_path)
    success_url = success_url + ('&' if '?' in success_url else '?') + 'session_id={CHECKOUT_SESSION_ID}'

    session = stripe.checkout.Session.create(
        mode='subscription',
        customer_email=email,
        client_reference_id=user_id,
        line_items=[{'price': price_id, 'quantity': 1}],
        success_url=success_url,
        cancel_url=_front_url(settings.stripe_cancel_path),
        allow_promotion_codes=True,
        metadata=metadata,
        subscription_data={'metadata': metadata},
    )
    return {'url': session.url, 'id': session.id}


def create_customer_portal_session(user: dict[str, Any]) -> dict[str, Any]:
    _stripe()
    customer_id = str(user.get('stripe_customer_id') or '')
    if not customer_id:
        raise RuntimeError('No Stripe customer is connected to this account yet.')
    session = stripe.billing_portal.Session.create(customer=customer_id, return_url=_front_url('/dashboard'))
    return {'url': session.url, 'id': session.id}


def _apply_subscription_state(*, user_id: str = '', email: str = '', plan: str = 'free', customer_id: str = '', subscription_id: str = '', status: str = '') -> dict[str, Any] | None:
    plan_to_apply = plan if status in ACTIVE_SUBSCRIPTION_STATUSES and plan in PAID_PLANS else 'free'
    return user_service.set_user_billing_state(
        user_id=user_id,
        email=email,
        plan=plan_to_apply,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        stripe_subscription_status=status,
        plan_grant_reason=f'Stripe subscription status: {status or "unknown"}',
    )


def handle_checkout_completed(session: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(session.get('metadata') or {})
    plan = str(metadata.get('plan') or '').lower()
    user_id = str(metadata.get('user_id') or session.get('client_reference_id') or '')
    email = str(metadata.get('user_email') or (session.get('customer_details') or {}).get('email') or session.get('customer_email') or '')
    customer_id = str(session.get('customer') or '')
    subscription_id = str(session.get('subscription') or '')
    status = 'active' if session.get('payment_status') == 'paid' else 'incomplete'

    if subscription_id:
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            status = str(sub.get('status') or status)
            sub_meta = dict(sub.get('metadata') or {})
            plan = str(sub_meta.get('plan') or plan).lower()
            customer_id = str(sub.get('customer') or customer_id)
        except Exception:
            pass
    updated = _apply_subscription_state(user_id=user_id, email=email, plan=plan, customer_id=customer_id, subscription_id=subscription_id, status=status)
    return {'ok': True, 'handled': 'checkout.session.completed', 'updated_user': updated}


def handle_subscription_event(subscription: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(subscription.get('metadata') or {})
    plan = str(metadata.get('plan') or '').lower()
    user_id = str(metadata.get('user_id') or '')
    email = str(metadata.get('user_email') or '')
    customer_id = str(subscription.get('customer') or '')
    subscription_id = str(subscription.get('id') or '')
    status = str(subscription.get('status') or '')
    if not user_id and not email:
        existing = user_service.find_user_by_stripe(customer_id=customer_id, subscription_id=subscription_id)
        if existing:
            user_id = str(existing.get('id') or '')
            email = str(existing.get('email') or '')
            plan = plan or str(existing.get('stored_plan') or existing.get('plan') or '').lower()
    updated = _apply_subscription_state(user_id=user_id, email=email, plan=plan, customer_id=customer_id, subscription_id=subscription_id, status=status)
    return {'ok': True, 'handled': 'subscription', 'updated_user': updated}


def construct_webhook_event(payload: bytes, signature: str | None) -> dict[str, Any]:
    _stripe()
    if not settings.stripe_webhook_secret:
        raise RuntimeError('STRIPE_WEBHOOK_SECRET is not configured.')
    return stripe.Webhook.construct_event(payload, signature or '', settings.stripe_webhook_secret)
