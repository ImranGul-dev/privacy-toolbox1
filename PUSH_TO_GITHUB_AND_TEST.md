# Push the latest code to GitHub and test

## 1. Unzip the new package locally

```bash
unzip privacy-toolbox-production-autoscaling-auth-ready.zip
cd privacy-toolbox-production-autoscaling-auth-ready
```

## 2. Check the changes

```bash
git status
git diff --stat
```

## 3. Commit and push to your current GitHub repo

```bash
git add .
git commit -m "Prepare production auth and autoscaling architecture"
git push origin main
```

Your current GitHub Actions Lightsail workflow should deploy to the existing server. The current Lightsail deployment can still use local storage/JSON/Redis while you prepare AWS ECS.

## 4. Test on current Lightsail after deployment

```bash
cd /opt/privacy-toolbox

docker compose -f infra/compose/docker-compose.prod.yml --env-file .env.production ps

docker compose -f infra/compose/docker-compose.prod.yml --env-file .env.production logs --tail=100 api

docker compose -f infra/compose/docker-compose.prod.yml --env-file .env.production logs --tail=100 worker
```

Open your site and test:

1. Signup with email/password.
2. Check verification code in SMTP email or dev outbox if still in staging.
3. Verify email.
4. Login.
5. Open login/register page and confirm Google/Microsoft/GitHub icons look correct.
6. If OAuth credentials are not configured yet, the buttons may be disabled or redirect with a setup message.

## 5. Production environment validation

After you configure real production values:

```bash
set -a
source .env.production
set +a
python scripts/validate-production-env.py
```

No blocking errors means the environment is safe enough to start production testing. Warnings about local storage, JSON users, or local Redis mean it is still a single-server MVP and not real autoscaling.
