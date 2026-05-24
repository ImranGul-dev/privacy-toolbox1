# AWS low-cost production deployment

This project is now tuned for a single-server AWS MVP deployment where cost matters more than horizontal scaling.

## Recommended starting architecture

Use one AWS Lightsail or EC2 Ubuntu instance with Docker Compose:

- Caddy reverse proxy with automatic HTTPS
- Next.js web container
- FastAPI API container
- Celery worker container
- Celery beat cleanup container
- Redis container for queue, result backend, and rate limiting
- One persistent Docker volume for temporary uploads, cleaned outputs, users, jobs, contact messages, analytics, and admin settings

This avoids the early cost of an Application Load Balancer, NAT Gateway, RDS, ElastiCache, ECS/Fargate, and S3 request/storage complexity.

## Minimum server size

For testing, 2GB RAM can work with small files.
For public MVP, use at least:

- 4GB RAM
- 2 vCPU
- 80GB disk or more

The worker default is intentionally `WORKER_CONCURRENCY=1` because PDF, Office, media, ExifTool, Ghostscript, FFmpeg, and LibreOffice jobs can use a lot of memory.

## Production deploy commands

```bash
cp .env.production.example .env.production
# edit .env.production: SITE_DOMAIN, SECRET_KEY, admin password, SMTP, Stripe values when ready

docker compose --env-file .env.production -f infra/compose/docker-compose.prod.yml up -d --build
```

Health checks:

```bash
curl https://your-domain.com/health
curl https://your-domain.com/ready
```

Logs:

```bash
docker compose --env-file .env.production -f infra/compose/docker-compose.prod.yml logs -f --tail=100
```

## Cost-control defaults

The included `.env.production.example` starts with:

- `MAX_UPLOAD_MB=512`
- `API_WORKERS=1`
- `WORKER_CONCURRENCY=1`
- Redis memory capped at 256MB
- Docker log rotation enabled
- No public ports except 80/443
- No PostgreSQL container because the current MVP still uses JSON/file storage

Raise these only after you confirm memory, disk, and processing time under real usage.

## Stripe billing activation

Billing routes are implemented but safely disabled until configuration exists.

To activate:

1. Create Stripe products/prices for Pro, Team, and optionally Business.
2. Add these values to `.env.production`:

```env
STRIPE_SECRET_KEY=sk_live_or_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_or_test_...
STRIPE_PRICE_ID_PRO_MONTHLY=price_...
STRIPE_PRICE_ID_PRO_YEARLY=price_...
STRIPE_PRICE_ID_TEAM_MONTHLY=price_...
STRIPE_PRICE_ID_TEAM_YEARLY=price_...
```

3. In Stripe Dashboard, create a webhook endpoint:

```text
https://your-domain.com/api/billing/webhook
```

4. Subscribe to these events:

```text
checkout.session.completed
customer.subscription.created
customer.subscription.updated
customer.subscription.deleted
```

After webhook confirmation, the backend updates the user plan stored in the local user store. Later, when you move to PostgreSQL, the same service boundary can be reused.

## When to move beyond this setup

Move to S3 + PostgreSQL + separate workers when you have one of these signs:

- More than 1,000 daily active users
- Many files above 500MB
- Worker queue regularly backs up
- You need multiple servers
- You need durable user/job/billing records beyond one VPS volume

Recommended next phase:

- S3 for uploads/outputs
- PostgreSQL for users/jobs/usage/billing/contact messages
- Managed Redis or separate Redis instance
- Separate light/heavy queues
- Worker autoscaling
