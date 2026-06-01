# Deployment Checklist

Use this checklist to keep the AWS rollout incremental, reviewable, and easy to tear down.

## 0. Publish Local Baseline

- [x] Implement and verify the local FastAPI API.
- [x] Add `.gitignore` rules for local environments, caches, credentials, keys, and logs.
- [x] Scan local source and documentation for common AWS credential patterns.
- [x] Document local setup, current architecture, and planned AWS architecture.
- [x] Review `git status` and staged changes.
- [x] Push the initial `main` branch to GitHub.
- [x] Confirm GitHub does not contain `.env`, `.venv`, `.cache`, credentials, keys, or logs.

Follow [`github-safety-check.md`](github-safety-check.md) before marking the final item complete.

## 1. Cost Guardrail

- [x] Configure an AWS Budget alert before provisioning workloads.
- [x] Choose a small monthly budget threshold.
- [ ] Confirm the alert email subscription.
- [ ] Record teardown steps for every AWS resource added later.

Follow [`aws-budget-guide.md`](aws-budget-guide.md) before provisioning AWS resources.

## 2. EC2 Deployment

- [x] Choose a small EC2 instance suitable for development.
- [x] Create a security group with `SSH 22` and `FastAPI 8000` limited to `My IP`.
- [x] Install and run the existing FastAPI application.
- [x] Verify `/health` remotely.
- [x] Verify `/docs` remotely.
- [x] Verify `/health`, `/summarize`, and `/requests/{request_id}` remotely.
- [x] Document start, stop, and teardown commands.
- [x] Expand the EC2 root volume to support CPU-only PyTorch and the Hugging Face model cache.
- [x] Enable Hugging Face summarization on EC2 with CPU-only PyTorch.

Follow [`ec2-deployment-guide.md`](ec2-deployment-guide.md) for the first manual deployment.

## 3. S3 Integration

- [x] Create one development S3 bucket with a unique name.
- [x] Keep Block Public Access enabled.
- [x] Add optional `boto3` integration without hard-coded AWS credentials.
- [x] Store input text and output summary JSON in S3 when enabled.
- [x] Return S3 object keys from `/summarize`.
- [x] Verify private input and output artifact storage from EC2.
- [x] Store object references in request records.
- [x] Document bucket cleanup and deletion.

Follow [`s3-integration-guide.md`](s3-integration-guide.md) for manual bucket, IAM role, and verification steps.

## 4. IAM Role

- [x] Create an EC2 IAM role with least-privilege S3 permissions.
- [x] Attach the role to EC2.
- [x] Verify temporary IAM role credentials through IMDSv2 and STS.
- [x] Verify S3 access without access keys in code or `.env`.
- [x] Review and narrow the policy after testing.

## 5. RDS PostgreSQL

- [x] Create a small PostgreSQL development database.
- [x] Keep the database non-public where practical.
- [x] Allow inbound PostgreSQL `5432` from the EC2 Security Group only.
- [x] Add SQLAlchemy persistence configured by `DATABASE_URL`.
- [x] Remove the temporary in-memory request store.
- [x] Use the limited `appuser` application DB user instead of the DB master user.
- [x] Verify `POST /summarize` persists metadata in RDS.
- [x] Verify `GET /requests/{request_id}` reads metadata after an app restart.
- [x] Document schema creation, connection handling, and teardown.

Follow [`rds-postgresql-guide.md`](rds-postgresql-guide.md) for EC2 configuration and verification.

## 6. CloudWatch

- [x] Send application logs to CloudWatch Logs.
- [x] Create the `FastAPIErrorCount` metric filter.
- [x] Create the `DocIntelligence-FastAPI-Error-Alarm` alarm.
- [x] Create the `DocIntelligenceDashboard` dashboard.
- [x] Add basic metrics and alarms.
- [x] Document the basic observability resources.

## 7. GitHub Actions

- [x] Add basic CI for FastAPI import validation and `/health` tests.
- [x] Use SQLite and disable S3 in CI.
- [x] Keep optional Hugging Face and PyTorch dependencies out of CI.
- [x] Add lightweight SSH deployment after successful CI on `main` pushes.
- [x] Read EC2 host, user, and SSH private key values from GitHub Secrets.
- [x] Verify `doc-intelligence.service` is registered and restartable on EC2.
- [x] Verify the first GitHub Actions CD deployment from a `main` push.
- [ ] Replace or harden GitHub-hosted runner SSH access for a production-style deployment.

## 8. DynamoDB Request Status Tracking

- [x] Define lightweight request status lookup as the key-value use case.
- [x] Add optional DynamoDB status writes after successful RDS persistence.
- [x] Add `GET /status/{request_id}` for optional DynamoDB-backed lookup.
- [x] Disable DynamoDB in local CI.
- [x] Create the on-demand `RequestStatus` DynamoDB table.
- [x] Grant the EC2 IAM role narrowly scoped DynamoDB access.
- [x] Verify status writes and lookups from EC2.
- [x] Compare its role with PostgreSQL in the documentation.

## 9. Optional Entry Point Improvements

- [ ] Evaluate ALB/ELB later if a stable public entry point is useful.
- [ ] Treat Route 53 and infrastructure as code (IaC) as future improvements.

## 10. Security Exploration

- [ ] Explore KMS encryption concepts.
- [ ] Explore CloudTrail audit logs.
- [ ] Explore GuardDuty findings.
- [ ] Explore Inspector assessments.

## Cost Constraints

- [ ] Do not create a NAT Gateway.
- [ ] Treat ALB and Route 53 as optional later improvements.
- [ ] Stop or remove unused development resources promptly.
