# Privacy Toolbox AWS autoscaling migration note

Date: 2026-05-25
Region baseline: ap-south-1 / Asia Pacific Mumbai

This document is written for the current Privacy Toolbox project, which is already running on AWS Lightsail with Docker Compose. Do not delete the working Lightsail server until the ECS/RDS/S3 migration has been tested and DNS cutover is complete.


## Cost model warning

AWS pricing changes by region, usage, architecture, data transfer, public IPv4, log volume, and support plan. Treat this as a planning estimate for ap-south-1. Before purchase, verify with the AWS Pricing Calculator.

## Main cost facts to remember

- Fargate compute charges are based on vCPU, memory, duration, and extra ephemeral storage.
- ALB has a fixed hourly charge plus LCU usage.
- RDS and ElastiCache usually run continuously unless you stop/delete them.
- NAT Gateway can become a surprise fixed cost plus per-GB processing cost.
- CloudWatch logs can grow if retention is not set.
- S3 is cheap per GB, but data transfer out and many requests can add cost.

## Stages

| Stage | Architecture | Estimated monthly cost | Notes |
|---|---|---:|---|
| Current Lightsail MVP | 2GB Lightsail + Docker Compose + local Redis/storage | about $12-$20 | Lowest cost, not autoscaling |
| Stage 2 stronger single server | 4GB Lightsail/EC2 + snapshots + domain/email | about $24-$45 | Better MVP, still not autoscaling |
| Stage 3 semi-scalable | VPS/EC2 + S3 + RDS PostgreSQL + local/managed Redis | about $45-$100 | safer data/storage, limited compute scaling |
| Stage 4 proper ECS/Fargate | ALB + ECS web/API/workers + S3 + RDS + ElastiCache + logs | about $130-$300+ | real service scaling, higher baseline cost |
| Stage 5 high-scale production | multi-AZ RDS, more ECS tasks/workers, WAF, NAT, CloudFront, monitoring | $300-$1000+ | depends heavily on jobs and traffic |

## Cheapest production-safe autoscaling path

For your current business stage, the cheapest practical path is:

1. Keep Lightsail for MVP.
2. Add domain/HTTPS/SMTP/backups/Stripe.
3. Split queues and enforce quotas.
4. Add S3 and PostgreSQL only when users and uploads matter.
5. Move to ECS/Fargate only when paid traffic justifies the baseline cost.

## Cost controls for ECS/Fargate

- Use 1 minimum task for web/API at first if uptime tolerance allows.
- Use 0 minimum workers if cold starts are acceptable.
- Use Fargate Spot only for interrupt-tolerant workers, not API.
- Keep heavy worker max tasks low.
- Set CloudWatch log retention to 7-14 days.
- Avoid NAT Gateway where possible by using VPC endpoints for ECR/S3/CloudWatch if cost-effective.
- Keep S3 lifecycle expiration short for free users.
- Use budget alerts at $25, $50, $100, $200.

## Example Fargate baseline estimate

Low-cost Stage 4 start:

- web: 1 task, 0.25 vCPU, 0.5GB
- API: 1 task, 0.5 vCPU, 1GB
- worker-light: min 0-1 task, 0.5 vCPU, 1GB
- worker-heavy: min 0-1 task, 1 vCPU, 2GB
- beat: 1 task, 0.25 vCPU, 0.5GB
- ALB: always on
- RDS: always on
- ElastiCache: always on
- S3/CloudWatch: usage-based

This can easily cost more than a VPS before any users because ALB, RDS, ElastiCache, and minimum tasks have ongoing charges.

## Pricing/quota connection

A paid plan should be priced at least about 2x backend variable cost after payment fees, support time, refunds, and abuse risk. For file-processing SaaS, do not sell unlimited heavy processing cheaply.
