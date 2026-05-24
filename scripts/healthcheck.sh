#!/usr/bin/env bash
set -euo pipefail
curl -f http://localhost:8000/health
curl -f http://localhost:3000 >/dev/null
