# Cloud-native Document Intelligence & Request Analytics Platform on AWS

## Project Overview

This project is a cloud-native document intelligence and request analytics platform in incremental development. The current milestone is a local FastAPI API that summarizes text, records each request, and allows request lookup.

AWS integration is intentionally deferred until the local baseline is documented and safely published. No AWS credentials are required or hard-coded.

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

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Optional: create a local `.env` file from `.env.example` to override settings. The `.env` file is ignored by Git.

## Run

```powershell
uvicorn app.main:app --reload
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
  "created_at": "2026-05-31T11:14:04.659046Z"
}
```

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

## Security Notes

- Never commit `.env`, AWS credentials, private keys, `.venv`, or model cache files.
- Use IAM roles for AWS workloads instead of long-lived access keys.
- Review staged files with `git status` and `git diff --cached` before every push.

## Current Limitations

- Request records are stored in memory and disappear when the server restarts.
- The API accepts text only. File upload and text extraction are not implemented yet.
- The first Hugging Face request may download model files into `.cache/huggingface`.
