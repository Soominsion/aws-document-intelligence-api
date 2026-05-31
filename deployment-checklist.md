# Deployment Checklist

Use this checklist to keep the AWS rollout incremental, reviewable, and easy to tear down.

## 0. Publish Local Baseline

- [x] Implement and verify the local FastAPI API.
- [x] Add `.gitignore` rules for local environments, caches, credentials, keys, and logs.
- [x] Scan local source and documentation for common AWS credential patterns.
- [x] Document local setup, current architecture, and planned AWS architecture.
- [ ] Review `git status` and staged changes.
- [ ] Push the initial `main` branch to GitHub.
- [ ] Confirm GitHub does not contain `.env`, `.venv`, `.cache`, credentials, keys, or logs.

## 1. Cost Guardrail

- [ ] Configure an AWS Budget alert before provisioning workloads.
- [ ] Choose a small monthly budget threshold.
- [ ] Confirm the alert email subscription.
- [ ] Record teardown steps for every AWS resource added later.

## 2. EC2 Deployment

- [ ] Choose a small EC2 instance suitable for development.
- [ ] Create a security group with narrowly scoped inbound access.
- [ ] Install and run the existing FastAPI application.
- [ ] Verify `/health`, `/summarize`, and `/requests/{request_id}` remotely.
- [ ] Document start, stop, and teardown commands.

## 3. S3 Integration

- [ ] Create one development S3 bucket with a unique name.
- [ ] Keep Block Public Access enabled.
- [ ] Add document upload and retrieval behavior.
- [ ] Store object references in request records.
- [ ] Document bucket cleanup and deletion.

## 4. IAM Role

- [ ] Create an EC2 IAM role with least-privilege S3 permissions.
- [ ] Attach the role to EC2.
- [ ] Verify S3 access without access keys in code or `.env`.
- [ ] Review and narrow the policy after testing.

## 5. RDS PostgreSQL

- [ ] Create a small PostgreSQL development database.
- [ ] Keep the database non-public where practical.
- [ ] Replace or extend in-memory records with durable relational storage.
- [ ] Document schema creation, connection handling, and teardown.

## 6. DynamoDB

- [ ] Define a specific key-value metadata use case.
- [ ] Create a small on-demand DynamoDB table.
- [ ] Add request metadata reads and writes.
- [ ] Compare its role with PostgreSQL in the documentation.

## 7. CloudWatch

- [ ] Send application logs to CloudWatch.
- [ ] Add basic metrics and alarms.
- [ ] Document how to inspect API errors and service health.

## 8. GitHub Actions

- [ ] Add CI for Python syntax checks and tests.
- [ ] Add deployment automation only after manual deployment is understood.
- [ ] Use GitHub secrets or OIDC as appropriate. Never commit credentials.

## 9. Security Exploration

- [ ] Explore KMS encryption concepts.
- [ ] Explore CloudTrail audit logs.
- [ ] Explore GuardDuty findings.
- [ ] Explore Inspector assessments.

## Cost Constraints

- [ ] Do not create a NAT Gateway.
- [ ] Treat ALB and Route 53 as optional later improvements.
- [ ] Stop or remove unused development resources promptly.
