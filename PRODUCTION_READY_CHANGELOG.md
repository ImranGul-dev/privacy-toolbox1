# Production-ready package changelog

This ZIP upgrades the project from autoscaling documentation only to a stronger production-ready code package.

## Added / improved

- Correct inline SVG logos for Google, Microsoft, and GitHub login buttons.
- Frontend provider-status detection from `/api/public/config` so OAuth buttons can reflect real provider configuration.
- Backend OAuth callback base URL support through `API_PUBLIC_URL` for ALB/ECS and single-domain deployments.
- Production startup checks for SMTP and optional required OAuth providers.
- Public auth configuration status without exposing secrets.
- S3-backed upload/job/output support for ECS workers that do not share local disk.
- PostgreSQL-backed user storage option through `USER_STORAGE_BACKEND=postgres`.
- Redis-backed quota counters through `QUOTA_BACKEND=redis`.
- ECS task definitions updated with S3/Postgres/Redis/OAuth/SMTP production environment and SSM placeholders.
- `.env.ecs.production.example` for the autoscaling target architecture.
- `scripts/validate-production-env.py` to catch unsafe/missing production settings before deployment.
- `docs/production-readiness-500-users.md` with the real 500-user deployment gates.

## Still requires AWS setup before it is live-autoscaling

The code is now prepared for real autoscaling, but AWS resources must still be created and wired:

- Route 53/domain + ACM certificate
- ALB
- ECS cluster and services
- ECR repositories
- S3 bucket + lifecycle rules
- RDS PostgreSQL
- ElastiCache Redis
- SSM/Secrets Manager parameters
- CloudWatch alarms
- OAuth apps and SMTP credentials

Do not call the deployment fully autoscaled until those resources are configured and tested.
