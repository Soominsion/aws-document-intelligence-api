# Cloud-native Document Intelligence & Request Analytics Platform on AWS

## Project Overview

This project is a cloud-native document intelligence and request analytics platform in incremental development. The current milestone is a FastAPI API deployed to one Ubuntu EC2 instance. It summarizes text, records each request, and allows request lookup.

AWS SDK integration is intentionally deferred until the EC2 deployment baseline is documented. No AWS credentials are required or hard-coded.

## Motivation

The project demonstrates how a small local API can evolve into an observable AWS workload. The implementation starts with a narrow, working service and adds cloud capabilities step by step: deployment, document storage, secure service permissions, durable data stores, monitoring, and CI/CD.

## Current Capabilities

- FastAPI service with interactive OpenAPI documentation.
- `GET /health` for service health checks.
- `POST /summarize` for text summarization.
- `GET /requests/{request_id}` for in-memory request lookup.
- Lightweight Hugging Face summarization when available.
- Rule-based fallback for short text, unavailable model files, or model failures.
- Environment-based configuration without hard-coded AWS credentials.
- Minimal EC2 runtime dependencies that do not install PyTorch or CUDA packages.
- Optional S3 artifact storage controlled by environment variables.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Optional: create a local `.env` file from `.env.example` to override settings. The `.env` file is ignored by Git.

The default install is intentionally lightweight. It starts FastAPI and keeps `/summarize` usable through the rule-based fallback without installing Hugging Face or PyTorch.

## Optional Local ML Setup

Install CPU-only PyTorch first, then the optional Hugging Face dependencies:

```powershell
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-ml.txt
```

This keeps CUDA packages out of the default installation. Local Hugging Face summarization has been verified with `method: "huggingface"`.

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

Local and EC2 verification are intentionally separated:

| Environment | Verified scope |
| --- | --- |
| Local | FastAPI endpoints and Hugging Face summarization with `method: "huggingface"`. |
| EC2 | FastAPI deployment, `/health`, and `/docs`. ML inference remains optional and will be optimized later with CPU-only PyTorch or a larger EBS volume. |

## Deployment Roadmap

- [x] Complete the local FastAPI summarization API.
- [x] Publish the GitHub baseline.
- [x] Configure an AWS Budget alert.
- [x] Deploy the current API to one Ubuntu EC2 instance.
- [ ] Add S3 storage using an EC2 IAM role without hard-coded credentials.
- [ ] Add RDS PostgreSQL, DynamoDB, CloudWatch, and GitHub Actions incrementally.

Preparation guides:

- [`github-safety-check.md`](github-safety-check.md)
- [`aws-budget-guide.md`](aws-budget-guide.md)
- [`ec2-deployment-guide.md`](ec2-deployment-guide.md)

## Future AWS Architecture

The planned implementation sequence is intentionally incremental:

1. Configure an AWS Budget alert before creating workloads.
2. Deploy the FastAPI service to Amazon EC2.
3. Add Amazon S3 document storage.
4. Use an IAM role for EC2-to-S3 access.
5. Add Amazon RDS for PostgreSQL.
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

The API returns these object keys as `input_s3_key` and `output_s3_key`. It also stores them in the in-memory request record. If S3 is disabled or an upload fails, the API continues with in-memory storage and returns both keys as `null`.

Keep S3 Block Public Access enabled. These JSON artifacts are private application data and do not need public URLs.

On EC2, attach an IAM role with narrowly scoped S3 permissions. Boto3 automatically uses the temporary role credentials. Do not add AWS access keys or secret keys to `.env`.

Run locally without AWS credentials:

```powershell
$env:ENABLE_S3 = "false"
python -m uvicorn app.main:app --reload
```

Run on EC2 after creating the bucket and attaching the EC2 IAM role:

```bash
export ENABLE_S3=true
export S3_BUCKET_NAME="<your-private-bucket-name>"
export AWS_REGION="ap-northeast-2"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

See [`s3-integration-guide.md`](s3-integration-guide.md) for manual AWS setup and verification.

## Security Notes

- Never commit `.env`, AWS credentials, private keys, `.venv`, or model cache files.
- Use IAM roles for AWS workloads instead of long-lived access keys.
- Review staged files with `git status` and `git diff --cached` before every push.

## Current Limitations

- Request records are stored in memory and disappear when the server restarts.
- The API accepts text only. File upload and text extraction are not implemented yet.
- S3 artifact storage is optional and falls back to in-memory-only behavior if uploads fail.
- EC2 ML inference is optional during this milestone.
- When ML dependencies are installed, the first Hugging Face request may download model files into `.cache/huggingface`.
