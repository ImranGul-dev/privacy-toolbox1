from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = 'development'
    secret_key: str = 'change-me-in-production'
    cors_origins: str = 'http://localhost:3000'
    frontend_url: str = 'http://localhost:3000'
    # Public API URL used for OAuth callbacks when the API is on a separate host.
    # If empty, the app assumes API and frontend share the same public domain through the proxy/ALB.
    api_public_url: str = ''
    redis_url: str = 'redis://redis:6379/0'
    storage_dir: Path = Path('/data/privacy-toolbox')

    # Celery queue separation. The single-server Lightsail worker can listen to
    # all queues, while ECS can run separate light/heavy worker services.
    celery_default_queue: str = 'default'
    celery_light_queue: str = 'light'
    celery_heavy_queue: str = 'heavy'
    celery_worker_queues: str = 'light,heavy,default,celery'
    worker_soft_time_limit_seconds: int = 18 * 60
    worker_hard_time_limit_seconds: int = 20 * 60

    # Optional AWS autoscaling stage placeholders. The current MVP remains local
    # unless these are enabled in a future migration after PostgreSQL/S3 testing.
    storage_backend: str = 'local'  # local|s3
    database_url: str = ''
    user_storage_backend: str = 'json'  # json|postgres
    quota_backend: str = 'local'  # local|redis
    aws_region: str = 'ap-south-1'
    s3_bucket: str = ''
    s3_upload_prefix: str = 'uploads/'
    s3_output_prefix: str = 'outputs/'
    s3_report_prefix: str = 'reports/'

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
    require_smtp_in_production: bool = True

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
    # Set true when you want production startup to fail unless Google, Microsoft, and GitHub OAuth are configured.
    # This keeps social-login buttons from silently shipping broken.
    require_oauth_providers_in_production: bool = False

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
    if settings.max_upload_mb > 1024 and settings.storage_backend != 's3':
        raise RuntimeError('MAX_UPLOAD_MB is too high for local single-server storage. Start at 512 or 1024 and raise only after scaling workers/storage.')
    if settings.storage_backend == 's3' and not settings.s3_bucket:
        raise RuntimeError('S3_BUCKET is required when STORAGE_BACKEND=s3.')
    if settings.user_storage_backend.lower() == 'postgres' and not settings.database_url:
        raise RuntimeError('DATABASE_URL is required when USER_STORAGE_BACKEND=postgres.')
    if settings.quota_backend.lower() == 'redis' and not settings.redis_url:
        raise RuntimeError('REDIS_URL is required when QUOTA_BACKEND=redis.')
    if settings.require_smtp_in_production and not settings.smtp_host:
        raise RuntimeError('SMTP_HOST is required in production so email verification codes can be delivered.')
    if settings.require_oauth_providers_in_production:
        missing = []
        for provider, client_id, client_secret in [
            ('Google', settings.google_client_id, settings.google_client_secret),
            ('Microsoft', settings.microsoft_client_id, settings.microsoft_client_secret),
            ('GitHub', settings.github_client_id, settings.github_client_secret),
        ]:
            if not client_id or not client_secret:
                missing.append(provider)
        if missing:
            raise RuntimeError('OAuth providers missing in production: ' + ', '.join(missing))

settings.storage_dir.mkdir(parents=True, exist_ok=True)
