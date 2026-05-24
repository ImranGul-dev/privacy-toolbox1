# Privacy Toolbox AWS autoscaling migration note

Date: 2026-05-25
Region baseline: ap-south-1 / Asia Pacific Mumbai

This document is written for the current Privacy Toolbox project, which is already running on AWS Lightsail with Docker Compose. Do not delete the working Lightsail server until the ECS/RDS/S3 migration has been tested and DNS cutover is complete.


## Goal

Replace SSH deploys with a scalable CI/CD pipeline:

GitHub Actions -> OIDC role -> build Docker images -> push to Amazon ECR -> deploy ECS services.

## Files included

- `.github/workflows/deploy-ecs.yml`
- `infra/ecs/task-definitions/web.json`
- `infra/ecs/task-definitions/api.json`
- `infra/ecs/task-definitions/worker-light.json`
- `infra/ecs/task-definitions/worker-heavy.json`
- `infra/ecs/task-definitions/beat.json`

These are templates. Fill AWS account ID, ECR image URIs, subnet/security group/service names, Secrets Manager ARNs, and log groups before production.

## Required GitHub variables/secrets

Prefer GitHub repository variables for non-secrets:

```text
AWS_REGION=ap-south-1
ECS_CLUSTER=privacy-toolbox-prod
ECS_WEB_SERVICE=privacy-toolbox-web
ECS_API_SERVICE=privacy-toolbox-api
ECS_WORKER_LIGHT_SERVICE=privacy-toolbox-worker-light
ECS_WORKER_HEAVY_SERVICE=privacy-toolbox-worker-heavy
ECS_BEAT_SERVICE=privacy-toolbox-beat
```

Secrets:

```text
AWS_ROLE_TO_ASSUME=arn:aws:iam::ACCOUNT_ID:role/github-actions-privacy-toolbox-deploy
```

Runtime secrets should not be GitHub secrets if ECS can fetch them directly. Put them in Secrets Manager or SSM Parameter Store and reference from task definitions.

## ECR repositories

```bash
export AWS_REGION=ap-south-1
aws ecr create-repository --repository-name privacy-toolbox-web --region "$AWS_REGION"
aws ecr create-repository --repository-name privacy-toolbox-api --region "$AWS_REGION"
aws ecr create-repository --repository-name privacy-toolbox-worker --region "$AWS_REGION"
```

## Deployment workflow

1. Build web image.
2. Build API image.
3. Build worker image.
4. Push all images to ECR with git SHA tag.
5. Render ECS task definitions.
6. Deploy API service.
7. Deploy web service.
8. Deploy light worker service.
9. Deploy heavy worker service.
10. Deploy beat service.
11. Run migrations as a one-off ECS task before service deployment if DB schema changed.

## Migration safety

Do not run destructive migrations automatically. For early production, keep migration as manual workflow input:

```yaml
workflow_dispatch:
  inputs:
    run_migrations:
      type: boolean
      default: false
```

## Rollback

- ECS keeps old task definition revisions.
- Redeploy previous image tag/task definition.
- If database migration is not backward compatible, restore RDS snapshot and point DNS back to Lightsail.
