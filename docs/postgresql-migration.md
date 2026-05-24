# Privacy Toolbox AWS autoscaling migration note

> Update in this ZIP: `USER_STORAGE_BACKEND=postgres` enables PostgreSQL-backed user storage. Run `infra/db/postgresql_schema.sql` and `scripts/db/migrate_users_json_to_postgres.py` before enabling it in production.


Date: 2026-05-25
Region baseline: ap-south-1 / Asia Pacific Mumbai

This document is written for the current Privacy Toolbox project, which is already running on AWS Lightsail with Docker Compose. Do not delete the working Lightsail server until the ECS/RDS/S3 migration has been tested and DNS cutover is complete.


## Goal

Move users, jobs, usage, plans, subscriptions, contacts, admin settings, coupons, affiliates, and analytics from local JSON files into PostgreSQL/RDS.

## Why PostgreSQL must come before ECS autoscaling

Multiple ECS API tasks cannot safely share local JSON files. Without PostgreSQL, users, jobs, quotas, payments, and admin settings may differ between containers.

## Recommended tables

Minimum production tables:

- users
- email_verifications
- sessions or auth_tokens denylist if needed
- jobs
- uploads
- usage_daily
- usage_monthly
- plans
- subscriptions
- payments/events
- contact_messages
- admin_settings
- coupons
- affiliates
- audit_logs
- api_keys later, hashed only

## Required indexes

```sql
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs (user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs (created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON jobs (job_id);
CREATE INDEX IF NOT EXISTS idx_users_plan ON users (plan);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer ON subscriptions (stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_subscription ON subscriptions (stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_contact_created_at ON contact_messages (created_at);
```

## RDS setup recommendations

- Engine: PostgreSQL current supported major version.
- Instance: start with `db.t4g.micro` or `db.t4g.small` for MVP, depending on budget.
- Storage: gp3, 20GB initial, autoscaling enabled.
- Backups: 7 days minimum; 14-30 days for paid production.
- Public access: false.
- Security group: allow only ECS API/worker security group.
- Deletion protection: true for production.
- Multi-AZ: optional at MVP, recommended when revenue supports uptime needs.

## Migration strategy

1. Take Lightsail snapshot.
2. Back up Docker volume.
3. Add SQLAlchemy/SQLModel models and Alembic migrations.
4. Add repository layer so services can read/write PostgreSQL while local JSON remains fallback.
5. Run migration on a staging copy first.
6. Run a one-time migration script from current JSON files.
7. Compare record counts and sample users/jobs.
8. Switch production services to PostgreSQL.
9. Keep JSON backup read-only for rollback.

## One-time migration command pattern

```bash
python -m app.db.migrate_json_to_postgres \
  --source /data/privacy-toolbox \
  --database-url "$DATABASE_URL" \
  --dry-run

python -m app.db.migrate_json_to_postgres \
  --source /data/privacy-toolbox \
  --database-url "$DATABASE_URL" \
  --apply
```

## Rollback

- Stop writes to ECS.
- Point DNS back to Lightsail.
- Restore old `.env.production`.
- Use JSON backup if PostgreSQL migration corrupted data.
- Do not delete RDS until rollback period has passed.
