# Privacy Toolbox AWS autoscaling migration note

Date: 2026-05-25
Region baseline: ap-south-1 / Asia Pacific Mumbai

This document is written for the current Privacy Toolbox project, which is already running on AWS Lightsail with Docker Compose. Do not delete the working Lightsail server until the ECS/RDS/S3 migration has been tested and DNS cutover is complete.


## Network security

- Only ALB is public.
- ECS tasks run in private subnets when possible.
- API/web tasks accept inbound traffic only from ALB security group.
- Workers have no public inbound ports.
- RDS accepts inbound only from ECS security group.
- ElastiCache accepts inbound only from ECS security group.
- S3 bucket blocks public access.
- SSH into production containers is not part of normal deployment.

## Application security

- HTTPS only.
- `AUTH_COOKIE_SECURE=true` in production.
- HttpOnly and SameSite cookies.
- Strict CORS: only your domain(s).
- CSRF protection for state-changing browser requests.
- Security headers: HSTS, X-Content-Type-Options, frame protection/CSP frame ancestors, Referrer-Policy.
- Admin routes protected and not discoverable by public users.
- Rate limiting for uploads/auth/contact/analytics/tool jobs.
- Signed short-lived download URLs.
- No public caching of private downloads.

## File abuse controls

- Extension, MIME, and magic-byte validation.
- Max file size by plan and type.
- Archive/ZIP bomb limits.
- Worker timeouts.
- Memory limits.
- Max tasks per child for workers.
- Daily/monthly quotas enforced by backend.
- Optional malware scanning before processing/downloading.

## Secrets

- Do not commit `.env.production`.
- Store runtime secrets in Secrets Manager or SSM Parameter Store.
- Use GitHub OIDC for deployment.
- Rotate admin password and old GitHub tokens before launch.
- Do not log tokens, cookies, Stripe secrets, S3 presigned URLs, file contents, or private metadata values.

## Monitoring/audit

- CloudWatch log retention set.
- Alarm on 5xx rate, high latency, worker failure rate, queue depth, RDS CPU/storage, Redis CPU/memory, ECS task restarts.
- Audit log admin actions: plan changes, user changes, coupon changes, billing overrides, file/job deletion.
- AWS Budget alerts enabled.

## WAF recommendation

Add AWS WAF after public launch or earlier if abuse begins. Start with managed common rules and rate-based rules for upload/auth endpoints.
