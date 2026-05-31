# Architecture

## Scope

This document separates the implemented local and EC2 deployment baseline from the planned AWS architecture. AWS SDK integration is not implemented yet.

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
  |     +-- In-memory request store
  |
  +-- /requests/{request_id}
        |
        +-- Reads from in-memory request store
```

## Components

- `app/main.py`: API routes, request/response models, and temporary in-memory storage.
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
Uvicorn on Ubuntu EC2
  |
  v
FastAPI app
  |
  +-- /health
  +-- /docs
  +-- /summarize
  +-- /requests/{request_id}
  |
  +-- In-memory request store
  |
  +-- Optional private S3 artifact storage
        +-- inputs/{user_id}/{request_id}.json
        +-- outputs/{user_id}/{request_id}.json
```

Verified remotely:

- `GET /health`
- Swagger UI at `/docs`

The EC2 baseline uses the minimal runtime dependencies. Hugging Face inference is optional and will be optimized later with CPU-only PyTorch or a larger EBS volume. Without ML dependencies, `/summarize` continues to use the rule-based fallback.

S3 artifact storage is also optional. When `ENABLE_S3=true`, `/summarize` attempts to store private input and output JSON artifacts. When S3 is disabled or an upload fails, the API continues with the in-memory record only.

## Data Storage

Requests are stored in a Python dictionary for the first local milestone.

This is useful for development because it keeps the API simple and easy to run. It is not durable and should be replaced later with managed storage.

## Planned AWS Architecture

```text
Client
  |
  v
EC2-hosted FastAPI API
  |
  +-- IAM role, no hard-coded access keys
  |
  +-- Amazon S3
  |     +-- Uploaded source documents
  |
  +-- Amazon RDS for PostgreSQL
  |     +-- Durable relational records and analytics
  |
  +-- Amazon DynamoDB
  |     +-- Request metadata where key-value access is useful
  |
  +-- Amazon CloudWatch
        +-- Logs, metrics, and alarms
```

## Delivery Sequence

| Phase | Goal | Notes |
| --- | --- | --- |
| `0` | AWS Budget alert | Configure before creating AWS workloads. |
| `1` | EC2 deployment | Run the existing FastAPI application on a small instance. |
| `2` | S3 integration | Add document upload and storage. |
| `3` | IAM role | Grant EC2 narrowly scoped S3 access without access keys. |
| `4` | RDS PostgreSQL | Replace or extend in-memory storage with durable relational data. |
| `5` | DynamoDB | Add a key-value persistence use case for request metadata. |
| `6` | CloudWatch | Add logs, metrics, alarms, and basic observability. |
| `7` | GitHub Actions | Add CI/CD after deployment steps are understood manually. |
| `8` | Security exploration | Explore KMS, CloudTrail, GuardDuty, and Inspector basics. |

## Current S3 Integration

- Optional `boto3` upload integration is implemented.
- Input text and output summary JSON artifacts use separate S3 prefixes.
- The `/summarize` response and in-memory record include S3 object keys when uploads succeed.
- Block Public Access must remain enabled.
- EC2 uses an IAM role instead of hard-coded AWS credentials.
- Manual bucket creation, IAM role attachment, and EC2 verification remain deployment tasks.

## Not Implemented Yet

- Manual S3 bucket creation and EC2 verification
- EC2 IAM role creation and attachment for S3 access
- Amazon RDS for PostgreSQL
- Amazon DynamoDB
- Amazon CloudWatch logs and monitoring
- GitHub Actions CI/CD

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
