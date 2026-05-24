#!/usr/bin/env python3
"""Stage 4 helper: migrate local users.json into PostgreSQL.

Safe defaults:
- dry-run by default
- does not delete or modify users.json
- stores original source row in raw_json for rollback/debugging

Usage:
  python scripts/db/migrate_users_json_to_postgres.py --source /data/privacy-toolbox/users/users.json --database-url "$DATABASE_URL" --dry-run
  python scripts/db/migrate_users_json_to_postgres.py --source /data/privacy-toolbox/users/users.json --database-url "$DATABASE_URL" --apply

Requires:
  pip install "psycopg[binary]"
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_ts(value: Any):
    if not value:
        return None
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00'))
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, help='Path to users.json')
    parser.add_argument('--database-url', required=True, help='PostgreSQL connection string')
    parser.add_argument('--apply', action='store_true', help='Write to database')
    parser.add_argument('--dry-run', action='store_true', help='Preview only')
    args = parser.parse_args()

    source = Path(args.source)
    users = json.loads(source.read_text(encoding='utf-8')) if source.exists() else {}
    rows = list(users.values()) if isinstance(users, dict) else []
    print(f'Loaded {len(rows)} users from {source}')

    if not args.apply:
        print('Dry run only. Use --apply to write to PostgreSQL.')
        for row in rows[:5]:
            print({'id': row.get('id'), 'email': row.get('email'), 'plan': row.get('plan'), 'role': row.get('role')})
        return 0

    try:
        import psycopg
        from psycopg.types.json import Jsonb
    except Exception as exc:
        raise SystemExit('psycopg is required. Install with: pip install "psycopg[binary]"') from exc

    sql = '''
    INSERT INTO users (
      id, email, name, password_hash, plan, role, email_verified, auth_provider,
      requires_password_change, plan_grant_reason, plan_expires_at, stripe_customer_id,
      stripe_subscription_id, stripe_subscription_status, created_at, updated_at,
      last_login_at, raw_json
    ) VALUES (
      %(id)s, %(email)s, %(name)s, %(password_hash)s, %(plan)s, %(role)s, %(email_verified)s, %(auth_provider)s,
      %(requires_password_change)s, %(plan_grant_reason)s, %(plan_expires_at)s, %(stripe_customer_id)s,
      %(stripe_subscription_id)s, %(stripe_subscription_status)s, %(created_at)s, %(updated_at)s,
      %(last_login_at)s, %(raw_json)s
    ) ON CONFLICT (email) DO UPDATE SET
      name = EXCLUDED.name,
      plan = EXCLUDED.plan,
      role = EXCLUDED.role,
      email_verified = EXCLUDED.email_verified,
      stripe_customer_id = EXCLUDED.stripe_customer_id,
      stripe_subscription_id = EXCLUDED.stripe_subscription_id,
      stripe_subscription_status = EXCLUDED.stripe_subscription_status,
      updated_at = now(),
      raw_json = EXCLUDED.raw_json;
    '''

    schema_path = Path(__file__).resolve().parents[2] / 'infra' / 'db' / 'postgresql_schema.sql'

    with psycopg.connect(args.database_url) as conn:
        with conn.cursor() as cur:
            if schema_path.exists():
                cur.execute(schema_path.read_text(encoding='utf-8'))
            for row in rows:
                now = datetime.now(timezone.utc)
                cur.execute(sql, {
                    'id': row.get('id') or row.get('email'),
                    'email': str(row.get('email') or '').lower(),
                    'name': row.get('name') or '',
                    'password_hash': row.get('password_hash') or '',
                    'plan': row.get('plan') or 'free',
                    'role': row.get('role') or 'user',
                    'email_verified': bool(row.get('email_verified')),
                    'auth_provider': row.get('auth_provider') or 'password',
                    'requires_password_change': bool(row.get('requires_password_change')),
                    'plan_grant_reason': row.get('plan_grant_reason') or '',
                    'plan_expires_at': parse_ts(row.get('plan_expires_at')),
                    'stripe_customer_id': row.get('stripe_customer_id') or '',
                    'stripe_subscription_id': row.get('stripe_subscription_id') or '',
                    'stripe_subscription_status': row.get('stripe_subscription_status') or '',
                    'created_at': parse_ts(row.get('created_at')) or now,
                    'updated_at': now,
                    'last_login_at': parse_ts(row.get('last_login_at')),
                    'raw_json': Jsonb(row),
                })
        conn.commit()
    print(f'Migrated {len(rows)} users into PostgreSQL.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
