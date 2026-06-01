import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.dynamodb_utils import (
    DynamoDBLookupError,
    get_request_status,
    store_request_status,
)
from app.models import RequestMetadata
from app.s3_utils import store_summary_artifacts
from app.summarizer import summarize_text

logger = logging.getLogger(__name__)


class RequestStatus(str, Enum):
    completed = "completed"
    failed = "failed"


class SummarizeRequest(BaseModel):
    user_id: str = Field(
        default="anonymous",
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
        description="Optional safe identifier used to group S3 artifacts.",
    )
    text: str = Field(..., min_length=1, description="Text content to summarize.")


class SummarizeResponse(BaseModel):
    request_id: str
    status: RequestStatus
    summary: str
    method: str
    created_at: datetime
    input_s3_key: str | None = None
    output_s3_key: str | None = None


class RequestRecord(SummarizeResponse):
    user_id: str
    original_text: str | None = None


class RequestStatusRecord(BaseModel):
    request_id: str
    user_id: str
    status: RequestStatus
    method: str
    created_at: str
    input_s3_key: str | None = None
    output_s3_key: str | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Local FastAPI prototype for document summarization and request analytics.",
    lifespan=lifespan,
)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }


@app.post("/summarize", response_model=SummarizeResponse)
def summarize_document(
    payload: SummarizeRequest,
    db: Session = Depends(get_db),
) -> SummarizeResponse:
    request_id = str(uuid4())
    created_at = datetime.now(timezone.utc)

    summary, method = summarize_text(payload.text)
    status = RequestStatus.completed
    input_s3_key, output_s3_key = store_summary_artifacts(
        user_id=payload.user_id,
        request_id=request_id,
        input_payload={
            "request_id": request_id,
            "user_id": payload.user_id,
            "text": payload.text,
            "created_at": created_at,
        },
        output_payload={
            "request_id": request_id,
            "user_id": payload.user_id,
            "status": status.value,
            "summary": summary,
            "method": method,
            "created_at": created_at,
        },
    )
    db_record = RequestMetadata(
        request_id=request_id,
        status=status.value,
        summary=summary,
        method=method,
        created_at=created_at,
        input_s3_key=input_s3_key,
        output_s3_key=output_s3_key,
        user_id=payload.user_id,
    )
    try:
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
    except SQLAlchemyError:
        db.rollback()
        logger.warning("Database request persistence failed.")
        raise HTTPException(
            status_code=503,
            detail="Request metadata persistence failed",
        )

    store_request_status(
        {
            "request_id": db_record.request_id,
            "user_id": db_record.user_id,
            "status": db_record.status,
            "method": db_record.method,
            "created_at": db_record.created_at.isoformat(),
            "input_s3_key": db_record.input_s3_key,
            "output_s3_key": db_record.output_s3_key,
        }
    )

    return SummarizeResponse(
        request_id=db_record.request_id,
        status=RequestStatus(db_record.status),
        summary=db_record.summary,
        method=db_record.method,
        created_at=db_record.created_at,
        input_s3_key=db_record.input_s3_key,
        output_s3_key=db_record.output_s3_key,
    )


@app.get("/requests/{request_id}", response_model=RequestRecord)
def get_request(
    request_id: str,
    db: Session = Depends(get_db),
) -> RequestRecord:
    try:
        db_record = (
            db.query(RequestMetadata)
            .filter(RequestMetadata.request_id == request_id)
            .first()
        )
    except SQLAlchemyError:
        logger.warning("Database request lookup failed.")
        raise HTTPException(status_code=503, detail="Request lookup failed")

    if db_record is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return RequestRecord(
        request_id=db_record.request_id,
        user_id=db_record.user_id,
        status=RequestStatus(db_record.status),
        summary=db_record.summary,
        method=db_record.method,
        created_at=db_record.created_at,
        input_s3_key=db_record.input_s3_key,
        output_s3_key=db_record.output_s3_key,
        original_text=None,
    )


@app.get("/status/{request_id}", response_model=RequestStatusRecord)
def get_status(request_id: str) -> RequestStatusRecord:
    if not settings.enable_dynamodb:
        raise HTTPException(
            status_code=503,
            detail="DynamoDB status tracking is disabled",
        )

    try:
        item = get_request_status(request_id)
    except DynamoDBLookupError:
        raise HTTPException(
            status_code=503,
            detail="Request status lookup is unavailable",
        )

    if item is None:
        raise HTTPException(status_code=404, detail="Request status not found")

    return RequestStatusRecord(**item)
