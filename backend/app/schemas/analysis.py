"""Analysis API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AnalysisMode,
    AnalysisStatus,
    CandidateSource,
    ConfidenceBand,
    EvidenceCategory,
    EvidenceKind,
)


class ExifRead(BaseModel):
    """EXIF summary surfaced to the UI (spec §9). Never claims GPS it doesn't have."""

    model_config = ConfigDict(from_attributes=True)

    has_gps: bool
    gps_valid: bool | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    captured_at: datetime | None = None
    camera_make: str | None = None
    camera_model: str | None = None


class ImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mime_type: str
    byte_size: int
    width: int | None = None
    height: int | None = None
    exif: ExifRead | None = None


class AnalysisError(BaseModel):
    code: str
    message: str


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: EvidenceCategory
    kind: EvidenceKind
    description: str
    weight: float | None = None


class CandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    latitude: float | None = None
    longitude: float | None = None
    city: str | None = None
    country: str | None = None
    country_code: str | None = None
    place_type: str | None = None
    source: CandidateSource
    score: float
    rank: int | None = None
    radius_m: float | None = None
    evidence: list[EvidenceRead] = Field(default_factory=list)


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
    candidates: list[CandidateRead] = Field(default_factory=list)
    error: AnalysisError | None = None


class AnalyzeCreateParams(BaseModel):
    """Non-file fields for POST /api/analyze (sent as multipart form fields)."""

    mode: AnalysisMode = AnalysisMode.IDENTIFY
    # Optional user hint — a search constraint, treated as unverified (spec §20).
    hint: str | None = Field(default=None, max_length=280)
