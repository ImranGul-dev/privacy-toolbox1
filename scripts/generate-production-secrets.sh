#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import secrets
print('SECRET_KEY=' + secrets.token_urlsafe(64))
print('BOOTSTRAP_ADMIN_PASSWORD=' + secrets.token_urlsafe(24))
PY
