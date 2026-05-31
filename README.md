# Cloud-native Document Intelligence & Request Analytics Platform on AWS

## Project Overview

This project is a cloud-native document intelligence and request analytics platform in incremental development. The current milestone is a FastAPI API deployed to one Ubuntu EC2 instance with Hugging Face summarization, private S3 artifact storage, and RDS PostgreSQL metadata persistence.

Amazon S3 integration uses an attached EC2 IAM role. No AWS credentials are required or hard-coded.

## Motivation

The project demonstrates how a small local API can evolve into an observable AWS workload. The implementation starts with a narrow, working service and adds cloud capabilities step by step: deployment, document storage, secure service permissions, durable data stores, monitoring, and CI/CD.

## Current Capabilities

- FastAPI service with interactive OpenAPI documentation.
- `GET /health` for service health checks.
- `POST /summarize` for text summarization.
- `GET /requests/{request_id}` for request metadata lookup.
- Lightweight Hugging Face summarization when available.
- Rule-based fallback for short text, unavailable model files, or model failures.
- Environment-based configuration without hard-coded AWS credentials.
- Minimal EC2 runtime dependencies that do not install PyTorch or CUDA packages.
- Optional S3 artifact storage controlled by environment variables.
- RDS PostgreSQL request metadata persistence configured through `DATABASE_URL`.

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

## Current Local Architecture

```text
Client
  |
  v
FastAPI API
  |
  +-- Hugging Face summarizer
  +-- Rule-based fallback
  +-- In-memory request store
```

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

## Deployment Roadmap

- [x] Complete the local FastAPI summarization API.
- [x] Publish the GitHub baseline.
- [x] Configure an AWS Budget alert.
- [x] Deploy the current API to one Ubuntu EC2 instance.
- [x] Add S3 storage using an EC2 IAM role without hard-coded credentials.
- [ ] Verify durable RDS PostgreSQL request metadata persistence.
- [ ] Add DynamoDB, CloudWatch, and GitHub Actions incrementally.

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
5. [ ] Verify Amazon RDS for PostgreSQL request metadata persistence.
6. Add Amazon DynamoDB where key-value request metadata is useful.
7. Add Amazon CloudWatch logs and monitoring.
8. Add GitHub Actions CI/CD.
9. Explore KMS, CloudTrail, GuardDuty, and Inspector at a basic level.

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
export DATABASE_URL="postgresql+psycopg2://appuser:<password>@<rds-endpoint>:5432/docintelligence"
```

Use the limited application DB user `appuser`. Do not commit the password or a populated `DATABASE_URL`.

The RDS Security Group should allow inbound PostgreSQL `5432` from the EC2 Security Group only. Do not expose PostgreSQL publicly.

See [`rds-postgresql-guide.md`](rds-postgresql-guide.md) for setup and verification.

The RDS database has been created and is reachable from EC2. End-to-end application persistence verification on EC2 is the remaining deployment step.

## Verified End-to-End Flow

Swagger UI called `POST /summarize` and received HTTP `200`. The response returned `method: "huggingface"` plus `input_s3_key` and `output_s3_key`.

Verified request ID:

```text
b2e80bc4-bf1f-464b-b1a6-7caa57f3d75f
```

Confirmed private S3 artifacts:

```text
inputs/test-user/b2e80bc4-bf1f-464b-b1a6-7caa57f3d75f.json
outputs/test-user/b2e80bc4-bf1f-464b-b1a6-7caa57f3d75f.json
```

The files were confirmed from EC2 with `aws s3 cp`. They remain private application artifacts, not public URLs.

## Security Notes

- Never commit `.env`, AWS credentials, private keys, `.venv`, or model cache files.
- Use IAM roles for AWS workloads instead of long-lived access keys.
- Review staged files with `git status` and `git diff --cached` before every push.

## Current Limitations

- `DATABASE_URL` must be set before the API starts.
- The API accepts text only. File upload and text extraction are not implemented yet.
- S3 artifact storage is optional. Metadata persistence continues with `null` S3 keys if uploads fail.
- When ML dependencies are installed, the first Hugging Face request may download model files into `.cache/huggingface`.
