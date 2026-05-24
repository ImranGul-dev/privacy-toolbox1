# Autoscaling implementation summary

## What stage the project is in

Current project stage: **Stage 1-3 MVP on Lightsail**. The app is production-hardened for a single Docker Compose server, but not yet real autoscaling because files, users, jobs, and Redis are still local to one server.

## What this ZIP completes

This ZIP completes a **safe autoscaling-readiness package**:

- Celery jobs now route to `light` or `heavy` queues.
- The current Lightsail worker listens to all queues, so existing deployment remains safe.
- ECS task definition templates are included for web, API, light worker, heavy worker, and beat.
- GitHub Actions ECS/ECR deployment template is included.
- S3 lifecycle, IAM policy, PostgreSQL starter schema, and migration helper are included.
- Required AWS autoscaling documentation is included under `docs/`.

## What this ZIP does not force yet

This ZIP does **not** force S3/RDS/ElastiCache runtime usage yet. That would be unsafe without a staged migration and database verification because the current production system still stores important data in local Docker volumes and JSON files.

## Safest next stage

1. Complete domain/HTTPS/SMTP/backups/admin-password security.
2. Enable Stripe test mode and plan/quota enforcement.
3. Test the new light/heavy queue behavior on Lightsail.
4. Add PostgreSQL migration on staging.
5. Add S3 storage migration on staging.
6. Deploy ECS/Fargate staging behind a subdomain.
7. Cut over DNS only after acceptance tests pass.
