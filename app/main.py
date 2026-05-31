from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.summarizer import summarize_text


class RequestStatus(str, Enum):
    completed = "completed"
    failed = "failed"


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text content to summarize.")


class SummarizeResponse(BaseModel):
    request_id: str
    status: RequestStatus
    summary: str
    method: str
    created_at: datetime


class RequestRecord(SummarizeResponse):
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
    record = RequestRecord(
        request_id=request_id,
        status=RequestStatus.completed,
        summary=summary,
        method=method,
        created_at=created_at,
        original_text=payload.text,
    )
    request_store[request_id] = record

    return SummarizeResponse(**record.model_dump(exclude={"original_text"}))


@app.get("/requests/{request_id}", response_model=RequestRecord)
def get_request(request_id: str) -> RequestRecord:
    record = request_store.get(request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return record
