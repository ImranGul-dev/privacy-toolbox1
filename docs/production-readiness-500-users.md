# Production readiness for 500 concurrent users

This project can be made production ready, but code alone does not guarantee 500 simultaneous active users. Real capacity depends on AWS resources, file sizes, worker concurrency, S3/RDS/Redis migration, queue depth, and plan limits.

## What is ready in this ZIP

- Email/password signup with verification-code flow.
- Google, Microsoft, and GitHub OAuth routes with environment-based provider credentials.
- Correct frontend social login icons and provider configuration detection.
- Production startup checks for secure cookies, strong secret key, CORS, SMTP, and optionally all OAuth providers.
- Celery queue separation for light and heavy file-processing jobs.
- ECS/Fargate, ECR, S3, RDS, ElastiCache, and autoscaling documentation/templates.

## What must be configured before it is truly production ready

1. Real domain with HTTPS.
2. SMTP provider such as Amazon SES, Mailgun, SendGrid, or another reliable provider.
3. Google OAuth app with callback URL: `https://your-domain.com/api/auth/oauth/google/callback`.
4. Microsoft Entra app with callback URL: `https://your-domain.com/api/auth/oauth/microsoft/callback`.
5. GitHub OAuth app with callback URL: `https://your-domain.com/api/auth/oauth/github/callback`.
6. Stripe or Lemon Squeezy subscription integration and webhook secrets.
7. PostgreSQL migration before multi-server/multi-task production.
8. S3 storage migration before multi-server/multi-worker production.
9. ElastiCache Redis or another managed queue/cache before ECS production.
10. CloudWatch alarms for API errors, worker failures, queue depth, CPU, memory, and billing.

## 500-user reality check

- 500 users browsing pages is mostly frontend/API traffic and can be handled with enough ECS web/API tasks behind an ALB.
- 500 users uploading and processing files at the same time is a heavy workload and requires S3, RDS, ElastiCache, separate light/heavy workers, strict quotas, low heavy-worker concurrency, and autoscaling policies.
- Heavy PDF/Office/video jobs must be throttled by plan and queue priority. Do not allow unlimited heavy jobs.

## Recommended AWS target for 500 active users

- ALB public entry point.
- ECS Fargate or ECS on EC2 for web/API tasks.
- Separate ECS worker services: `worker-light` and `worker-heavy`.
- S3 private buckets for uploads/outputs/reports with lifecycle rules.
- RDS PostgreSQL for users, jobs, usage, subscriptions, contacts, and admin settings.
- ElastiCache Redis for Celery broker/result backend, rate limits, and queue metrics.
- Secrets Manager or SSM Parameter Store for secrets.
- CloudWatch dashboards and alarms.

## Minimum production deployment gates

Run before public launch:

```bash
set -a
source .env.production
set +a
python scripts/validate-production-env.py
```

The script must show no blocking errors. Warnings about local storage/database/Redis mean the deployment is still MVP/single-server, not true autoscaling.
