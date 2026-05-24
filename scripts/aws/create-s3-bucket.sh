#!/usr/bin/env bash
set -euo pipefail
AWS_REGION=${AWS_REGION:-ap-south-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET=${S3_BUCKET:-privacy-toolbox-prod-${ACCOUNT_ID}}
aws s3api create-bucket --bucket "$BUCKET" --region "$AWS_REGION" --create-bucket-configuration LocationConstraint="$AWS_REGION" || true
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-bucket-lifecycle-configuration --bucket "$BUCKET" --lifecycle-configuration file://infra/aws/s3-lifecycle.json
echo "Created/updated private S3 bucket: $BUCKET"
