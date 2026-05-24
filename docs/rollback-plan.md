# Privacy Toolbox AWS autoscaling migration note

Date: 2026-05-25
Region baseline: ap-south-1 / Asia Pacific Mumbai

This document is written for the current Privacy Toolbox project, which is already running on AWS Lightsail with Docker Compose. Do not delete the working Lightsail server until the ECS/RDS/S3 migration has been tested and DNS cutover is complete.


## Goal

Never break the currently working Lightsail deployment during autoscaling migration.

## Before any risky work

1. Take Lightsail snapshot.
2. Back up Docker volume.
3. Export `.env.production` securely to a password manager.
4. Lower DNS TTL before cutover.
5. Keep old GitHub Lightsail workflow until ECS is verified.

## Docker volume backup command

```bash
mkdir -p ~/privacy-toolbox-backups

docker run --rm \
  -v compose_privacy-data:/data \
  -v ~/privacy-toolbox-backups:/backup \
  alpine tar czf /backup/privacy-data-$(date +%F-%H%M).tar.gz /data

ls -lh ~/privacy-toolbox-backups
```

## Rollback from code issue on Lightsail

```bash
cd /opt/privacy-toolbox
git log --oneline -5
# choose previous commit in GitHub, revert, push, then let GitHub Actions redeploy
```

Or manually restart last working container if image exists.

## Rollback from ECS cutover

1. Change Route 53 DNS back to Lightsail IP.
2. Wait for DNS TTL.
3. Verify Lightsail app works.
4. Stop ECS services or set desired count to 0 to control cost.
5. Keep RDS/S3 data until you compare what changed during cutover.

## Rollback from database migration

- If no production writes happened: restore RDS snapshot or rerun migration.
- If production writes happened: do not blindly restore old DB; export changed rows first.
- If severe issue: point DNS back to Lightsail and use JSON backup.

## Rollback from S3 storage migration

- Keep local file storage fallback until S3 is fully verified.
- Do not delete local Docker volume after migration.
- Keep S3 lifecycle expiration conservative during initial migration testing.

## Do not do this

- Do not run `docker compose down -v` on production.
- Do not delete Lightsail snapshot immediately after ECS launch.
- Do not delete RDS/S3/ElastiCache without exporting data.
- Do not switch DNS before signup, login, upload, clean, download, Stripe webhook, and admin dashboard tests pass.
