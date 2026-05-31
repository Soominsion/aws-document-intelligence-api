# Optional S3 Integration Guide

This milestone adds private S3 artifact storage to `POST /summarize`. S3 remains optional so local development and EC2 health checks continue to work without AWS credentials.

## Stored Objects

When `ENABLE_S3=true`, the API attempts to store two JSON objects per summarization request:

```text
inputs/{user_id}/{request_id}.json
outputs/{user_id}/{request_id}.json
```

Example request:

```json
{
  "user_id": "demo-user",
  "text": "Text to summarize."
}
```

If `user_id` is omitted, the API uses `anonymous`. The accepted characters are letters, numbers, `.`, `_`, and `-`.

## Create the Bucket Manually

1. Open the AWS Management Console and go to `S3`.
2. Choose `Create bucket`.
3. Enter a globally unique bucket name.
4. Select `ap-northeast-2` unless your EC2 deployment uses another Region.
5. Keep all S3 Block Public Access settings enabled.
6. Create the bucket.

The objects are private application artifacts. Do not enable public access and do not create public object URLs.

## Create and Attach an EC2 IAM Role

Create an IAM role trusted by EC2 and attach a least-privilege policy for your bucket. Replace `<your-private-bucket-name>` before saving the policy.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::<your-private-bucket-name>/inputs/*",
        "arn:aws:s3:::<your-private-bucket-name>/outputs/*"
      ]
    }
  ]
}
```

`s3:PutObject` stores artifacts. `s3:DeleteObject` allows best-effort cleanup if the input upload succeeds but the output upload fails.

Attach the role to the running instance:

1. Open `EC2`.
2. Select the instance.
3. Choose `Actions`, `Security`, then `Modify IAM role`.
4. Select the EC2 IAM role.
5. Choose `Update IAM role`.

Do not create IAM user access keys. Boto3 uses temporary credentials from the attached EC2 IAM role automatically.

## Run Locally With S3 Disabled

No AWS credentials are needed:

```powershell
$env:ENABLE_S3 = "false"
python -m uvicorn app.main:app --reload
```

The response contains:

```json
{
  "input_s3_key": null,
  "output_s3_key": null
}
```

## Run on EC2 With S3 Enabled

```bash
cd ~/aws-document-intelligence-api
git pull
source .venv/bin/activate
pip install -r requirements.txt
export ENABLE_S3=true
export S3_BUCKET_NAME="<your-private-bucket-name>"
export AWS_REGION="ap-northeast-2"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Do not export `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY`.

## Verify Through Swagger UI

1. Open `http://<EC2_PUBLIC_IP>:8000/docs`.
2. Run `POST /summarize` with:

```json
{
  "user_id": "demo-user",
  "text": "Amazon S3 stores private request artifacts for this document intelligence API."
}
```

3. Confirm that the response includes keys similar to:

```json
{
  "input_s3_key": "inputs/demo-user/<request_id>.json",
  "output_s3_key": "outputs/demo-user/<request_id>.json"
}
```

4. Open the S3 console and confirm that both JSON objects exist.
5. Run `GET /requests/{request_id}` and confirm that the in-memory record contains both keys.

## Failure Behavior

If S3 is disabled, the bucket is not configured, the IAM role is missing, or upload fails:

- `/summarize` continues to return a completed in-memory result.
- `input_s3_key` and `output_s3_key` are both `null`.
- No sensitive AWS error details are returned in the API response.

## Cleanup

When the experiment is finished:

1. Delete test objects from the `inputs/` and `outputs/` prefixes.
2. Delete the development bucket if it is no longer needed.
3. Detach and remove the EC2 IAM role if it is no longer needed.
4. Stop or terminate unused EC2 resources.

## Official References

- [Boto3 S3 `put_object`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html)
- [S3 Block Public Access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
- [IAM roles for Amazon EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html)
- [Boto3 credentials](https://docs.aws.amazon.com/boto3/latest/guide/credentials.html)
