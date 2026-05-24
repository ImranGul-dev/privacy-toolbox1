# Privacy Toolbox AWS autoscaling migration note

Date: 2026-05-25
Region baseline: ap-south-1 / Asia Pacific Mumbai

This document is written for the current Privacy Toolbox project, which is already running on AWS Lightsail with Docker Compose. Do not delete the working Lightsail server until the ECS/RDS/S3 migration has been tested and DNS cutover is complete.


## Goal

Move from one Lightsail Docker Compose server to ECS/Fargate without downtime or data loss.

## What changes in code

Required before real ECS cutover:

- API must be stateless.
- Celery jobs must route to `light` and `heavy` queues.
- Jobs/users/usage/admin/contact/subscription state must move from JSON files to PostgreSQL.
- Uploads/outputs/reports must move from local Docker volume to S3.
- Download links must become short-lived S3 presigned URLs or API-controlled streaming.
- Secrets must come from Secrets Manager/SSM, not `.env.production` files on disk.

Already added in this ZIP:

- queue settings in `apps/api/app/core/config.py`
- queue selection in `apps/api/app/core/queueing.py`
- job dispatch to selected queue in `apps/api/app/api/routes/tools.py`
- Docker Compose worker consumes all queues by default, so Lightsail keeps working
- ECS deployment templates and migration docs

## What changes in AWS terminal/CLI

Use the scripts under `scripts/aws/` as copy-and-edit templates. The normal order is:

```bash
export AWS_REGION=ap-south-1
export APP_NAME=privacy-toolbox
export DOMAIN=yourdomain.com
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

Then create:

1. ECR repositories
2. S3 bucket and lifecycle rules
3. VPC/subnets/security groups or use an existing production VPC
4. RDS PostgreSQL
5. ElastiCache Redis
6. ECS cluster
7. ALB target groups/listeners
8. ECS task definitions/services
9. Application Auto Scaling targets/policies
10. CloudWatch alarms and log retention

## What changes in AWS console

- Route 53: create/verify hosted zone and DNS records.
- ACM: request certificate for apex and `www` domain; validate by DNS.
- VPC: confirm public/private subnet layout.
- RDS: verify backups, deletion protection, private subnets only.
- ElastiCache: verify private subnets only.
- ECS: verify services/tasks, logs, scaling events, health checks.
- WAF: optional at launch, recommended after public traffic grows.
- Budgets: create monthly budget alerts before ECS migration.

## What changes in GitHub Actions

Current Lightsail deploy uses SSH and Docker Compose. ECS deploy should use:

- GitHub OIDC, not long-lived AWS keys
- build Docker images
- push to ECR
- render ECS task definitions
- deploy ECS services
- run database migrations as a controlled one-off ECS task

Template: `.github/workflows/deploy-ecs.yml`.

## What changes in environment variables

Add or migrate:

```env
APP_ENV=production
AUTH_COOKIE_SECURE=true
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
FRONTEND_URL=https://yourdomain.com
NEXT_PUBLIC_API_BASE_URL=https://yourdomain.com
NEXT_PUBLIC_SITE_URL=https://yourdomain.com
DATABASE_URL=postgresql+psycopg://...
REDIS_URL=rediss://...
STORAGE_BACKEND=s3
AWS_REGION=ap-south-1
S3_BUCKET=privacy-toolbox-prod-ACCOUNT_ID
CELERY_LIGHT_QUEUE=light
CELERY_HEAVY_QUEUE=heavy
CELERY_DEFAULT_QUEUE=default
```

Store secrets in Secrets Manager or SSM Parameter Store and reference them from ECS task definitions.

## What changes in admin dashboard

Add/verify admin controls for:

- plan quotas: daily scans, daily cleans, monthly files, max file size
- queue priority per plan
- concurrent jobs per plan
- job history retention days
- S3 report/output retention policy by plan
- contact messages stored in DB
- subscription state from Stripe webhooks
- job failure/retry visibility

## Safe cutover checklist

- ECS staging URL passes health checks.
- New user signup works.
- Existing migrated user login works.
- Test file scan/clean/download works.
- Stripe test webhook updates plan.
- Admin dashboard can see users/jobs/contact messages.
- S3 lifecycle policy exists.
- RDS snapshot exists.
- Lightsail snapshot exists.
- DNS TTL lowered before cutover.
- DNS switched to ALB only after tests pass.
