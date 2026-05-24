from __future__ import annotations

import json
import secrets
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings

CONFIG_DIR = settings.storage_dir / 'admin'
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / 'site_settings.json'


def NOW() -> datetime:
    return datetime.now(timezone.utc)

DEFAULT_SETTINGS: dict[str, Any] = {
    'plans': {
        'free': {
            'name': 'free', 'label': 'Free', 'price_monthly': 0, 'price_yearly': 0, 'currency': 'USD',
            'cta': 'Start free', 'stripe_price_id_monthly': '', 'stripe_price_id_yearly': '',
            'daily_scans': 5, 'daily_cleans': 3, 'monthly_files': 60, 'batch_files': 1,
            'history_days': 0, 'audit_reports': False, 'advanced_pdf': False, 'api_access': False,
            'file_mb': {'image': 25, 'pdf': 50, 'office': 50, 'zip': 50, 'audio': 50, 'video': 100, 'other': 25},
        },
        'pro': {
            'name': 'pro', 'label': 'Pro', 'price_monthly': 9, 'price_yearly': 84, 'currency': 'USD',
            'cta': 'Upgrade to Pro', 'stripe_price_id_monthly': '', 'stripe_price_id_yearly': '',
            'daily_scans': 100, 'daily_cleans': 100, 'monthly_files': 100, 'batch_files': 10,
            'history_days': 7, 'audit_reports': True, 'advanced_pdf': True, 'api_access': False,
            'file_mb': {'image': 100, 'pdf': 200, 'office': 200, 'zip': 250, 'audio': 250, 'video': 512, 'other': 100},
        },
        'team': {
            'name': 'team', 'label': 'Team', 'price_monthly': 19, 'price_yearly': 180, 'currency': 'USD',
            'cta': 'Create team workspace', 'stripe_price_id_monthly': '', 'stripe_price_id_yearly': '',
            'daily_scans': 500, 'daily_cleans': 500, 'monthly_files': 500, 'batch_files': 50,
            'history_days': 30, 'audit_reports': True, 'advanced_pdf': True, 'api_access': False,
            'file_mb': {'image': 200, 'pdf': 500, 'office': 500, 'zip': 512, 'audio': 512, 'video': 512, 'other': 200},
        },
        'business': {
            'name': 'business', 'label': 'Business/API', 'price_monthly': 49, 'price_yearly': 468, 'currency': 'USD',
            'cta': 'Discuss API access', 'stripe_price_id_monthly': '', 'stripe_price_id_yearly': '',
            'daily_scans': 2500, 'daily_cleans': 2500, 'monthly_files': 2000, 'batch_files': 100,
            'history_days': 90, 'audit_reports': True, 'advanced_pdf': True, 'api_access': True,
            'file_mb': {'image': 300, 'pdf': 512, 'office': 512, 'zip': 512, 'audio': 512, 'video': 512, 'other': 300},
        },
    },
    'promo': {
        'enabled': False,
        'headline': 'Launch offer',
        'message': 'Save {percent}% on Pro and Team plans for the next {days} days.',
        'percent': 25,
        'coupon_code': 'LAUNCH25',
        'starts_at': '',
        'ends_at': '',
        'affiliate_url': '',
    },
    'coupons': [],
    'affiliate_links': [],
    'billing': {
        'stripe_ready': False,
        'checkout_enabled': False,
        'customer_portal_enabled': False,
        'webhook_secret_configured': False,
    },
}


def _merge(default: Any, current: Any) -> Any:
    if isinstance(default, dict) and isinstance(current, dict):
        merged = deepcopy(default)
        for key, value in current.items():
            merged[key] = _merge(merged.get(key), value) if key in merged else value
        return merged
    return deepcopy(current) if current is not None else deepcopy(default)


def _read_raw() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return deepcopy(DEFAULT_SETTINGS)
    try:
        return _merge(DEFAULT_SETTINGS, json.loads(CONFIG_FILE.read_text(encoding='utf-8')))
    except Exception:
        return deepcopy(DEFAULT_SETTINGS)


def _write(data: dict[str, Any]) -> None:
    tmp = CONFIG_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
    tmp.replace(CONFIG_FILE)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except Exception:
        return None


def _normalize_plan(plan: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    p = _merge(fallback, plan or {})
    for key in ['price_monthly', 'price_yearly', 'daily_scans', 'daily_cleans', 'monthly_files', 'batch_files', 'history_days']:
        try:
            p[key] = max(0, int(float(p.get(key, 0))))
        except Exception:
            p[key] = fallback.get(key, 0)
    for key in ['audit_reports', 'advanced_pdf', 'api_access']:
        p[key] = bool(p.get(key))
    file_mb = p.setdefault('file_mb', {})
    for family, value in fallback.get('file_mb', {}).items():
        try:
            file_mb[family] = max(1, int(float(file_mb.get(family, value))))
        except Exception:
            file_mb[family] = value
    return p


def sanitize_coupon(coupon: dict[str, Any]) -> dict[str, Any]:
    code = str(coupon.get('code') or '').strip().upper().replace(' ', '-')[:40]
    try:
        percent = max(0, min(95, int(float(coupon.get('percent', 0)))))
    except Exception:
        percent = 0
    return {
        'id': str(coupon.get('id') or secrets.token_urlsafe(8)),
        'code': code,
        'percent': percent,
        'enabled': bool(coupon.get('enabled', True)),
        'applies_to': [p for p in (coupon.get('applies_to') or ['pro', 'team']) if p in DEFAULT_SETTINGS['plans']],
        'starts_at': str(coupon.get('starts_at') or '').strip(),
        'ends_at': str(coupon.get('ends_at') or '').strip(),
        'max_redemptions': int(coupon.get('max_redemptions') or 0),
        'redemptions': int(coupon.get('redemptions') or 0),
        'notes': str(coupon.get('notes') or '').strip()[:500],
        'created_at': str(coupon.get('created_at') or NOW().isoformat()),
    }


def sanitize_affiliate(link: dict[str, Any]) -> dict[str, Any]:
    return {
        'id': str(link.get('id') or secrets.token_urlsafe(8)),
        'label': str(link.get('label') or '').strip()[:80],
        'url': str(link.get('url') or '').strip(),
        'enabled': bool(link.get('enabled', True)),
        'notes': str(link.get('notes') or '').strip()[:500],
        'created_at': str(link.get('created_at') or NOW().isoformat()),
    }


def sanitize_settings(data: dict[str, Any]) -> dict[str, Any]:
    clean = _merge(DEFAULT_SETTINGS, data or {})
    for name, fallback in DEFAULT_SETTINGS['plans'].items():
        clean['plans'][name] = _normalize_plan(clean.get('plans', {}).get(name, {}), fallback)
    promo = clean.setdefault('promo', {})
    promo['enabled'] = bool(promo.get('enabled'))
    try:
        promo['percent'] = max(0, min(95, int(float(promo.get('percent', 0)))))
    except Exception:
        promo['percent'] = 0
    for key in ['headline', 'message', 'coupon_code', 'affiliate_url', 'starts_at', 'ends_at']:
        promo[key] = str(promo.get(key) or '').strip()
    clean['coupons'] = [sanitize_coupon(c) for c in clean.get('coupons', []) if isinstance(c, dict)]
    clean['affiliate_links'] = [sanitize_affiliate(a) for a in clean.get('affiliate_links', []) if isinstance(a, dict)]
    return clean


def read_settings() -> dict[str, Any]:
    data = sanitize_settings(_read_raw())
    if not CONFIG_FILE.exists():
        _write(data)
    return data


def update_settings(patch: dict[str, Any]) -> dict[str, Any]:
    data = read_settings()
    data = _merge(data, patch or {})
    data = sanitize_settings(data)
    _write(data)
    return data


def set_promo_percent_days(percent: int, days: int, headline: str | None = None, message: str | None = None, coupon_code: str | None = None, affiliate_url: str | None = None) -> dict[str, Any]:
    now = NOW()
    patch: dict[str, Any] = {'promo': {'enabled': True, 'percent': int(percent), 'starts_at': now.isoformat(), 'ends_at': (now + timedelta(days=max(1, int(days)))).isoformat()}}
    if headline is not None: patch['promo']['headline'] = headline
    if message is not None: patch['promo']['message'] = message
    if coupon_code is not None: patch['promo']['coupon_code'] = coupon_code
    if affiliate_url is not None: patch['promo']['affiliate_url'] = affiliate_url
    return update_settings(patch)


def add_coupon(coupon: dict[str, Any]) -> dict[str, Any]:
    data = read_settings()
    new_coupon = sanitize_coupon(coupon)
    if not new_coupon['code']:
        raise ValueError('Coupon code is required.')
    coupons = [c for c in data.get('coupons', []) if c.get('code') != new_coupon['code']]
    coupons.insert(0, new_coupon)
    data['coupons'] = coupons[:100]
    _write(data)
    return new_coupon


def remove_coupon(coupon_id: str) -> None:
    data = read_settings()
    data['coupons'] = [c for c in data.get('coupons', []) if c.get('id') != coupon_id and c.get('code') != coupon_id]
    _write(data)


def add_affiliate(link: dict[str, Any]) -> dict[str, Any]:
    data = read_settings()
    new_link = sanitize_affiliate(link)
    if not new_link['label'] or not new_link['url']:
        raise ValueError('Affiliate label and URL are required.')
    links = [a for a in data.get('affiliate_links', []) if a.get('id') != new_link['id']]
    links.insert(0, new_link)
    data['affiliate_links'] = links[:50]
    _write(data)
    return new_link


def remove_affiliate(link_id: str) -> None:
    data = read_settings()
    data['affiliate_links'] = [a for a in data.get('affiliate_links', []) if a.get('id') != link_id]
    _write(data)


def public_config() -> dict[str, Any]:
    data = read_settings()
    promo = dict(data.get('promo', {}))
    now = NOW()
    start = _parse_dt(promo.get('starts_at'))
    end = _parse_dt(promo.get('ends_at'))
    active = bool(promo.get('enabled')) and (not start or now >= start) and (not end or now <= end)
    seconds_remaining = 0
    days_remaining = 0
    if active and end:
        seconds_remaining = max(0, int((end - now).total_seconds()))
        days_remaining = max(1, (seconds_remaining + 86399) // 86400)
    promo['active'] = active
    promo['days_remaining'] = days_remaining
    promo['seconds_remaining'] = seconds_remaining
    promo['display_text'] = ''
    if active:
        promo['display_text'] = (promo.get('message') or '').replace('{percent}', str(promo.get('percent', 0))).replace('{days}', str(days_remaining))

    plans_by_name = data.get('plans', {})
    checkout_price_available = False
    for name, plan in plans_by_name.items():
        if name == 'free':
            continue
        if plan.get('stripe_price_id_monthly') or plan.get('stripe_price_id_yearly') or settings.stripe_price_id(name, 'monthly') or settings.stripe_price_id(name, 'yearly'):
            checkout_price_available = True
            break

    billing = dict(data.get('billing', {}))
    billing.update({
        'stripe_ready': bool(settings.stripe_secret_key),
        'checkout_enabled': bool(settings.stripe_secret_key and checkout_price_available),
        'customer_portal_enabled': bool(settings.stripe_secret_key),
        'webhook_secret_configured': bool(settings.stripe_webhook_secret),
        'publishable_key_configured': bool(settings.stripe_publishable_key),
    })
    return {
        'plans': list(plans_by_name.values()),
        'plans_by_name': plans_by_name,
        'promo': promo,
        'coupons': [c for c in data.get('coupons', []) if c.get('enabled')],
        'affiliate_links': [a for a in data.get('affiliate_links', []) if a.get('enabled')],
        'billing': billing,
    }


def effective_plan(name: str) -> dict[str, Any]:
    settings_data = read_settings()
    return settings_data.get('plans', {}).get(name, settings_data['plans']['free'])
