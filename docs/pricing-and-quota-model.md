# Privacy Toolbox AWS autoscaling migration note

Date: 2026-05-25
Region baseline: ap-south-1 / Asia Pacific Mumbai

This document is written for the current Privacy Toolbox project, which is already running on AWS Lightsail with Docker Compose. Do not delete the working Lightsail server until the ECS/RDS/S3 migration has been tested and DNS cutover is complete.


## Goal

Keep pricing profitable by connecting every plan to backend cost, worker capacity, file size, and queue priority.

## Important rule

Do not sell unlimited heavy processing. File processing costs CPU, memory, storage, bandwidth, logs, support time, and failed/retry jobs.

## Recommended public plan model

| Plan | Suggested price | Monthly processed files | Daily scans | Daily cleans | Concurrent jobs | Queue priority | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| Free | $0 | 30-60 | 5 | 3 | 1 | low | trust builder, strict file sizes, short retention |
| Pro | $9-$15/mo | 100-300 | 100 | 100 | 2 | medium | individual creators/freelancers |
| Team | $29-$49/mo | 500-1500 | 500 | 500 | 4 | high | small teams/agencies |
| Business | $99+/mo | 2000+ | 2500 | 2500 | 8+ | highest | custom limits, priority support |

## Recommended max file size by type

| Type | Free | Pro | Team | Business |
|---|---:|---:|---:|---:|
| Images | 25MB | 100MB | 200MB | 300MB |
| PDF | 50MB | 200MB | 500MB | 512MB+ |
| Office | 50MB | 200MB | 500MB | 512MB+ |
| ZIP | 50MB | 250MB | 512MB | 512MB+ |
| Audio | 50MB | 250MB | 512MB | custom |
| Video | 100MB | 512MB | 512MB | custom/high-price only |

## Backend enforcement

Plan limits must be enforced in backend routes, not only frontend text.

Current code already enforces:

- plan file-size limits in `apps/api/app/core/plans.py`
- daily/monthly usage in `apps/api/app/services/quota_service.py`
- tool-level plan restrictions in `apps/api/app/api/routes/tools.py`
- queue priority hint from plan priority in `apps/api/app/core/queueing.py`

Still needed for full autoscaling:

- move usage/quota counters from JSON to PostgreSQL or Redis+PostgreSQL
- enforce concurrent jobs per plan in the jobs table
- store plan history and Stripe subscription state in PostgreSQL
- show quota usage in admin and user dashboard

## Overage/add-on strategy

Do not allow hidden unlimited overage at first. Use prepaid add-ons:

- Extra 100 files: $5-$10
- Extra 1000 files: $25-$50
- Large file pack/video processing: custom or Business only
- API access: Business only until abuse monitoring is mature

## Profit check formula

```text
minimum plan price >= (expected compute + storage + bandwidth + payment fees + support + abuse buffer) x 2
```

For heavy users, the multiplier should be higher than 2x because failures, refunds, and support time are real costs.
