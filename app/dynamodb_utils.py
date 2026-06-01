import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class DynamoDBLookupError(Exception):
    """Raised when an enabled DynamoDB lookup cannot be completed."""


def store_request_status(item: dict[str, Any]) -> bool:
    if not settings.enable_dynamodb:
        return False

    if not settings.dynamodb_table_name:
        logger.warning("DynamoDB status tracking is enabled but no table is configured.")
        return False

    try:
        import boto3

        table = boto3.resource(
            "dynamodb",
            region_name=settings.aws_region,
        ).Table(settings.dynamodb_table_name)
        table.put_item(Item=item)
        return True
    except Exception:
        logger.warning("DynamoDB status write failed; continuing without status tracking.")
        return False


def get_request_status(request_id: str) -> dict[str, Any] | None:
    if not settings.dynamodb_table_name:
        raise DynamoDBLookupError("DynamoDB table is not configured.")

    try:
        import boto3

        table = boto3.resource(
            "dynamodb",
            region_name=settings.aws_region,
        ).Table(settings.dynamodb_table_name)
        response = table.get_item(Key={"request_id": request_id})
        return response.get("Item")
    except Exception as exc:
        logger.warning("DynamoDB status lookup failed.")
        raise DynamoDBLookupError("DynamoDB status lookup failed.") from exc
