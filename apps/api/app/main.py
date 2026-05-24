from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import configure_logging
from app.api.routes import health, uploads, jobs, tools, tools_c2pa, auth, billing, api_keys, admin, public, analytics, contact
from app.services.user_service import bootstrap_admin_from_env

configure_logging()

# Explicit bootstrap only. Public registration never creates an admin.
try:
    bootstrap_admin_from_env()
except Exception:
    # Let startup continue in development, but production config validation already
    # rejects unsafe secrets/cookies. Admin bootstrap errors are visible in logs.
    if settings.is_production:
        raise

app = FastAPI(title='Privacy Toolbox API', version='0.3.0', description='Scan, clean and verify hidden file data before sharing.')
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type', 'X-CSRF-Token'],
)

SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS'}

@app.middleware('http')
async def csrf_and_security_headers(request: Request, call_next):
    if settings.is_production and request.method.upper() not in SAFE_METHODS:
        origin = (request.headers.get('origin') or '').rstrip('/')
        referer = request.headers.get('referer') or ''
        allowed = settings.allowed_origins
        if origin and origin not in allowed:
            from fastapi.responses import JSONResponse
            return JSONResponse({'detail': 'Cross-site request blocked.'}, status_code=403)
        if not origin and referer and not any(referer.startswith(o + '/') or referer == o for o in allowed):
            from fastapi.responses import JSONResponse
            return JSONResponse({'detail': 'Cross-site request blocked.'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cross-Origin-Resource-Policy'] = 'same-site'
    if settings.is_production:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        response.headers['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'"
    return response

# Legacy bypass routers were intentionally removed from app.include_router.
# All scan/clean/verify jobs must go through /api/tools/{tool_id}/{action},
# which enforces ownership, plan limits, quotas, and plugin validation.
for router_module in [health, uploads, jobs, tools, tools_c2pa, auth, billing, api_keys, admin, public, analytics, contact]:
    app.include_router(router_module.router)
