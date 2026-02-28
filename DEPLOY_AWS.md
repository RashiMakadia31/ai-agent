# AWS Deployment Guide (ECS Fargate)

This repo is now prepared to run as a single FastAPI service in AWS:
- API routes (`/chat`, `/sql/*`, `/thinking-log`, etc.)
- frontend pages (`/index`, `/login`, `/register`, `/mysql-ui`)
- static assets under `/static/*`

## 1. Prerequisites

- AWS account with permissions for: ECR, ECS, IAM, ELB, CloudWatch, ACM, Route53
- Docker installed locally
- AWS CLI configured (`aws configure`)
- A rotated Gemini key (do not reuse an exposed key)

## 2. Environment Variables (set in ECS task definition)

- `GEMINI_API_KEY` (required, use Secrets Manager)
- `GEMINI_MODEL` (optional, default: `gemini-2.5-flash`)
- `CORS_ORIGINS` (optional, comma-separated)
  - Example: `https://app.example.com,https://www.app.example.com`

## 3. Build and Push Docker Image to ECR

```bash
REGION=us-east-1
REPO=aws-deployment
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws ecr create-repository --repository-name "$REPO" --region "$REGION" || true
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

docker build -t "$REPO:latest" .
docker tag "$REPO:latest" "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO:latest"
docker push "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO:latest"
```

## 4. Create ECS Infrastructure

1. Create ECS cluster (Fargate).
2. Create IAM roles:
   - Task execution role (with `AmazonECSTaskExecutionRolePolicy`)
   - Task role (minimum app permissions only; add S3/RDS if required)
3. Create CloudWatch log group (for container logs).

## 5. Create Task Definition

- Launch type: `FARGATE`
- Container image: ECR image URI
- Port mapping: `8000`
- Command:
  - `gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 core.main:app --timeout 120`
- Health check command:
  - `CMD-SHELL curl -f http://localhost:8000/ping || exit 1`
- CPU/memory: start with `0.5 vCPU / 1 GB` (adjust after load testing)
- Secrets:
  - Inject `GEMINI_API_KEY` from AWS Secrets Manager
- Environment:
  - `GEMINI_MODEL`
  - `CORS_ORIGINS`

## 6. Create ALB and Target Group

1. Create target group:
   - Target type: `ip`
   - Protocol: `HTTP`
   - Port: `8000`
   - Health check path: `/ping`
2. Create internet-facing ALB:
   - Listener `80` (and `443` after cert)
   - Register ECS service with this target group.
3. Increase ALB idle timeout (important for SSE `/thinking-log`):
   - Set > 60s (for example, 180s).

## 7. Create ECS Service

- Cluster: your ECS cluster
- Launch type: Fargate
- Task definition: created above
- Desired count: `1` (start), then scale
- Networking:
  - Private subnets for tasks (recommended)
  - Public subnets for ALB
  - Security groups:
    - ALB SG: allow `80/443` from internet
    - ECS SG: allow `8000` from ALB SG only

## 8. Add HTTPS and Domain

1. Request ACM certificate for your domain.
2. Add HTTPS listener (`443`) on ALB with ACM cert.
3. Route53 alias record -> ALB DNS name.
4. Optionally redirect `80 -> 443`.

## 9. Verify Deployment

Run:

```bash
curl -I https://your-domain/ping
curl https://your-domain/ping
```

Then open:
- `https://your-domain/index`
- `https://your-domain/mysql-ui`

## 10. Rollout Updates

1. Build and push a new image tag.
2. Register new task definition revision with new image.
3. Update ECS service to the new revision.
4. Verify health checks and logs.

## 11. Recommended Hardening

- Keep `CORS_ORIGINS` restricted to your domains.
- Store all secrets in Secrets Manager (not in git / `.env`).
- Enable ECS service autoscaling (CPU/memory target tracking).
- Add CloudWatch alarms for 5xx and high CPU/memory.

