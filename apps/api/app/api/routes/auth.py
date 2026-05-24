from __future__ import annotations

from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings
from app.core.plans import PLANS, plan_dict
from app.core.rate_limit import allow, client_ip
from app.services import user_service

router = APIRouter(prefix='/api/auth', tags=['auth'])

class RegisterPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10)
    name: str = ''

class LoginPayload(BaseModel):
    email: EmailStr
    password: str

class VerifyEmailPayload(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=12)

class ResendVerificationPayload(BaseModel):
    email: EmailStr


def _frontend(path: str, **query: str) -> str:
    base = settings.frontend_url.rstrip('/')
    qs = urlencode({k: v for k, v in query.items() if v})
    return f"{base}{path}{('?' + qs) if qs else ''}"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(settings.auth_cookie_name, token, httponly=True, secure=settings.auth_cookie_secure, samesite='lax', max_age=user_service.TOKEN_MAX_AGE, path='/')


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.auth_cookie_name, path='/')


def current_user(authorization: str | None = Header(default=None), cookie_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name)) -> dict | None:
    token = ''
    if authorization:
        scheme, _, bearer = authorization.partition(' ')
        if scheme.lower() == 'bearer' and bearer:
            token = bearer
        else:
            raise HTTPException(status_code=401, detail='Invalid authorization header.')
    elif cookie_token:
        token = cookie_token
    if not token:
        return None
    try:
        return user_service.verify_auth_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


def require_user(user: dict | None = Depends(current_user)) -> dict:
    if not user:
        raise HTTPException(status_code=401, detail='Login required.')
    return user


def require_admin(user: dict = Depends(require_user)) -> dict:
    if user.get('role') != 'admin':
        raise HTTPException(status_code=404, detail='Not found.')
    return user


@router.post('/register')
def register(payload: RegisterPayload, request: Request):
    if not allow(f'auth:register:{client_ip(request)}', limit=5, window=3600):
        raise HTTPException(status_code=429, detail='Too many registration attempts. Please try again later.')
    try:
        user = user_service.create_user(payload.email, payload.password, payload.name)
        return {'ok': True, 'requires_verification': True, 'email': user['email'], 'message': 'Account created. Check your email for the verification code.'}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post('/verify-email')
def verify_email(payload: VerifyEmailPayload, request: Request):
    if not allow(f'auth:verify:{payload.email.lower()}:{client_ip(request)}', limit=10, window=900):
        raise HTTPException(status_code=429, detail='Too many verification attempts. Please request a new code later.')
    try:
        user = user_service.verify_email_code(payload.email, payload.code)
        return {'ok': True, 'user': user, 'message': 'Email verified. You can now log in.'}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post('/resend-verification')
def resend_verification(payload: ResendVerificationPayload, request: Request):
    if not allow(f'auth:resend:{payload.email.lower()}:{client_ip(request)}', limit=3, window=900):
        raise HTTPException(status_code=429, detail='Too many code requests. Please wait before requesting another code.')
    return user_service.resend_verification(payload.email)


@router.post('/login')
def login(payload: LoginPayload, response: Response, request: Request):
    if not allow(f'auth:login:{payload.email.lower()}:{client_ip(request)}', limit=8, window=900):
        raise HTTPException(status_code=429, detail='Too many login attempts. Please wait and try again.')
    try:
        user = user_service.authenticate(payload.email, payload.password)
        token = user_service.issue_token(user)
        _set_session_cookie(response, token)
        return {'user': user}
    except ValueError as exc:
        # Intentionally generic except verification message, so users know next step.
        detail = str(exc)
        raise HTTPException(status_code=401, detail=detail)


@router.get('/me')
def me(user: dict | None = Depends(current_user)):
    return {'authenticated': bool(user), 'user': user, 'plans': [plan_dict(PLANS[name]) for name in PLANS]}


@router.post('/logout')
def logout(response: Response):
    _clear_session_cookie(response)
    return {'ok': True}


def _provider_config(provider: str) -> dict[str, str]:
    if provider == 'google':
        return {
            'client_id': settings.google_client_id,
            'client_secret': settings.google_client_secret,
            'redirect_uri': settings.google_redirect_uri or f"{settings.frontend_url.rstrip('/').replace('http://localhost:3000','http://localhost:8000')}/api/auth/oauth/google/callback",
            'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'userinfo_url': 'https://openidconnect.googleapis.com/v1/userinfo',
            'scope': 'openid email profile',
        }
    if provider == 'microsoft':
        tenant = settings.microsoft_tenant_id or 'common'
        return {
            'client_id': settings.microsoft_client_id,
            'client_secret': settings.microsoft_client_secret,
            'redirect_uri': settings.microsoft_redirect_uri or f"{settings.frontend_url.rstrip('/').replace('http://localhost:3000','http://localhost:8000')}/api/auth/oauth/microsoft/callback",
            'authorize_url': f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize',
            'token_url': f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token',
            'userinfo_url': 'https://graph.microsoft.com/oidc/userinfo',
            'scope': 'openid email profile',
        }
    if provider == 'github':
        return {
            'client_id': settings.github_client_id,
            'client_secret': settings.github_client_secret,
            'redirect_uri': settings.github_redirect_uri or f"{settings.frontend_url.rstrip('/').replace('http://localhost:3000','http://localhost:8000')}/api/auth/oauth/github/callback",
            'authorize_url': 'https://github.com/login/oauth/authorize',
            'token_url': 'https://github.com/login/oauth/access_token',
            'userinfo_url': 'https://api.github.com/user',
            'emails_url': 'https://api.github.com/user/emails',
            'scope': 'read:user user:email',
        }
    raise HTTPException(status_code=404, detail='OAuth provider not supported.')


@router.get('/oauth/{provider}/start')
def oauth_start(provider: str):
    cfg = _provider_config(provider)
    if not cfg.get('client_id') or not cfg.get('client_secret'):
        return RedirectResponse(_frontend('/auth/login', error=f'{provider.title()} login is not configured yet.'))
    state = user_service.issue_oauth_state(provider)
    params = {
        'client_id': cfg['client_id'],
        'redirect_uri': cfg['redirect_uri'],
        'response_type': 'code',
        'scope': cfg['scope'],
        'state': state,
    }
    if provider == 'google':
        params['access_type'] = 'online'
        params['prompt'] = 'select_account'
    return RedirectResponse(f"{cfg['authorize_url']}?{urlencode(params)}")


@router.get('/oauth/{provider}/callback')
def oauth_callback(provider: str, code: str = '', state: str = ''):
    cfg = _provider_config(provider)
    try:
        user_service.verify_oauth_state(provider, state)
        if not code:
            raise ValueError('Missing authorization code.')
        with httpx.Client(timeout=20) as client:
            token_resp = client.post(cfg['token_url'], data={
                'client_id': cfg['client_id'],
                'client_secret': cfg['client_secret'],
                'code': code,
                'redirect_uri': cfg['redirect_uri'],
                'grant_type': 'authorization_code',
            }, headers={'Accept': 'application/json'})
            token_resp.raise_for_status()
            token_data = token_resp.json()
            access_token = token_data.get('access_token')
            if not access_token:
                raise ValueError('OAuth provider did not return an access token.')
            headers = {'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'}
            info = client.get(cfg['userinfo_url'], headers=headers).json()
            email = info.get('email') or info.get('mail') or info.get('userPrincipalName') or ''
            name = info.get('name') or info.get('login') or ''
            sub = str(info.get('sub') or info.get('id') or '')
            if provider == 'github' and not email:
                emails = client.get(cfg['emails_url'], headers=headers).json()
                if isinstance(emails, list):
                    primary = next((e for e in emails if e.get('primary') and e.get('verified')), None) or next((e for e in emails if e.get('verified')), None)
                    email = (primary or {}).get('email', '')
            user = user_service.create_or_update_oauth_user(email, name, provider, sub)
            token = user_service.issue_token(user)
        redirect = RedirectResponse(_frontend('/tools', login='success'))
        _set_session_cookie(redirect, token)
        return redirect
    except Exception as exc:
        return RedirectResponse(_frontend('/auth/login', error='OAuth login failed. Please try again or use email login.'))
