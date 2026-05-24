#!/usr/bin/env bash
set -euo pipefail
AWS_REGION=${AWS_REGION:-ap-south-1}
for repo in privacy-toolbox-web privacy-toolbox-api privacy-toolbox-worker; do
  aws ecr describe-repositories --repository-names "$repo" --region "$AWS_REGION" >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name "$repo" --region "$AWS_REGION"
done
