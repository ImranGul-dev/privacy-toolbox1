#!/usr/bin/env python3
"""Validate production environment variables before deploying Privacy Toolbox.

Usage:
  set -a && source .env.production && set +a
  python scripts/validate-production-env.py

This script does not print secret values. It only reports missing or unsafe keys.
"""
from __future__ import annotations

import os
import sys

errors: list[str] = []
warnings: list[str] = []

def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()

def require(name: str) -> None:
    if not env(name):
        errors.append(f"Missing required env var: {name}")

app_env = env("APP_ENV", "development").lower()
if app_env not in {"production", "prod"}:
    warnings.append("APP_ENV is not production; production-only checks are warnings only.")

require("SECRET_KEY")
if len(env("SECRET_KEY")) < 32 or env("SECRET_KEY") in {"change-me-in-production", "CHANGE_TO_64_CHAR_RANDOM_SECRET"}:
    errors.append("SECRET_KEY must be a strong random value with at least 32 characters.")

for name in ["FRONTEND_URL", "NEXT_PUBLIC_API_BASE_URL", "NEXT_PUBLIC_SITE_URL", "CORS_ORIGINS"]:
    require(name)

if env("AUTH_COOKIE_SECURE", "false").lower() != "true":
    errors.append("AUTH_COOKIE_SECURE must be true for production HTTPS.")

if "*" in env("CORS_ORIGINS"):
    errors.append("CORS_ORIGINS must not include wildcard * in production.")

if env("REQUIRE_SMTP_IN_PRODUCTION", "true").lower() == "true":
    for name in ["SMTP_HOST", "SMTP_FROM_EMAIL"]:
        require(name)
    if not env("SMTP_USER") or not env("SMTP_PASSWORD"):
        warnings.append("SMTP_USER/SMTP_PASSWORD are empty. This is only OK for providers that allow unauthenticated SMTP from your network.")

if env("REQUIRE_OAUTH_PROVIDERS_IN_PRODUCTION", "false").lower() == "true":
    for prefix in ["GOOGLE", "MICROSOFT", "GITHUB"]:
        require(f"{prefix}_CLIENT_ID")
        require(f"{prefix}_CLIENT_SECRET")
        require(f"{prefix}_REDIRECT_URI")

if env("STORAGE_BACKEND", "local").lower() == "s3":
    require("S3_BUCKET")
    require("AWS_REGION")
else:
    warnings.append("STORAGE_BACKEND is local. This is OK for Lightsail MVP but not for horizontal ECS autoscaling.")

if env("USER_STORAGE_BACKEND", "json").lower() == "postgres":
    require("DATABASE_URL")
else:
    warnings.append("USER_STORAGE_BACKEND is json. This is OK for Lightsail MVP but not for multi-task autoscaling; use postgres for ECS production.")

if env("QUOTA_BACKEND", "local").lower() == "redis":
    require("REDIS_URL")
else:
    warnings.append("QUOTA_BACKEND is local. Use redis for shared quota enforcement across autoscaled API tasks.")

if env("REDIS_URL", "").startswith("redis://redis"):
    warnings.append("REDIS_URL points to local Docker Redis. Use ElastiCache/managed Redis for ECS autoscaling.")

if errors:
    print("Production environment validation failed:")
    for item in errors:
        print(f"  - {item}")
else:
    print("Production environment validation passed with no blocking errors.")

if warnings:
    print("\nWarnings:")
    for item in warnings:
        print(f"  - {item}")

sys.exit(1 if errors else 0)
