"""Analysis API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AnalysisMode, AnalysisStatus, ConfidenceBand


class ImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mime_type: str
    byte_size: int
    width: int | None = None
    height: int | None = None


class AnalysisError(BaseModel):
    code: str
    message: str


class AnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mode: AnalysisMode
    status: AnalysisStatus
    hint: str | None = None
    confidence: float | None = None
    confidence_band: ConfidenceBand | None = None
    created_at: datetime
    image: ImageRead | None = None
    error: AnalysisError | None = None


class AnalyzeCreateParams(BaseModel):
    """Non-file fields for POST /api/analyze (sent as multipart form fields)."""

    mode: AnalysisMode = AnalysisMode.IDENTIFY
    # Optional user hint — a search constraint, treated as unverified (spec §20).
    hint: str | None = Field(default=None, max_length=280)
