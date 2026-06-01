# Cloud-native Document Intelligence & Request Analytics Platform on AWS

## Project Overview

Built and deployed a cloud-native FastAPI document summarization API on AWS using EC2, S3, an IAM role, RDS PostgreSQL, DynamoDB, CloudWatch, and Hugging Face inference, with private artifact storage, durable metadata persistence, status tracking, monitoring, and lightweight CI/CD.

The Linux deployment uses Security Groups, environment-based configuration, and least-privilege EC2-to-S3 access. No AWS credentials are required or hard-coded.

## Motivation

The project demonstrates how a small local API can evolve into an observable AWS workload. The implementation starts with a narrow, working service and adds cloud capabilities step by step: deployment, document storage, secure service permissions, durable data stores, monitoring, and CI/CD.

## Current Capabilities

- FastAPI service with interactive OpenAPI documentation.
- `GET /health` for service health checks.
- `POST /summarize` for text summarization.
- `GET /requests/{request_id}` for request metadata lookup.
- `GET /status/{request_id}` for DynamoDB-backed status lookup.
- Lightweight Hugging Face summarization when available.
- Rule-based fallback for short text, unavailable model files, or model failures.
- Environment-based configuration without hard-coded AWS credentials.
- Minimal EC2 runtime dependencies that do not install PyTorch or CUDA packages.
- Optional S3 artifact storage controlled by environment variables.
- RDS PostgreSQL request metadata persistence configured through `DATABASE_URL`.
- DynamoDB request status tracking controlled by environment variables.
- CloudWatch Logs, metric filter, alarm, and dashboard for basic observability.
- GitHub Actions CI plus a lightweight EC2 deployment workflow.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Optional: create a local `.env` file from `.env.example` to override settings. The `.env` file is ignored by Git.

Set a local development database URL before starting the API:

```powershell
$env:DATABASE_URL = "sqlite:///./local-dev.db"
```

The default dependency install is intentionally lightweight. It starts FastAPI and keeps `/summarize` usable through the rule-based fallback without installing Hugging Face or PyTorch.

## Optional Local ML Setup

Install CPU-only PyTorch first, then the optional Hugging Face dependencies:

```powershell
pip install --no-cache-dir torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
pip install --no-cache-dir -r requirements-ml.txt
```

This keeps CUDA packages out of the default installation. Hugging Face summarization has been verified locally and on EC2 with `method: "huggingface"`.

## Run

```powershell
python -m uvicorn app.main:app --reload
```

Open the interactive API docs at:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Returns the local service status. |
| `POST` | `/summarize` | Summarizes submitted text and stores the request record. |
| `GET` | `/requests/{request_id}` | Returns a stored request record by ID. |
| `GET` | `/status/{request_id}` | Returns an optional DynamoDB-backed request status item. |

## Example Request and Response

```powershell
$body = @{
  text = "Amazon Web Services is a cloud computing platform. It provides compute, storage, database, networking, and monitoring services. Customers use AWS to build scalable and reliable applications. This project tests a small document summarization API."
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/summarize" `
  -ContentType "application/json" `
  -Body $body
```

```json
{
  "request_id": "25b85ba6-af50-4c04-9fee-c5a922d450df",
  "status": "completed",
  "summary": "Amazon Web Services is a cloud computing platform...",
  "method": "huggingface",
  "created_at": "2026-05-31T11:14:04.659046Z",
  "input_s3_key": null,
  "output_s3_key": null
}
```

The optional `user_id` request field groups S3 objects by user. Existing clients can omit it and use the default `anonymous` value.

## Current Architecture

```text
Client / Swagger UI
  |
  v
EC2 Ubuntu FastAPI
  |
  +-- systemd: doc-intelligence.service
  +-- Hugging Face summarization or rule-based fallback
  +-- Private S3 input/output artifact storage
  +-- RDS PostgreSQL request metadata persistence
  +-- DynamoDB request status tracking
  +-- CloudWatch Logs and basic monitoring
```

Local development can use SQLite or another local database through `DATABASE_URL`. The deployed AWS environment uses RDS PostgreSQL.

See [`architecture.md`](architecture.md) for the detailed current and planned architecture.
Track the implementation steps in [`deployment-checklist.md`](deployment-checklist.md).

## EC2 Deployment Result

The first EC2 deployment milestone is complete:

- [x] Configure an AWS Budget alert.
- [x] Launch one Ubuntu EC2 instance.
- [x] Allow inbound `SSH 22` from `My IP`.
- [x] Allow inbound `FastAPI 8000` from `My IP`.
- [x] Clone the GitHub repository into EC2.
- [x] Create a Python virtual environment.
- [x] Install the minimal runtime dependencies.
- [x] Launch FastAPI with:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- [x] Verify remote access to `/health`.
- [x] Verify remote access to `/docs`.

EC2 deployment verification now includes S3 and ML inference:

- [x] Expand the EC2 root volume to approximately `15G`.
- [x] Install CPU-only `torch==2.5.1+cpu` and `transformers==4.47.1`.
- [x] Attach the EC2 IAM role `ec2-s3-doc-intelligence-role`.
- [x] Verify temporary role credentials through IMDSv2 and `aws sts get-caller-identity`.
- [x] Verify private S3 access with `aws s3 ls` and `aws s3 cp`.
- [x] Verify `/summarize` returns `method: "huggingface"` and stores input/output JSON artifacts in S3.
- [x] Run FastAPI through `doc-intelligence.service`.
- [x] Verify DynamoDB `RequestStatus` writes and `/status/{request_id}` lookups.
- [x] Connect application logs to CloudWatch Logs.
- [x] Create the `FastAPIErrorCount` metric filter.
- [x] Create the `DocIntelligence-FastAPI-Error-Alarm` alarm.
- [x] Create the `DocIntelligenceDashboard` dashboard.
- [x] Verify the lightweight GitHub Actions CD run.

## Deployment Roadmap

- [x] Complete the local FastAPI summarization API.
- [x] Publish the GitHub baseline.
- [x] Configure an AWS Budget alert.
- [x] Deploy the current API to one Ubuntu EC2 instance.
- [x] Add S3 storage using an EC2 IAM role without hard-coded credentials.
- [x] Add and verify durable RDS PostgreSQL request metadata persistence.
- [x] Add CloudWatch Logs and basic monitoring.
- [x] Add a lightweight GitHub Actions CI workflow.
- [x] Create and verify the DynamoDB request status table on AWS.
- [x] Add and verify the lightweight EC2 deployment workflow.
- [ ] Evaluate load balancing only where it adds a clear use case.

Preparation guides:

- [`github-safety-check.md`](github-safety-check.md)
- [`aws-budget-guide.md`](aws-budget-guide.md)
- [`ec2-deployment-guide.md`](ec2-deployment-guide.md)

## Delivery Sequence

The implementation sequence is intentionally incremental. The first four steps are complete:

1. [x] Configure an AWS Budget alert before creating workloads.
2. [x] Deploy the FastAPI service to Amazon EC2.
3. [x] Add Amazon S3 artifact storage.
4. [x] Use an IAM role for EC2-to-S3 access.
5. [x] Add and verify Amazon RDS for PostgreSQL request metadata persistence.
6. [x] Add Amazon CloudWatch logs and monitoring.
7. [x] Add a lightweight GitHub Actions CI workflow.
8. [x] Create and verify the Amazon DynamoDB request status table.
9. [x] Run FastAPI as `doc-intelligence.service` and verify the lightweight EC2 deployment workflow.
10. Optionally evaluate ALB/ELB for a production-style entry point.
11. Treat Route 53 and infrastructure as code (IaC) as future improvements.
12. Explore KMS, CloudTrail, GuardDuty, and Inspector at a basic level.

NAT Gateway is intentionally out of scope to avoid unnecessary cost. ALB and Route 53 are optional later improvements.

## S3 Integration

S3 artifact storage is optional and disabled by default. When `ENABLE_S3=true`, each successful `/summarize` request attempts to store:

```text
inputs/{user_id}/{request_id}.json
outputs/{user_id}/{request_id}.json
```

The API returns these object keys as `input_s3_key` and `output_s3_key`. It also stores them in the PostgreSQL request metadata record. If S3 is disabled or an upload fails, the API continues without S3 artifacts and returns both keys as `null`.

Keep S3 Block Public Access enabled. These JSON artifacts are private application data and do not need public URLs.

On EC2, the attached IAM role `ec2-s3-doc-intelligence-role` provides narrowly scoped S3 permissions. Boto3 automatically uses its temporary role credentials through the instance metadata service. Do not add AWS access keys or secret keys to `.env`.

Run locally without AWS credentials:

```powershell
$env:ENABLE_S3 = "false"
python -m uvicorn app.main:app --reload
```

Run on EC2:

```bash
export ENABLE_S3=true
export S3_BUCKET_NAME="doc-intelligence-artifacts-594541045547-ap-northeast-2-an"
export AWS_REGION="ap-northeast-2"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

See [`s3-integration-guide.md`](s3-integration-guide.md) for manual AWS setup and verification.

## RDS PostgreSQL Integration

Request metadata is stored durably in RDS PostgreSQL. The original input and output artifacts remain in private S3 objects.

`POST /summarize` writes metadata to PostgreSQL and `GET /requests/{request_id}` reads from PostgreSQL:

```bash
export DATABASE_URL="postgresql+psycopg2://appuser:<password>@<rds-endpoint>:5432/docintelligence?sslmode=require"
```

Use the limited application DB user `appuser`. Do not commit the password or a populated `DATABASE_URL`.

The RDS Security Group should allow inbound PostgreSQL `5432` from the EC2 Security Group only. Do not expose PostgreSQL publicly.

See [`rds-postgresql-guide.md`](rds-postgresql-guide.md) for setup and verification.

The RDS database is reachable from EC2. End-to-end durable persistence has been verified through an RDS insert and a successful `GET /requests/{request_id}` after restarting the API server.

## DynamoDB Status Tracking

DynamoDB provides a lightweight request status lookup path. RDS PostgreSQL remains the durable metadata store.

When `ENABLE_DYNAMODB=true`, each successful `/summarize` request attempts to write:

```text
request_id, user_id, status, method, created_at, input_s3_key, output_s3_key
```

Create an on-demand table named `RequestStatus` with a string partition key named `request_id`. If a DynamoDB write fails, the API logs a warning and preserves the successful RDS-backed `/summarize` response.

Extend the EC2 IAM role with narrowly scoped `dynamodb:PutItem` and `dynamodb:GetItem` permissions for that table. Boto3 uses the EC2 role credentials automatically; do not add AWS access keys to the app.

Run locally or in CI with DynamoDB disabled:

```powershell
$env:ENABLE_DYNAMODB = "false"
```

Run on EC2 with the verified table and narrowly scoped EC2 IAM role permissions:

```bash
export ENABLE_DYNAMODB=true
export DYNAMODB_TABLE_NAME="RequestStatus"
```

Use `GET /status/{request_id}` for the optional DynamoDB-backed lookup. The endpoint returns HTTP `503` with a clear message when the integration is disabled.

The `RequestStatus` table, status writes after `POST /summarize`, and `GET /status/{request_id}` lookups have been verified on EC2.

## CloudWatch Observability

Basic observability is configured for the EC2-hosted FastAPI service:

- CloudWatch Logs receives application logs.
- Metric filter: `FastAPIErrorCount`.
- Alarm: `DocIntelligence-FastAPI-Error-Alarm`.
- Dashboard: `DocIntelligenceDashboard`.

This provides a small operational baseline for inspecting logs and monitoring FastAPI errors.

## Verified End-to-End Flow

Swagger UI called `POST /summarize` and received HTTP `200`. The response returned `method: "huggingface"` plus `input_s3_key` and `output_s3_key`.

Final verified request ID:

```text
c27e74fa-6715-4c29-a1da-5af4fe3f9b28
```

Confirmed RDS metadata row:

```text
request_id: c27e74fa-6715-4c29-a1da-5af4fe3f9b28
user_id: test-user
status: completed
method: huggingface
input_s3_key: inputs/test-user/c27e74fa-6715-4c29-a1da-5af4fe3f9b28.json
output_s3_key: outputs/test-user/c27e74fa-6715-4c29-a1da-5af4fe3f9b28.json
```

The private S3 artifacts were confirmed from EC2. After restarting the API server, `GET /requests/c27e74fa-6715-4c29-a1da-5af4fe3f9b28` still returned the RDS-backed metadata record.

This verifies durable metadata persistence beyond the lifetime of the FastAPI process. The EC2 instance was stopped after testing to limit development cost.

The later deployment milestones are also complete: DynamoDB status writes and `GET /status/{request_id}` lookups were verified, CloudWatch observability resources were created, FastAPI was registered as `doc-intelligence.service`, and a `main` branch push completed the lightweight EC2 deployment workflow successfully.

## Security Notes

- Never commit `.env`, AWS credentials, private keys, `.venv`, or model cache files.
- Use IAM roles for AWS workloads instead of long-lived access keys.
- Review staged files with `git status` and `git diff --cached` before every push.

## GitHub Actions CI

The basic `CI` workflow runs on every push and pull request with Python `3.12`. It installs the lightweight runtime requirements, imports the FastAPI app, and runs a `/health` pytest check with:

```text
DATABASE_URL=sqlite:///./ci-test.db
ENABLE_S3=false
ENABLE_DYNAMODB=false
AWS_REGION=ap-northeast-2
```

CI does not install `requirements-ml.txt`, download Hugging Face models, call DynamoDB, deploy AWS resources, or use AWS credentials.

## GitHub Actions CD

The `main` branch uses a lightweight EC2 deployment workflow after CI succeeds. Pull requests run CI only. Docs-only changes do not trigger EC2 deployment.

The deploy job reads `EC2_HOST`, `EC2_USER`, and `EC2_SSH_PRIVATE_KEY` from GitHub Secrets. It connects to EC2 over SSH and runs:

```bash
cd /home/ubuntu/aws-document-intelligence-api
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart doc-intelligence
sudo systemctl status doc-intelligence --no-pager
```

The EC2 instance contains the cloned repository, `.venv`, runtime environment configuration, and the registered `doc-intelligence.service`. The lightweight EC2 deployment workflow has completed successfully. Keep database passwords and AWS credentials outside the repository and workflow.

This SSH-based CD path is intentionally small and suitable for a demo. Restrict EC2 SSH access carefully. GitHub-hosted runners use changing outbound IP addresses, so SSH access may need to be opened temporarily for deployment or replaced with a safer deployment mechanism. Production alternatives include a self-hosted runner, AWS Systems Manager, CodeDeploy, or an OIDC-based AWS deployment flow.

## Current Limitations

- `DATABASE_URL` must be set before the API starts.
- The API accepts text only. File upload and text extraction are not implemented yet.
- S3 artifact storage is optional. Metadata persistence continues with `null` S3 keys if uploads fail.
- DynamoDB status tracking is optional. RDS metadata persistence remains authoritative if a status write fails.
- When ML dependencies are installed, the first Hugging Face request may download model files into `.cache/huggingface`.

## Next Steps

- Rotate the `appuser` database password because it was exposed during manual testing.
- Optionally evaluate ALB/ELB later.
- Treat Route 53 and infrastructure as code (IaC) as future improvements.
