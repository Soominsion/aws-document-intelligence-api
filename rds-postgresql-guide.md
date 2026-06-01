# RDS PostgreSQL Integration Guide

This milestone adds durable request metadata storage with Amazon RDS for PostgreSQL. Local development can use a SQLite database URL.

## Storage Responsibilities

Amazon S3 stores private input and output JSON artifacts:

```text
inputs/{user_id}/{request_id}.json
outputs/{user_id}/{request_id}.json
```

PostgreSQL stores request metadata in the `requests` table:

| Column | Purpose |
| --- | --- |
| `request_id` | Request UUID primary key |
| `user_id` | Artifact grouping identifier |
| `status` | Request processing status |
| `summary` | Generated summary |
| `method` | `huggingface` or `rule_based` |
| `created_at` | Timezone-aware creation timestamp |
| `input_s3_key` | Nullable S3 input artifact key |
| `output_s3_key` | Nullable S3 output artifact key |

## Network Rule

Keep RDS non-public where practical.

In the RDS Security Group, add one inbound rule:

| Type | Port | Source |
| --- | --- | --- |
| `PostgreSQL` | `5432` | EC2 Security Group |

Use the EC2 Security Group as the source. Do not allow `0.0.0.0/0`.

## Limited Application User

Use the limited PostgreSQL application user:

```text
appuser
```

The application database is:

```text
docintelligence
```

Provision the `requests` table and grant only the permissions needed by the app. The SQLAlchemy model also calls `create_all()` at startup, which is harmless when the table already exists.

Run the schema setup as a database owner or administrator:

```sql
CREATE TABLE IF NOT EXISTS requests (
    request_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL,
    summary TEXT NOT NULL,
    method VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    input_s3_key VARCHAR(1024),
    output_s3_key VARCHAR(1024)
);

GRANT USAGE ON SCHEMA public TO appuser;
GRANT SELECT, INSERT, UPDATE ON TABLE requests TO appuser;
```

## Run Locally With SQLite

No RDS credentials are needed:

```powershell
$env:DATABASE_URL = "sqlite:///./local-dev.db"
python -m uvicorn app.main:app --reload
```

The local SQLite file is ignored by Git.

## Run on EC2 With RDS

Set the URL at runtime. Replace the placeholders and do not commit the populated value:

```bash
export DATABASE_URL="postgresql+psycopg2://appuser:<password>@<rds-endpoint>:5432/docintelligence?sslmode=require"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If the password contains URL-sensitive characters, URL-encode it before building the connection string.

## Verify Durable Persistence

1. Start the API with `DATABASE_URL` configured.
2. Open `http://<EC2_PUBLIC_IP>:8000/docs`.
3. Run `POST /summarize`.
4. Save the returned `request_id`.
5. Run `GET /requests/{request_id}` and confirm the record is returned.
6. Stop Uvicorn with `Ctrl+C`.
7. Start Uvicorn again with the same environment variables.
8. Run `GET /requests/{request_id}` again.
9. Confirm the record still exists after the process restart.

## Verified EC2 Result

The RDS-backed request flow has been verified on EC2:

1. Swagger UI called `POST /summarize`.
2. The API returned `method: "huggingface"` and private S3 object keys.
3. SQLAlchemy inserted the request metadata into RDS PostgreSQL.
4. The API server was restarted.
5. `GET /requests/{request_id}` returned the same durable RDS-backed record.

Final verified row:

```text
request_id: c27e74fa-6715-4c29-a1da-5af4fe3f9b28
user_id: test-user
status: completed
method: huggingface
input_s3_key: inputs/test-user/c27e74fa-6715-4c29-a1da-5af4fe3f9b28.json
output_s3_key: outputs/test-user/c27e74fa-6715-4c29-a1da-5af4fe3f9b28.json
```

The application uses the limited `appuser` DB user. Rotate its password after manual testing and keep the new value outside Git.

## Failure Behavior

- If `DATABASE_URL` is empty, the app fails to start with a clear configuration error.
- If PostgreSQL is unavailable during startup, the app fails to start rather than claiming durable storage is ready.
- If PostgreSQL fails during a save or lookup after startup, the API returns HTTP `503`.
- The API response does not expose the database password or connection string.

## Security Notes

- Never commit a populated `DATABASE_URL`.
- Never add database passwords to `.env.example`.
- Keep using the limited `appuser` account for the application.
- Restrict PostgreSQL `5432` to the EC2 Security Group.
- Keep S3 objects private and continue using the EC2 IAM role for S3 access.

## Cleanup

When the experiment is finished:

1. Stop or delete the RDS instance.
2. Decide whether to retain or delete snapshots.
3. Remove unused Security Group rules.
4. Review AWS Billing and the configured Budget alert.
