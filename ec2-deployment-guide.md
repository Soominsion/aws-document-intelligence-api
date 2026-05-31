# EC2 Deployment Guide

This guide deploys the existing FastAPI application to one Ubuntu EC2 instance. It does not add AWS SDK integrations or store AWS credentials on the server.

## Development Plan

Use one small, removable EC2 instance:

- AMI: current Ubuntu Server LTS for `64-bit (x86)`
- Recommended instance type: `t3.medium`
- Storage: a small `gp3` root volume, such as `16 GiB`
- Public IPv4 address: enabled for this learning deployment
- Elastic IP: do not allocate one unless a later milestone clearly needs a stable IP

The default application install is intentionally lightweight and uses the rule-based summarization fallback. Optional ML inference installs PyTorch and loads a Hugging Face summarization model. `t3.medium` gives the model more practical memory headroom than the smallest instance types. For a cheaper fallback-only experiment, try `t3.small`.

Prices vary by AWS Region and account eligibility. Check the console estimate before launching.

## Launch the Instance

1. Open the AWS Management Console and go to `EC2`.
2. Choose `Instances`, then `Launch instances`.
3. Enter a name such as `document-intelligence-dev`.
4. Select the current Ubuntu Server LTS AMI for `64-bit (x86)`.
5. Select `t3.medium`.
6. Create or choose an EC2 key pair.
7. Enable a public IPv4 address for this learning deployment.
8. Create the security group rules described below.
9. Configure a small `gp3` root volume, such as `16 GiB`.
10. Review the estimated cost, then launch the instance.

## Security Group Plan

Create a security group with only these inbound rules:

| Type | Port | Source | Purpose |
| --- | --- | --- | --- |
| `SSH` | `22` | `My IP` | Connect from your current computer only. |
| `Custom TCP` | `8000` | `My IP` | Test the FastAPI service from your current computer only. |

Keep the default outbound rule for this milestone so Ubuntu packages, Python packages, GitHub files, and Hugging Face model files can be downloaded.

Do not use `0.0.0.0/0` for SSH or the FastAPI port. If your local public IP changes, update the security group rule.

## Key Pair

Create or select an EC2 key pair during instance launch. Store the downloaded `.pem` file locally and never copy it into this repository.

From PowerShell, connect with:

```powershell
ssh -i "C:\path\to\your-key.pem" ubuntu@<EC2_PUBLIC_IP>
```

## Install the Application

After connecting to the Ubuntu instance:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git
```

Clone the repository:

```bash
git clone https://github.com/Soominsion/aws-document-intelligence-api.git
cd aws-document-intelligence-api
```

Create the virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Start the API:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Leave the SSH terminal open during the first test. With the minimal dependencies, `/summarize` uses the rule-based fallback.

## Optional ML Inference

The default `requirements.txt` deliberately excludes PyTorch and Transformers. The API, `/health`, `/docs`, and rule-based `/summarize` fallback work without them.

For CPU-only ML inference, increase the EBS volume first if needed, then install:

```bash
source .venv/bin/activate
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-ml.txt
```

The initial long-text summarization request may download Hugging Face model files into `.cache/huggingface`.

## Verify the Deployment

Open these URLs from your computer:

```text
http://<EC2_PUBLIC_IP>:8000/health
http://<EC2_PUBLIC_IP>:8000/docs
```

Expected health response:

```json
{
  "status": "ok",
  "service": "Cloud-native Document Intelligence API",
  "environment": "local"
}
```

Use `/docs` to test `POST /summarize` and `GET /requests/{request_id}`.

## Deployment Result

The initial Ubuntu EC2 deployment has been verified:

- AWS Budget configured before continuing the rollout.
- Security Group allows `SSH 22` and `FastAPI 8000` from `My IP`.
- GitHub repository cloned into EC2.
- Python virtual environment created.
- Minimal runtime dependencies installed.
- FastAPI launched with `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- Remote `/health` and `/docs` access verified through the EC2 public IPv4 address.

Local Hugging Face summarization has been verified. EC2 ML inference remains optional until CPU-only PyTorch or a larger EBS volume is prepared.

## Troubleshooting

### `uvicorn: command not found`

Cause: Uvicorn is not installed in the active virtual environment, or the shell is not using that environment.

Fix:

```bash
source .venv/bin/activate
pip install "uvicorn[standard]"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### `ModuleNotFoundError: No module named 'fastapi'`

Cause: FastAPI is not installed in the active virtual environment.

Fix:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### `ModuleNotFoundError: No module named 'pydantic_settings'`

Cause: `pydantic-settings` is missing from the active virtual environment.

Fix:

```bash
source .venv/bin/activate
pip install pydantic-settings
```

### `No space left on device` During PyTorch Installation

Cause: The default EC2 root disk can be too small for large PyTorch CUDA dependencies and package caches.

Options:

- Install `requirements.txt` first and use the rule-based fallback.
- Install CPU-only PyTorch with the command in `Optional ML Inference`.
- Increase the EBS root volume to `20-30 GiB` before ML experimentation.
- Keep Hugging Face inference optional during this stage.

## Stop the Application

Press `Ctrl+C` in the SSH terminal running Uvicorn.

This stops the API process only. It does not stop EC2 billing.

## Stop or Terminate EC2

After testing:

1. Open the `EC2` console.
2. Select the instance.
3. Choose `Instance state`.
4. Choose `Stop instance` if you plan to continue soon.
5. Choose `Terminate instance` when the experiment is finished.

Stopping an instance avoids EC2 instance usage charges while stopped, but EBS storage can still incur charges. A stopped and restarted instance usually receives a new public IPv4 address.

Terminating permanently removes the instance. Confirm whether its EBS volume is configured for deletion on termination.

## Cost Warnings

- Do not leave the EC2 instance running when you are not testing.
- Public IPv4 addresses can incur charges.
- Do not allocate an Elastic IP unless needed. Elastic IP addresses can incur charges whether used or idle.
- Do not create a NAT Gateway.
- Do not create an ALB or Route 53 configuration during this milestone.
- Review the AWS Budget and Billing dashboard after each session.

## Not Included Yet

- S3 upload or download code
- IAM role configuration
- RDS PostgreSQL
- DynamoDB
- CloudWatch agent setup
- Background service configuration such as `systemd`
- HTTPS, ALB, or Route 53

## Official References

- [Security group rules for different use cases](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules-reference.html)
- [How EC2 instance stop and start works](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/how-ec2-instance-stop-start-works.html)
- [Elastic IP addresses](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html)
- [Burstable performance instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances.html)
- [PyTorch CPU-only installation options](https://docs.pytorch.org/get-started/previous-versions/)
