#!/usr/bin/env bash
set -euo pipefail
AWS_REGION=${AWS_REGION:-ap-south-1}
CLUSTER=${ECS_CLUSTER:-privacy-toolbox-prod}

# Web and API target tracking examples. Update service names and target values for production.
for svc in privacy-toolbox-web privacy-toolbox-api; do
  aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/${CLUSTER}/${svc} \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 1 \
    --max-capacity 4 \
    --region "$AWS_REGION"

  aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --resource-id service/${CLUSTER}/${svc} \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-name ${svc}-cpu-60 \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration '{"TargetValue":60.0,"PredefinedMetricSpecification":{"PredefinedMetricType":"ECSServiceAverageCPUUtilization"},"ScaleOutCooldown":120,"ScaleInCooldown":300}' \
    --region "$AWS_REGION"
done

# Worker queue-depth scaling needs CloudWatch custom metrics or alarms.
# Publish LightQueueDepth and HeavyQueueDepth first, then attach step scaling policies.
