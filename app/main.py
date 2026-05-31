from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.s3_utils import store_summary_artifacts
from app.summarizer import summarize_text


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
    original_text: str


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Local FastAPI prototype for document summarization and request analytics.",
)

request_store: dict[str, RequestRecord] = {}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }


@app.post("/summarize", response_model=SummarizeResponse)
def summarize_document(payload: SummarizeRequest) -> SummarizeResponse:
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
    record = RequestRecord(
        request_id=request_id,
        status=status,
        summary=summary,
        method=method,
        created_at=created_at,
        input_s3_key=input_s3_key,
        output_s3_key=output_s3_key,
        user_id=payload.user_id,
        original_text=payload.text,
    )
    request_store[request_id] = record

    return SummarizeResponse(**record.model_dump(exclude={"original_text", "user_id"}))


@app.get("/requests/{request_id}", response_model=RequestRecord)
def get_request(request_id: str) -> RequestRecord:
    record = request_store.get(request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return record
