import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")


def store_summary_artifacts(
    *,
    user_id: str,
    request_id: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
) -> tuple[str | None, str | None]:
    if not settings.enable_s3:
        return None, None

    if not settings.s3_bucket_name:
        logger.warning("S3 artifact storage is enabled but no bucket is configured.")
        return None, None

    input_key = f"inputs/{user_id}/{request_id}.json"
    output_key = f"outputs/{user_id}/{request_id}.json"
    s3_client = None
    input_uploaded = False

    try:
        import boto3

        s3_client = boto3.client("s3", region_name=settings.aws_region)
        s3_client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=input_key,
            Body=_json_bytes(input_payload),
            ContentType="application/json",
        )
        input_uploaded = True
        s3_client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=output_key,
            Body=_json_bytes(output_payload),
            ContentType="application/json",
        )
        return input_key, output_key
    except Exception:
        logger.warning("S3 artifact upload failed; continuing with in-memory storage only.")
        if s3_client is not None and input_uploaded:
            try:
                s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=input_key)
            except Exception:
                logger.warning("S3 partial-upload cleanup failed.")
        return None, None
