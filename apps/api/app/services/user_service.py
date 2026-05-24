from __future__ import annotations

import hashlib
import hmac
import json
import fcntl
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import settings
from app.core.plans import get_plan, plan_dict
from app.core.security import random_id
from app.services.email_service import send_verification_code

USERS_DIR = settings.storage_dir / 'users'
USERS_DIR.mkdir(parents=True, exist_ok=True)
USERS_FILE = USERS_DIR / 'users.json'
TOKEN_SALT = 'privacy-toolbox-auth-v2'
OAUTH_STATE_SALT = 'privacy-toolbox-oauth-state-v1'
TOKEN_MAX_AGE = 60 * 60 * 24 * 30


def _use_postgres() -> bool:
    return settings.user_storage_backend.lower() == 'postgres' and bool(settings.database_url)


def _pg_connect():
    import psycopg
    from psycopg.rows import dict_row
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def _pg_init(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY,
          email TEXT NOT NULL UNIQUE,
          name TEXT NOT NULL DEFAULT '',
          password_hash TEXT NOT NULL DEFAULT '',
          plan TEXT NOT NULL DEFAULT 'free',
          role TEXT NOT NULL DEFAULT 'user',
          email_verified BOOLEAN NOT NULL DEFAULT FALSE,
          auth_provider TEXT NOT NULL DEFAULT 'password',
          requires_password_change BOOLEAN NOT NULL DEFAULT FALSE,
          plan_grant_reason TEXT NOT NULL DEFAULT '',
          plan_expires_at TIMESTAMPTZ NULL,
          stripe_customer_id TEXT NOT NULL DEFAULT '',
          stripe_subscription_id TEXT NOT NULL DEFAULT '',
          stripe_subscription_status TEXT NOT NULL DEFAULT '',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          last_login_at TIMESTAMPTZ NULL,
          raw_json JSONB NOT NULL DEFAULT '{}'::jsonb
        );
        CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
        CREATE INDEX IF NOT EXISTS idx_users_plan ON users (plan);
        CREATE INDEX IF NOT EXISTS idx_users_stripe_customer ON users (stripe_customer_id);
        CREATE INDEX IF NOT EXISTS idx_users_stripe_subscription ON users (stripe_subscription_id);
        """
    )


def _pg_row_to_user(row: dict[str, Any]) -> dict[str, Any]:
    raw = dict(row.get('raw_json') or {})
    for key in [
        'id', 'email', 'name', 'password_hash', 'plan', 'role', 'email_verified',
        'auth_provider', 'requires_password_change', 'plan_grant_reason',
        'stripe_customer_id', 'stripe_subscription_id', 'stripe_subscription_status',
    ]:
        raw[key] = row.get(key) if row.get(key) is not None else raw.get(key, '')
    for key in ['created_at', 'updated_at', 'last_login_at', 'plan_expires_at']:
        value = row.get(key)
        raw[key] = value.isoformat() if hasattr(value, 'isoformat') else (value or raw.get(key, ''))
    return raw


def _pg_upsert_user(conn, user: dict[str, Any]) -> None:
    from psycopg.types.json import Jsonb
    raw = dict(user)
    values = {
        'id': user.get('id') or random_id('user'),
        'email': str(user.get('email') or '').lower(),
        'name': user.get('name') or '',
        'password_hash': user.get('password_hash') or '',
        'plan': user.get('plan') or 'free',
        'role': user.get('role') or 'user',
        'email_verified': bool(user.get('email_verified')),
        'auth_provider': user.get('auth_provider') or 'password',
        'requires_password_change': bool(user.get('requires_password_change')),
        'plan_grant_reason': user.get('plan_grant_reason') or '',
        'plan_expires_at': user.get('plan_expires_at') or None,
        'stripe_customer_id': user.get('stripe_customer_id') or '',
        'stripe_subscription_id': user.get('stripe_subscription_id') or '',
        'stripe_subscription_status': user.get('stripe_subscription_status') or '',
        'created_at': user.get('created_at') or _now().isoformat(),
        'updated_at': user.get('updated_at') or _now().isoformat(),
        'last_login_at': user.get('last_login_at') or None,
        'raw_json': Jsonb(raw),
    }
    conn.execute(
        """
        INSERT INTO users (
          id,email,name,password_hash,plan,role,email_verified,auth_provider,requires_password_change,
          plan_grant_reason,plan_expires_at,stripe_customer_id,stripe_subscription_id,stripe_subscription_status,
          created_at,updated_at,last_login_at,raw_json
        ) VALUES (
          %(id)s,%(email)s,%(name)s,%(password_hash)s,%(plan)s,%(role)s,%(email_verified)s,%(auth_provider)s,%(requires_password_change)s,
          %(plan_grant_reason)s,%(plan_expires_at)s,%(stripe_customer_id)s,%(stripe_subscription_id)s,%(stripe_subscription_status)s,
          %(created_at)s,%(updated_at)s,%(last_login_at)s,%(raw_json)s
        )
        ON CONFLICT (email) DO UPDATE SET
          id=EXCLUDED.id,
          name=EXCLUDED.name,
          password_hash=EXCLUDED.password_hash,
          plan=EXCLUDED.plan,
          role=EXCLUDED.role,
          email_verified=EXCLUDED.email_verified,
          auth_provider=EXCLUDED.auth_provider,
          requires_password_change=EXCLUDED.requires_password_change,
          plan_grant_reason=EXCLUDED.plan_grant_reason,
          plan_expires_at=EXCLUDED.plan_expires_at,
          stripe_customer_id=EXCLUDED.stripe_customer_id,
          stripe_subscription_id=EXCLUDED.stripe_subscription_id,
          stripe_subscription_status=EXCLUDED.stripe_subscription_status,
          updated_at=EXCLUDED.updated_at,
          last_login_at=EXCLUDED.last_login_at,
          raw_json=EXCLUDED.raw_json
        """,
        values,
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load_users() -> dict[str, dict[str, Any]]:
    if _use_postgres():
        try:
            with _pg_connect() as conn:
                _pg_init(conn)
                rows = conn.execute('SELECT * FROM users').fetchall()
                return {str(row['email']).lower(): _pg_row_to_user(row) for row in rows}
        except Exception:
            if settings.is_production:
                raise
            return {}
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _save_users(users: dict[str, dict[str, Any]]) -> None:
    if _use_postgres():
        with _pg_connect() as conn:
            _pg_init(conn)
            for user in users.values():
                _pg_upsert_user(conn, user)
            conn.commit()
        return
    tmp = USERS_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(users, indent=2, sort_keys=True), encoding='utf-8')
    tmp.replace(USERS_FILE)


def _with_user_lock(fn):
    if _use_postgres():
        # PostgreSQL centralizes storage for all API tasks. The small critical sections
        # here are kept compatible with the JSON path; high-scale deployments should
        # move account updates to row-level SQL operations/Alembic models.
        return fn()
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = USERS_DIR / 'users.lock'
    with lock_path.open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            return fn()
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _serializer(salt: str = TOKEN_SALT) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key, salt=salt)


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 210_000)
    return f'pbkdf2_sha256$210000${salt}${digest.hex()}'


def _verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt, digest = stored.split('$', 3)
        if algo != 'pbkdf2_sha256':
            return False
        new_digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), int(rounds)).hex()
        return hmac.compare_digest(new_digest, digest)
    except Exception:
        return False


def _new_code() -> str:
    return f'{secrets.randbelow(1000000):06d}'


def _verification_expiry() -> str:
    return (_now() + timedelta(minutes=settings.verification_code_ttl_minutes)).isoformat()


def _effective_plan_name(user: dict[str, Any]) -> str:
    plan_name = user.get('plan') or 'free'
    expires = str(user.get('plan_expires_at') or '').strip()
    if expires:
        try:
            if datetime.fromisoformat(expires.replace('Z', '+00:00')) < _now():
                return 'free'
        except Exception:
            try:
                if datetime.fromisoformat(expires + 'T23:59:59+00:00') < _now():
                    return 'free'
            except Exception:
                pass
    return plan_name


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    plan_name = _effective_plan_name(user)
    return {
        'id': user['id'],
        'email': user['email'],
        'name': user.get('name') or '',
        'plan': plan_name,
        'stored_plan': user.get('plan') or 'free',
        'role': user.get('role') or 'user',
        'email_verified': bool(user.get('email_verified')),
        'auth_provider': user.get('auth_provider', 'password'),
        'created_at': user.get('created_at'),
        'last_login_at': user.get('last_login_at', ''),
        'requires_password_change': bool(user.get('requires_password_change', False)),
        'stripe_customer_id': user.get('stripe_customer_id', ''),
        'stripe_subscription_id': user.get('stripe_subscription_id', ''),
        'stripe_subscription_status': user.get('stripe_subscription_status', ''),
        'limits': plan_dict(get_plan(plan_name)),
    }


def list_users() -> list[dict[str, Any]]:
    users = _load_users()
    rows = []
    for u in users.values():
        rows.append(_public_user(u) | {
            'plan_grant_reason': u.get('plan_grant_reason', ''),
            'plan_expires_at': u.get('plan_expires_at', ''),
            'created_by_admin': bool(u.get('created_by_admin')),
        })
    return sorted(rows, key=lambda u: u.get('created_at') or '', reverse=True)


def create_user(email: str, password: str, name: str = '') -> dict[str, Any]:
    email = email.strip().lower()
    if not email or '@' not in email:
        raise ValueError('A valid email address is required.')
    if len(password) < 10:
        raise ValueError('Password must be at least 10 characters.')
    users = _load_users()
    if email in users:
        raise ValueError('An account with this email already exists.')
    role = 'user'
    code = _new_code()
    user = {
        'id': random_id('user'),
        'email': email,
        'name': name.strip(),
        'password_hash': _hash_password(password),
        'plan': 'free',
        'role': role,
        'email_verified': False,
        'verification_code_hash': _hash_password(code),
        'verification_expires_at': _verification_expiry(),
        'auth_provider': 'password',
        'created_at': _now().isoformat(),
    }
    users[email] = user
    _save_users(users)
    send_verification_code(email, code, name)
    return _public_user(user) | {'verification_sent': True}


def resend_verification(email: str) -> dict[str, Any]:
    users = _load_users()
    key = email.strip().lower()
    user = users.get(key)
    # Generic response to reduce account enumeration.
    generic = {'ok': True, 'message': 'If an unverified account exists, a verification code has been sent.'}
    if not user or user.get('email_verified'):
        return generic
    code = _new_code()
    user['verification_code_hash'] = _hash_password(code)
    user['verification_expires_at'] = _verification_expiry()
    user['verification_last_sent_at'] = _now().isoformat()
    user['verification_attempts'] = 0
    users[key] = user
    _save_users(users)
    send_verification_code(key, code, user.get('name') or '')
    return generic


def verify_email_code(email: str, code: str) -> dict[str, Any]:
    def _verify():
        users = _load_users()
        key = email.strip().lower()
        user = users.get(key)
        if not user:
            raise ValueError('Invalid or expired verification code.')
        if user.get('email_verified'):
            return _public_user(user)
        expires = str(user.get('verification_expires_at') or '')
        try:
            if datetime.fromisoformat(expires.replace('Z', '+00:00')) < _now():
                raise ValueError('Invalid or expired verification code.')
        except ValueError:
            raise
        except Exception:
            raise ValueError('Invalid or expired verification code.')
        attempts = int(user.get('verification_attempts') or 0)
        if attempts >= 8:
            raise ValueError('Too many verification attempts. Request a new code.')
        if not _verify_password(code.strip(), user.get('verification_code_hash', '')):
            user['verification_attempts'] = attempts + 1
            users[key] = user
            _save_users(users)
            raise ValueError('Invalid or expired verification code.')
        user['email_verified'] = True
        user['verified_at'] = _now().isoformat()
        user.pop('verification_code_hash', None)
        user.pop('verification_expires_at', None)
        user.pop('verification_attempts', None)
        users[key] = user
        _save_users(users)
        return _public_user(user)
    return _with_user_lock(_verify)


def authenticate(email: str, password: str) -> dict[str, Any]:
    users = _load_users()
    key = email.strip().lower()
    user = users.get(key)
    if not user or not _verify_password(password, user.get('password_hash', '')):
        raise ValueError('Invalid email or password.')
    if not user.get('email_verified'):
        raise ValueError('Please verify your email before logging in.')
    user['last_login_at'] = _now().isoformat()
    users[key] = user
    _save_users(users)
    return _public_user(user)


def create_user_by_admin(email: str, password: str, name: str = '', plan: str = 'free', role: str = 'user', plan_grant_reason: str = '', plan_expires_at: str = '', email_verified: bool = True, requires_password_change: bool = False) -> dict[str, Any]:
    email = email.strip().lower()
    if not email or '@' not in email:
        raise ValueError('A valid email address is required.')
    if len(password) < 10:
        raise ValueError('Admin-created passwords must be at least 10 characters.')
    users = _load_users()
    if email in users:
        raise ValueError('An account with this email already exists.')
    plan_obj = get_plan(plan)
    role = 'admin' if role == 'admin' else 'user'
    user = {
        'id': random_id('user'),
        'email': email,
        'name': name.strip(),
        'password_hash': _hash_password(password),
        'plan': plan_obj.name,
        'role': role,
        'email_verified': bool(email_verified),
        'auth_provider': 'password',
        'requires_password_change': bool(requires_password_change),
        'plan_grant_reason': plan_grant_reason.strip()[:500],
        'plan_expires_at': plan_expires_at.strip(),
        'created_at': _now().isoformat(),
        'created_by_admin': True,
    }
    users[email] = user
    _save_users(users)
    return _public_user(user) | {'plan_grant_reason': user.get('plan_grant_reason', ''), 'plan_expires_at': user.get('plan_expires_at', '')}


def update_user_by_admin(email: str, patch: dict[str, Any]) -> dict[str, Any]:
    users = _load_users()
    key = email.strip().lower()
    if key not in users:
        raise ValueError('User not found.')
    user = users[key]
    if 'plan' in patch and patch.get('plan'):
        user['plan'] = get_plan(str(patch.get('plan'))).name
    if 'role' in patch and patch.get('role') in {'user', 'admin'}:
        user['role'] = patch.get('role')
    if 'name' in patch:
        user['name'] = str(patch.get('name') or '').strip()
    if 'email_verified' in patch:
        user['email_verified'] = bool(patch.get('email_verified'))
    if 'requires_password_change' in patch:
        user['requires_password_change'] = bool(patch.get('requires_password_change'))
    if 'password' in patch and patch.get('password'):
        password = str(patch.get('password'))
        if len(password) < 10:
            raise ValueError('Password must be at least 10 characters.')
        user['password_hash'] = _hash_password(password)
    if 'plan_grant_reason' in patch:
        user['plan_grant_reason'] = str(patch.get('plan_grant_reason') or '').strip()[:500]
    if 'plan_expires_at' in patch:
        user['plan_expires_at'] = str(patch.get('plan_expires_at') or '').strip()
    user['updated_at'] = _now().isoformat()
    users[key] = user
    _save_users(users)
    return _public_user(user) | {'plan_grant_reason': user.get('plan_grant_reason', ''), 'plan_expires_at': user.get('plan_expires_at', '')}


def create_or_update_oauth_user(email: str, name: str, provider: str, provider_sub: str = '') -> dict[str, Any]:
    email = email.strip().lower()
    if not email or '@' not in email:
        raise ValueError('OAuth provider did not return a usable email address.')
    users = _load_users()
    user = users.get(email)
    if not user:
        role = 'user'
        user = {
            'id': random_id('user'),
            'email': email,
            'name': name.strip(),
            'password_hash': '',
            'plan': 'free',
            'role': role,
            'email_verified': True,
            'auth_provider': provider,
            'provider_accounts': {provider: provider_sub},
            'created_at': _now().isoformat(),
        }
    else:
        accounts = user.setdefault('provider_accounts', {})
        accounts[provider] = provider_sub
        user['email_verified'] = True
        user['auth_provider'] = user.get('auth_provider') or provider
        if name and not user.get('name'):
            user['name'] = name.strip()
    user['last_login_at'] = _now().isoformat()
    users[email] = user
    _save_users(users)
    return _public_user(user)


def issue_token(user: dict[str, Any]) -> str:
    return _serializer().dumps({'sub': user['id'], 'email': user['email']})


def verify_auth_token(token: str) -> dict[str, Any]:
    try:
        payload = _serializer().loads(token, max_age=TOKEN_MAX_AGE)
    except SignatureExpired as exc:
        raise ValueError('Session expired. Please log in again.') from exc
    except BadSignature as exc:
        raise ValueError('Invalid session token.') from exc
    email = str(payload.get('email', '')).lower()
    user = _load_users().get(email)
    if not user:
        raise ValueError('User account not found.')
    if not user.get('email_verified'):
        raise ValueError('Email verification required.')
    return _public_user(user)


def issue_oauth_state(provider: str) -> str:
    return _serializer(OAUTH_STATE_SALT).dumps({'provider': provider, 'nonce': secrets.token_urlsafe(16)})


def verify_oauth_state(provider: str, state: str) -> None:
    try:
        payload = _serializer(OAUTH_STATE_SALT).loads(state, max_age=600)
    except Exception as exc:
        raise ValueError('Invalid or expired OAuth state.') from exc
    if payload.get('provider') != provider:
        raise ValueError('Invalid OAuth provider state.')


def set_user_plan(email: str, plan: str) -> dict[str, Any]:
    users = _load_users()
    key = email.strip().lower()
    if key not in users:
        raise ValueError('User not found.')
    get_plan(plan)
    users[key]['plan'] = get_plan(plan).name
    _save_users(users)
    return _public_user(users[key])


def _find_key_by_user_id(users: dict[str, dict[str, Any]], user_id: str) -> str:
    for key, user in users.items():
        if str(user.get('id') or '') == str(user_id or ''):
            return key
    return ''


def find_user_by_stripe(customer_id: str = '', subscription_id: str = '') -> dict[str, Any] | None:
    users = _load_users()
    for user in users.values():
        if customer_id and user.get('stripe_customer_id') == customer_id:
            return _public_user(user)
        if subscription_id and user.get('stripe_subscription_id') == subscription_id:
            return _public_user(user)
    return None


def set_user_billing_state(*, user_id: str = '', email: str = '', plan: str = 'free', stripe_customer_id: str = '', stripe_subscription_id: str = '', stripe_subscription_status: str = '', plan_grant_reason: str = '') -> dict[str, Any] | None:
    def _update():
        users = _load_users()
        key = email.strip().lower() if email else ''
        if key not in users and user_id:
            key = _find_key_by_user_id(users, user_id)
        if key not in users:
            return None
        user = users[key]
        user['plan'] = get_plan(plan).name
        if stripe_customer_id:
            user['stripe_customer_id'] = stripe_customer_id
        if stripe_subscription_id:
            user['stripe_subscription_id'] = stripe_subscription_id
        user['stripe_subscription_status'] = stripe_subscription_status
        user['plan_grant_reason'] = plan_grant_reason[:500]
        user['updated_at'] = _now().isoformat()
        users[key] = user
        _save_users(users)
        return _public_user(user)
    return _with_user_lock(_update)


def bootstrap_admin_from_env() -> dict[str, Any] | None:
    """Create the first admin only from explicit environment variables.

    This replaces unsafe "first registered user becomes admin" logic. It is idempotent and
    intended for Docker startup/admin setup, not public registration.
    """
    email = settings.bootstrap_admin_email.strip().lower()
    password = settings.bootstrap_admin_password
    if not email or not password:
        return None
    if len(password) < 14:
        raise RuntimeError('BOOTSTRAP_ADMIN_PASSWORD must be at least 14 characters.')

    def _bootstrap():
        users = _load_users()
        existing = users.get(email)
        if existing:
            changed = False
            if existing.get('role') != 'admin':
                existing['role'] = 'admin'; changed = True
            if not existing.get('email_verified'):
                existing['email_verified'] = True; changed = True
            if changed:
                existing['updated_at'] = _now().isoformat()
                users[email] = existing
                _save_users(users)
            return _public_user(existing)
        user = {
            'id': random_id('user'),
            'email': email,
            'name': 'Bootstrap Admin',
            'password_hash': _hash_password(password),
            'plan': 'business',
            'role': 'admin',
            'email_verified': True,
            'auth_provider': 'password',
            'created_at': _now().isoformat(),
            'created_by_bootstrap': True,
        }
        users[email] = user
        _save_users(users)
        return _public_user(user)
    return _with_user_lock(_bootstrap)
