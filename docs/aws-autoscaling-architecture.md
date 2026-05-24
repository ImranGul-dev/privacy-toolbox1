# Privacy Toolbox AWS autoscaling migration note

> Update in this ZIP: the application now has code-level switches for S3 file/job storage, PostgreSQL user storage, and Redis shared quota counters. ECS production should use `STORAGE_BACKEND=s3`, `USER_STORAGE_BACKEND=postgres`, and `QUOTA_BACKEND=redis`.


Date: 2026-05-25
Region baseline: ap-south-1 / Asia Pacific Mumbai

This document is written for the current Privacy Toolbox project, which is already running on AWS Lightsail with Docker Compose. Do not delete the working Lightsail server until the ECS/RDS/S3 migration has been tested and DNS cutover is complete.


## Current stage

The uploaded project is currently between Stage 1 and Stage 3:

- compute: one Lightsail VPS
- runtime: Docker Compose
- public entry: Caddy
- frontend: Next.js container
- API: FastAPI container
- background processing: one Celery worker container
- queue/cache: local Redis container
- storage: local Docker volume
- users/jobs/usage/contact/admin data: local JSON files in the Docker volume
- deployment: GitHub Actions SSH/rsync to Lightsail

This is good for MVP, but it is not real autoscaling. Lightsail cannot scale horizontally like ECS/EC2 Auto Scaling, and local files/JSON prevent safe multi-server operation.

## Architecture option comparison

| Option | Fit for Privacy Toolbox | Pros | Cons | Recommendation |
|---|---:|---|---|---|
| A. ECS Fargate + ALB | High | managed containers, no EC2 patching, separate web/API/workers, service autoscaling, clean deployments | higher fixed cost than VPS; needs ALB/RDS/ElastiCache/S3 | Best practical target for production autoscaling |
| B. ECS on EC2 Auto Scaling Group | Medium/High | cheaper at steady load, supports workers well, more control over large jobs | EC2 patching/capacity management, cluster tuning | Best later if heavy workload cost becomes high |
| C. EC2 Auto Scaling Group + Docker Compose/systemd | Medium | cheaper and familiar | harder rolling deployments, weaker service-level autoscaling, more custom scripts | Not first choice |
| D. AWS Batch for heavy jobs | Medium | very good for long/heavy file processing, job queues, compute environments | more complex product flow, slower cold starts, separate job orchestration | Add later for very heavy/video/large PDFs |
| E. Lambda only | Low/Partial | useful for small metadata checks or webhooks | timeout, memory/tmp limits, package/binary constraints, large file limits | Use only for small utilities or async helpers |

## Chosen target architecture

Use **ECS Fargate with Application Load Balancer** as the main Stage 4 autoscaling architecture.

Components:

- Route 53: DNS hosted zone for the domain.
- ACM: public TLS certificate in the same region as the ALB.
- ALB: public HTTPS entry point. Only the ALB security group is public.
- ECS cluster: Fargate launch type.
- ECS web service: Next.js frontend tasks.
- ECS API service: FastAPI tasks; stateless; no local persistent dependency.
- ECS worker-light service: Celery worker with `-Q light` for image/EXIF/GPS/small scans.
- ECS worker-heavy service: Celery worker with `-Q heavy` for PDF/Office/ZIP/media/advanced cleanup.
- ECS beat service: one task only for cleanup/schedules.
- S3: private bucket for uploads, cleaned files, reports, temporary files.
- RDS PostgreSQL: users, jobs, usage, plans, subscriptions, contacts, admin data.
- ElastiCache Redis: Celery broker/result backend, rate limits, cache, queue metrics.
- CloudWatch: logs, metrics, alarms, dashboards.
- Secrets Manager or SSM Parameter Store: runtime secrets.
- IAM roles: separate execution role and task role, least privilege.
- GitHub Actions: OIDC role -> ECR push -> ECS service deploy.

## Traffic and job flow

1. Browser opens `https://yourdomain.com`.
2. Route 53 sends traffic to ALB.
3. ALB routes `/api/*` to API target group and all other traffic to web target group.
4. API validates auth/quota/file type and creates a job record in PostgreSQL.
5. Uploads should use S3 presigned POST/PUT or API streaming to S3. Do not require local Docker volume storage.
6. API dispatches Celery job to `light` or `heavy` queue.
7. Worker downloads the file from S3 into task-local ephemeral storage, processes it, uploads output/report to S3, updates PostgreSQL.
8. User gets job status and a short-lived private presigned download URL.

## Scaling design

### Web service

- min tasks: 1 for low cost, 2 for high availability
- max tasks: 4 for MVP growth
- scale out: CPU > 60%, memory > 70%, or ALB request count per target > 500-1000/minute
- scale in: cooldown 5-10 minutes
- health check: `/` or `/ready`

### API service

- min tasks: 1 for low cost, 2 for high availability
- max tasks: 6 for early paid growth
- scale out: CPU > 55%, memory > 70%, ALB request count per target, p95 latency, or 5xx rate
- API rule: stateless only. No sessions or file processing should depend on local disk.
- health check: `/api/health`

### Light worker service

- min tasks: 0 or 1. Use 0 only if cold starts are acceptable.
- max tasks: 10 for early growth.
- concurrency: 2-4 depending on memory.
- scale metric: pending jobs in Redis/Celery light queue.
- scale out example: queue depth > 10 for 2 datapoints.
- scale in: queue depth = 0 for 10-15 minutes.

### Heavy worker service

- min tasks: 0 or 1.
- max tasks: 3 for MVP/growth.
- concurrency: 1. Keep heavy tasks low to avoid memory crashes.
- task size: start with 1 vCPU / 2-4GB RAM; increase for video/large PDFs.
- scale metric: pending jobs in Redis/Celery heavy queue.
- scale out example: queue depth > 2 for 2 datapoints.
- scale in: queue depth = 0 for 15-30 minutes.

## Why not keep Lightsail for autoscaling?

Lightsail is excellent for the current MVP cost, but it does not provide real service autoscaling for separate web/API/workers. The current Docker volume and local JSON storage also mean that adding more servers would cause inconsistent users, jobs, files, quotas, and downloads.

## Minimum migration order

1. Keep Lightsail live.
2. Add domain/HTTPS/security and Stripe first.
3. Split Celery queues in code and verify single-worker compatibility.
4. Add PostgreSQL models and migrate users/jobs/usage/contact/admin data.
5. Add S3 private object storage and lifecycle cleanup.
6. Add ElastiCache Redis and update Redis URLs.
7. Create ECR repositories and ECS services.
8. Test ECS behind a staging subdomain.
9. Switch DNS only after acceptance tests pass.
10. Keep Lightsail snapshot for rollback.
