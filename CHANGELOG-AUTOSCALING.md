# Autoscaling migration changelog

## 2026-05-25

Added a safe AWS autoscaling migration pack while preserving the current Lightsail Docker Compose deployment.

### Code/config changes

- Added Celery queue separation settings for `light`, `heavy`, and `default` queues.
- Added queue selection logic so image/EXIF/GPS-style jobs can go to `light` and PDF/Office/ZIP/media jobs can go to `heavy`.
- Updated job creation to dispatch Celery tasks with queue names and plan priority hints.
- Updated the production Docker Compose worker command so the existing Lightsail worker consumes all queues by default.
- Added optional environment placeholders for future S3/RDS/ECS migration.

### AWS deployment templates

- Added GitHub Actions template for building images, pushing to ECR, deploying ECS services, and running migrations as a controlled step.
- Added ECS task-definition templates for web, API, beat, light worker, and heavy worker services.
- Added AWS CLI command templates and lifecycle/policy JSON examples.

### Documentation

- Added required autoscaling, migration, security, cost, rollback, pricing/quota, S3, PostgreSQL, ElastiCache, worker-scaling, and ECS deployment docs.

### Safety note

This update does not force the app to use S3/RDS/ElastiCache yet. That must be enabled only after a tested migration because the current production system still stores users/jobs/files in local Docker volumes.
