# Privacy Toolbox AWS autoscaling migration note

> Update in this ZIP: `QUOTA_BACKEND=redis` enables Redis-backed shared quota counters for autoscaled API tasks. Use ElastiCache Redis for ECS production; keep local Redis only for Lightsail/MVP.


Date: 2026-05-25
Region baseline: ap-south-1 / Asia Pacific Mumbai

This document is written for the current Privacy Toolbox project, which is already running on AWS Lightsail with Docker Compose. Do not delete the working Lightsail server until the ECS/RDS/S3 migration has been tested and DNS cutover is complete.


## Goal

Replace the local Redis container with ElastiCache Redis/Valkey for production autoscaling.

## Why

ECS API and worker tasks need a shared queue/cache/rate-limit backend. A local Redis container inside one task is not shared and is not safe for horizontal scaling.

## Recommended setup

- Engine: Redis OSS or Valkey supported by ElastiCache.
- Network: private subnets only.
- Public access: no.
- Security group: allow inbound 6379 only from ECS service security group.
- TLS: enable if supported by chosen mode/client setup.
- Auth token: store in Secrets Manager/SSM.
- Backups: optional for broker/cache; not a replacement for job DB.

## Redis URL

```env
REDIS_URL=rediss://:PASSWORD@ELASTICACHE-ENDPOINT:6379/0
```

If TLS is not enabled in the first private VPC setup, use `redis://` internally, but prefer TLS for mature production.

## Celery queue names

```env
CELERY_DEFAULT_QUEUE=default
CELERY_LIGHT_QUEUE=light
CELERY_HEAVY_QUEUE=heavy
CELERY_WORKER_QUEUES=light,heavy,default,celery
```

ECS service commands:

```bash
# light worker
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO -Q light --concurrency=2 --max-tasks-per-child=30

# heavy worker
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO -Q heavy --concurrency=1 --max-tasks-per-child=10
```

## Queue depth monitoring

For simple MVP autoscaling, publish queue-depth metrics from a small scheduled task/script to CloudWatch:

```bash
redis-cli -u "$REDIS_URL" LLEN light
redis-cli -u "$REDIS_URL" LLEN heavy
```

For robust production, publish custom metrics:

- Namespace: `PrivacyToolbox/Queues`
- Metric: `LightQueueDepth`
- Metric: `HeavyQueueDepth`
- Dimensions: `Environment=production`

Scale workers using CloudWatch alarms and Application Auto Scaling.
