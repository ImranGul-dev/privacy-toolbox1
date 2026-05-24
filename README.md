# Privacy Toolbox for Modern Files

Privacy Toolbox is a privacy-focused file utility site for scanning, cleaning, and verifying hidden file data before sharing.

Core promise: **Scan, clean, and verify hidden file data before you share.**

## What is included

- Next.js App Router frontend with responsive SaaS UI
- FastAPI API with upload, job, download, auth, admin, billing, analytics, and tool routes
- Celery worker and Redis queue
- Caddy reverse proxy production setup for low-cost AWS deployment
- Stripe Checkout and webhook integration, disabled safely until keys/price IDs are configured
- Plugin-based tool registry for images, PDFs, Office files, media, ZIP archives, C2PA detection, and verification
- File type allowlist and magic-byte validation
- ZIP/OOXML safety checks
- Short-lived signed download links
- Upload/job ownership protection for guests and logged-in users
- Production secret validation
- Docker log rotation and low-cost resource limits

## Run locally

```bash
cp .env.example .env
docker compose -f infra/compose/docker-compose.dev.yml up --build
```

Open:

- Frontend: http://localhost:3000
- API health: http://localhost:8000/health

## AWS low-cost production deployment

Recommended MVP setup:

```text
AWS Lightsail or EC2 Ubuntu VPS
Docker Compose
Caddy HTTPS reverse proxy
Next.js web
FastAPI API
Celery worker
Celery beat cleanup
Redis
Persistent Docker volumes
```

Deploy:

```bash
cp .env.production.example .env.production
# Edit .env.production first.
docker compose --env-file .env.production -f infra/compose/docker-compose.prod.yml up -d --build
```

Only ports 80 and 443 should be open publicly. Do not expose 3000, 8000, or 6379 to the internet.

See `docs/aws-low-cost-production.md` for the full AWS guide.

## Stripe billing

Billing is ready but disabled until you add Stripe values.

Required values:

```env
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
STRIPE_PRICE_ID_PRO_MONTHLY=
STRIPE_PRICE_ID_PRO_YEARLY=
STRIPE_PRICE_ID_TEAM_MONTHLY=
STRIPE_PRICE_ID_TEAM_YEARLY=
```

Webhook endpoint:

```text
https://your-domain.com/api/billing/webhook
```

Events:

```text
checkout.session.completed
customer.subscription.created
customer.subscription.updated
customer.subscription.deleted
```

## Important production limits

The default production profile is intentionally cost-safe:

- `MAX_UPLOAD_MB=512`
- `API_WORKERS=1`
- `WORKER_CONCURRENCY=1`
- Worker memory limit 1536MB
- Redis memory limit 256MB
- File/job cleanup after 60 minutes

Increase limits only after upgrading server resources or moving uploads/outputs to object storage.

## Tool behavior

### PDF cleaner

The scanner separates real privacy findings from low-risk technical metadata. Normal regenerated PDF `Producer` or `Creator` values created by pikepdf/Ghostscript are shown as technical metadata and should not trigger scary hidden-data warnings by themselves.

### Image cleaner

ExifTool is used for scan/clean where available. The scanner ignores normal file-system fields and image dimensions so they do not become false privacy warnings.

### Office cleaner

Supports DOCX, XLSX, and PPTX. Legacy DOC/XLS/PPT are rejected in MVP. The cleaner removes `docProps` metadata and common comments/people parts where practical.

### Media and ZIP tools

FFmpeg/ExifTool are used for audio/video metadata workflows where available. ZIP cleaning removes unsafe paths and common system/secret artifacts, but metadata-bearing files inside ZIPs should be scanned separately.

## Honest limitations

Do not market this product as:

- 100% anonymous
- guaranteed to remove every possible hidden data structure
- browser-only for all formats

Use safer copy:

- “No removable metadata found by our current scanners.”
- “Temporary files are automatically deleted.”
- “Verification included.”
- “Some technical metadata may remain for compatibility.”

## Future scaling path

When traffic grows, move to:

- S3-compatible object storage for uploads/outputs
- PostgreSQL for users, jobs, quotas, billing, contacts, and analytics
- Separate light/heavy Celery queues
- Managed Redis or dedicated Redis server
- Worker autoscaling
- CloudFront for static assets only
