# Privacy Toolbox AWS autoscaling migration note

Date: 2026-05-25
Region baseline: ap-south-1 / Asia Pacific Mumbai

This document is written for the current Privacy Toolbox project, which is already running on AWS Lightsail with Docker Compose. Do not delete the working Lightsail server until the ECS/RDS/S3 migration has been tested and DNS cutover is complete.


## Goal

Scale Celery workers separately from web/API and separate light jobs from heavy jobs.

## Code status in this ZIP

Implemented safely:

- `apps/api/app/core/queueing.py` decides `light` vs `heavy`.
- `apps/api/app/api/routes/tools.py` dispatches with `apply_async(queue=...)`.
- `apps/api/app/workers/celery_app.py` declares default/light/heavy queues.
- Docker Compose worker listens to all queues by default, so Lightsail does not break.

## Queue assignment

Light queue:

- image metadata scan/clean
- EXIF removal
- GPS removal
- small verification jobs
- C2PA detection if small and quick

Heavy queue:

- PDF scanning/cleaning
- Office DOCX/XLSX/PPTX cleaning
- ZIP scanning/cleaning
- audio/video metadata removal
- advanced PDF hidden data cleanup

## ECS worker service design

### worker-light

- command: `celery ... -Q light --concurrency=2`
- CPU/memory: start 0.5 vCPU / 1GB
- min tasks: 0 or 1
- max tasks: 10
- scale out: `LightQueueDepth > 10`
- scale in: `LightQueueDepth == 0` for 10 minutes

### worker-heavy

- command: `celery ... -Q heavy --concurrency=1`
- CPU/memory: start 1 vCPU / 2GB, increase to 4GB for video/large PDFs
- min tasks: 0 or 1
- max tasks: 3 early, 5 later
- scale out: `HeavyQueueDepth > 2`
- scale in: `HeavyQueueDepth == 0` for 15-30 minutes

## Job timeout strategy

Suggested defaults:

```env
WORKER_SOFT_TIME_LIMIT_SECONDS=1080
WORKER_HARD_TIME_LIMIT_SECONDS=1200
```

For heavy video tools, use separate larger workers and possibly longer timeouts. Do not increase timeouts without increasing task memory and abuse controls.

## Dead-letter/retry strategy

Redis broker has limited DLQ behavior compared with SQS. For production:

- keep retry count low for file-processing jobs
- record failures in PostgreSQL jobs table
- refund quota only when processing fails before output
- alert when failure rate spikes
- for a stronger DLQ, move heavy-job orchestration to SQS + worker consumer or AWS Batch later

## Per-plan priority

The code now passes a Celery priority hint based on plan priority. Redis priority is approximate, so do not rely on it as the only SLA mechanism. Better production plan priority:

- separate queues by plan tier later: `heavy_pro`, `heavy_team`, `heavy_business`
- reserve at least one worker for paid queues once revenue supports it
- keep free jobs low priority and low file size

## Worker acceptance tests

1. Upload an image and run scan: job should include `queue: light`.
2. Upload a PDF and run clean: job should include `queue: heavy`.
3. On Lightsail, the single worker should process both because it listens to `light,heavy,default,celery`.
4. On ECS, light worker should only process light jobs and heavy worker should only process heavy jobs.
