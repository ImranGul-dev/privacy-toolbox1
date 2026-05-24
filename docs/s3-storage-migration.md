# Privacy Toolbox AWS autoscaling migration note

> Update in this ZIP: `apps/api/app/services/storage_service.py` now includes an S3 storage mode for uploads, jobs, cleaned outputs, and download token rehydration. Enable with `STORAGE_BACKEND=s3` only after creating the private bucket, IAM task role, lifecycle rules, and SSM/ECS environment values.


Date: 2026-05-25
Region baseline: ap-south-1 / Asia Pacific Mumbai

This document is written for the current Privacy Toolbox project, which is already running on AWS Lightsail with Docker Compose. Do not delete the working Lightsail server until the ECS/RDS/S3 migration has been tested and DNS cutover is complete.


## Goal

Move uploads, cleaned outputs, reports, and temporary artifacts from local Docker volumes to private S3 so multiple API and worker tasks can safely share files.

## Bucket design

Recommended bucket pattern:

```text
privacy-toolbox-prod-ACCOUNT_ID
```

Recommended prefixes:

```text
uploads/{yyyy}/{mm}/{dd}/{job_or_file_id}/original-file
outputs/{yyyy}/{mm}/{dd}/{job_id}/cleaned-file
reports/{yyyy}/{mm}/{dd}/{job_id}/report.json
tmp/{yyyy}/{mm}/{dd}/...
```

## Security rules

- Block all public access.
- Enable default encryption with SSE-S3 or SSE-KMS.
- Do not host private downloads through public CloudFront caching.
- Use short-lived presigned URLs for private upload/download.
- Workers should download into local ephemeral storage only for the current task.
- Never log S3 presigned URLs, file contents, or private metadata.

## Lifecycle policy

Start conservative:

| Prefix | Expire after |
|---|---:|
| `tmp/` | 1 day |
| `uploads/` | 1-3 days |
| `outputs/free/` | 1 day |
| `outputs/pro/` | 7 days |
| `outputs/team/` | 30 days |
| `reports/free/` | 1 day |
| `reports/pro/` | 7 days |
| `reports/team/` | 30 days |
| `reports/business/` | 90 days |

Template lifecycle JSON: `infra/aws/s3-lifecycle.json`.

## AWS CLI setup

```bash
export AWS_REGION=ap-south-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export BUCKET=privacy-toolbox-prod-${ACCOUNT_ID}

aws s3api create-bucket \
  --bucket "$BUCKET" \
  --region "$AWS_REGION" \
  --create-bucket-configuration LocationConstraint="$AWS_REGION"

aws s3api put-public-access-block \
  --bucket "$BUCKET" \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

aws s3api put-bucket-encryption \
  --bucket "$BUCKET" \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

aws s3api put-bucket-lifecycle-configuration \
  --bucket "$BUCKET" \
  --lifecycle-configuration file://infra/aws/s3-lifecycle.json
```

## Code migration steps

1. Add PostgreSQL first so file metadata is not trapped in local JSON.
2. Add S3 object keys to job/upload models.
3. Update upload route to save to S3 or issue presigned upload URL.
4. Update worker to download from S3 into `/tmp`, process, upload output/report to S3, and update job record.
5. Update download route to return presigned URL or stream private S3 object.
6. Keep local storage fallback until migration is verified.

## Acceptance tests

- S3 bucket is private.
- Public anonymous object URL fails.
- Presigned upload succeeds.
- Worker can read input and write output.
- Presigned download expires.
- Lifecycle rule exists.
- Deleted/expired job files cannot be downloaded.
