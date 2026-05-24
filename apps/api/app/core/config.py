from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = 'development'
    secret_key: str = 'change-me-in-production'
    cors_origins: str = 'http://localhost:3000'
    frontend_url: str = 'http://localhost:3000'
    redis_url: str = 'redis://redis:6379/0'
    storage_dir: Path = Path('/data/privacy-toolbox')

    # Global hard upload ceiling. Plan-specific limits are stricter and enforced separately.
    # Keep this modest on a single low-cost AWS VPS; raise only after moving heavy jobs to larger workers.
    max_upload_mb: int = 512
    download_token_ttl_minutes: int = 10
    job_ttl_minutes: int = 60
    rate_limit_per_minute: int = 45
    auth_cookie_name: str = 'pt_session'
    auth_cookie_secure: bool = False
    upload_session_cookie_name: str = 'pt_upload_session'
    csrf_cookie_name: str = 'pt_csrf'
    admin_dashboard_path: str = '/dashboard'

    # Hard safety limits for ZIP and OOXML containers.
    zip_max_entry_mb: int = 256
    zip_max_total_uncompressed_mb: int = 1024
    zip_max_compression_ratio: int = 80
    zip_max_depth: int = 10

    # Email verification / transactional email. In development, if SMTP_HOST is empty,
    # verification codes are written to backend logs and /data email outbox for testing.
    smtp_host: str = ''
    smtp_port: int = 587
    smtp_user: str = ''
    smtp_password: str = ''
    smtp_from_email: str = 'gulimran980@gmail.com'
    smtp_from_name: str = 'Privacy Toolbox'
    contact_admin_email: str = 'gulimran980@gmail.com'
    smtp_use_tls: bool = True
    verification_code_ttl_minutes: int = 15

    # OAuth login providers. Leave empty until credentials are created.
    google_client_id: str = ''
    google_client_secret: str = ''
    google_redirect_uri: str = ''
    microsoft_client_id: str = ''
    microsoft_client_secret: str = ''
    microsoft_tenant_id: str = 'common'
    microsoft_redirect_uri: str = ''
    github_client_id: str = ''
    github_client_secret: str = ''
    github_redirect_uri: str = ''

    # Safe admin bootstrap. First registered user is NEVER auto-admin.
    bootstrap_admin_email: str = ''
    bootstrap_admin_password: str = ''

    # Stripe billing. Checkout/webhook routes stay disabled until keys and price IDs are set.
    stripe_secret_key: str = ''
    stripe_webhook_secret: str = ''
    stripe_publishable_key: str = ''
    stripe_success_path: str = '/dashboard?billing=success'
    stripe_cancel_path: str = '/pricing?billing=cancelled'
    stripe_price_id_pro_monthly: str = ''
    stripe_price_id_pro_yearly: str = ''
    stripe_price_id_team_monthly: str = ''
    stripe_price_id_team_yearly: str = ''
    stripe_price_id_business_monthly: str = ''
    stripe_price_id_business_yearly: str = ''

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {'production', 'prod'}

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip().rstrip('/') for o in self.cors_origins.split(',') if o.strip()]

    def stripe_price_id(self, plan: str, interval: str) -> str:
        key = f'stripe_price_id_{plan}_{interval}'.lower()
        return str(getattr(self, key, '') or '')


settings = Settings()

if settings.is_production:
    if settings.secret_key in {'change-me-in-production', 'replace-this-with-a-long-random-secret'} or len(settings.secret_key) < 32:
        raise RuntimeError('SECRET_KEY must be a strong 32+ character random value in production.')
    if not settings.auth_cookie_secure:
        raise RuntimeError('AUTH_COOKIE_SECURE=true is required in production.')
    if '*' in settings.allowed_origins:
        raise RuntimeError('Wildcard CORS origins are not allowed in production.')
    if settings.max_upload_mb > 1024:
        raise RuntimeError('MAX_UPLOAD_MB is too high for the low-cost AWS profile. Start at 512 or 1024 and raise only after scaling workers/storage.')

settings.storage_dir.mkdir(parents=True, exist_ok=True)
