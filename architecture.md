# Architecture

## Scope

This document separates the implemented EC2, Hugging Face, S3, IAM role, RDS, DynamoDB, CloudWatch, and lightweight CI/CD baseline from later AWS milestones.

## Current Local Architecture

```text
Client
  |
  v
FastAPI app
  |
  +-- /health
  |
  +-- /summarize
  |     |
  |     +-- Hugging Face summarizer, if available
  |     +-- Rule-based fallback
  |     +-- PostgreSQL request metadata store
  |
  +-- /requests/{request_id}
  |     |
  |     +-- Reads from request metadata database
  |
  +-- /status/{request_id}
        |
        +-- Reads from DynamoDB when enabled
```

## Components

- `app/main.py`: API routes, request/response models, and database operations.
- `app/database.py`: SQLAlchemy engine, session factory, and database dependency.
- `app/models.py`: SQLAlchemy mapping for the PostgreSQL `requests` table.
- `app/dynamodb_utils.py`: Optional DynamoDB status writes and lookups.
- `app/summarizer.py`: Hugging Face summarization wrapper plus rule-based fallback.
- `app/config.py`: Local configuration loaded from environment variables or `.env`.

## Current EC2 Deployment

```text
Client browser
  |
  v
EC2 Public IPv4:8000
  |
  v
systemd: doc-intelligence.service
  |
  v
Uvicorn on Ubuntu EC2
  |
  v
FastAPI app
  |
  +-- /health
  +-- /docs
  +-- /summarize
  +-- /requests/{request_id}
  +-- /status/{request_id}
  |
  +-- Optional private S3 artifact storage
        +-- inputs/{user_id}/{request_id}.json
        +-- outputs/{user_id}/{request_id}.json
  |
  +-- RDS PostgreSQL metadata storage
        +-- requests table
  |
  +-- DynamoDB status tracking
        +-- RequestStatus table
  |
  +-- CloudWatch Logs and monitoring
        +-- FastAPIErrorCount metric filter
        +-- DocIntelligence-FastAPI-Error-Alarm
        +-- DocIntelligenceDashboard
```

Verified remotely:

- `GET /health`
- Swagger UI at `/docs`
- `POST /summarize` with `method: "huggingface"`
- Private input and output JSON artifacts in Amazon S3
- Durable request metadata in Amazon RDS for PostgreSQL
- `GET /requests/{request_id}` after an API server restart
- DynamoDB status writes and `GET /status/{request_id}` lookups
- CloudWatch Logs, metric filter, alarm, and dashboard
- `doc-intelligence.service` restart through the successful GitHub Actions CD run

The EC2 root volume was expanded to approximately `15G`. CPU-only `torch==2.5.1+cpu` and `transformers==4.47.1` are installed, and `/summarize` uses the Hugging Face model successfully. The rule-based fallback remains available if the ML path fails.

S3 artifact storage is enabled on EC2. The app uses temporary credentials from the attached IAM role `ec2-s3-doc-intelligence-role`. No access key or secret key is stored in the app. S3 Block Public Access remains enabled.

RDS PostgreSQL persistence is configured through `DATABASE_URL`. Request metadata is stored in PostgreSQL. The database password is supplied at runtime and is not committed.

## Request Metadata Storage

- Request metadata is stored durably in PostgreSQL.
- Original input and output artifacts remain in private S3 objects.

## Deployed AWS Architecture

```text
Client
  |
  v
EC2-hosted FastAPI API
  |
  +-- IAM role, no hard-coded access keys
  |
  +-- Amazon S3
  |     +-- Private input and output JSON artifacts
  |
  +-- Amazon RDS for PostgreSQL
  |     +-- Durable relational records and analytics
  |
  +-- Amazon CloudWatch
  |     +-- Logs, metrics, and alarms
  |
  +-- Amazon DynamoDB
        +-- Lightweight request status lookup by request_id
```

## Delivery Sequence

| Phase | Goal | Notes |
| --- | --- | --- |
| `0` | AWS Budget alert | Configure before creating AWS workloads. |
| `1` | EC2 deployment | Run the existing FastAPI application on a small instance. |
| `2` | S3 integration | Add document upload and storage. |
| `3` | IAM role | Grant EC2 narrowly scoped S3 access without access keys. |
| `4` | RDS PostgreSQL | Store request metadata durably. |
| `5` | CloudWatch | Logs, metric filter, alarm, and dashboard implemented. |
| `6` | GitHub Actions | CI and lightweight EC2 deployment workflow verified. |
| `7` | DynamoDB | Request status table, writes, and lookups verified. |
| `8` | Optional ALB/ELB | Evaluate a production-style entry point. |
| `9` | Route 53 and IaC | Treat DNS and infrastructure as code as future improvements. |
| `10` | Security exploration | Explore KMS, CloudTrail, GuardDuty, and Inspector basics. |

## Verified S3 Integration

- Optional `boto3` upload integration is implemented and enabled on EC2.
- Input text and output summary JSON artifacts use separate S3 prefixes.
- The `/summarize` response and PostgreSQL metadata record include S3 object keys when uploads succeed.
- Block Public Access must remain enabled.
- EC2 uses an IAM role instead of hard-coded AWS credentials.
- IAM role access was verified through IMDSv2, STS, `aws s3 ls`, and `aws s3 cp`.

## RDS PostgreSQL Integration

- SQLAlchemy persistence is configured through `DATABASE_URL`.
- The PostgreSQL table is `requests`.
- The limited application DB user is `appuser`.
- `POST /summarize` stores request metadata after summarization and S3 upload.
- `GET /requests/{request_id}` reads PostgreSQL metadata.
- Local development can use a SQLite `DATABASE_URL`.
- Original input text is stored in the private S3 input artifact. PostgreSQL stores metadata and S3 object keys.
- Durable persistence was verified after restarting the EC2 API server.

## DynamoDB Status Tracking

- `POST /summarize` attempts a DynamoDB status write after the RDS commit.
- DynamoDB write failures log a warning and do not fail the API response.
- `GET /status/{request_id}` reads the optional DynamoDB status item.
- The table name is configured with `DYNAMODB_TABLE_NAME`.
- The integration is disabled by default through `ENABLE_DYNAMODB=false`.
- RDS PostgreSQL remains the durable metadata source of truth.
- The `RequestStatus` table and EC2 request flow have been verified.

## CloudWatch Observability

- FastAPI application logs are connected to CloudWatch Logs.
- The `FastAPIErrorCount` metric filter tracks FastAPI errors.
- The `DocIntelligence-FastAPI-Error-Alarm` alarm is configured.
- The `DocIntelligenceDashboard` dashboard provides a basic operational view.

## GitHub Actions CI/CD

```text
Push to main
  |
  v
GitHub Actions CI
  +-- FastAPI import
  +-- SQLite-backed pytest
  |
  v
Lightweight SSH deployment
  |
  v
Ubuntu EC2
  +-- git pull origin main
  +-- pip install -r requirements.txt
  +-- systemctl restart doc-intelligence
```

The deploy job runs only after CI succeeds on a `main` push. EC2 host, SSH user, and SSH private key values come from GitHub Secrets. The repository does not store deployment credentials. FastAPI runs as `doc-intelligence.service`, and the lightweight EC2 deployment workflow has completed successfully.

This demo workflow uses SSH. Restrict EC2 SSH access and consider AWS Systems Manager, CodeDeploy, a self-hosted runner, or an OIDC-based AWS deployment flow for a stronger production design.

## Not Implemented Yet

- Optional ALB/ELB evaluation
- Route 53 and infrastructure as code

## Cost Controls

- Configure AWS Budget alerts before deployment.
- Do not create a NAT Gateway.
- Keep ALB and Route 53 optional until the core platform works.
- Prefer small, removable development resources.
- Document teardown steps as each AWS resource is added.

## Security Principles

- Do not hard-code AWS credentials.
- Do not commit `.env`, AWS configuration files, private keys, local virtual environments, logs, or Hugging Face model cache files.
- Use IAM roles and least-privilege policies for AWS workloads.
- Add encryption and audit services incrementally after the core deployment works.

## Later Options

- Amazon Textract or Amazon Bedrock for richer document intelligence.
- Application Load Balancer and Route 53 for a production-style entry point.
- AWS KMS for customer-managed encryption keys where justified.
