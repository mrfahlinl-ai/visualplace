"""Analysis endpoints (spec §27).

    POST   /api/analyze          create an analysis from an uploaded image
    GET    /api/analyze/{id}     fetch an analysis
    DELETE /api/analyze/{id}     privacy delete

The pipeline that populates clues/candidates/result runs in later phases; for
now a created analysis is persisted as ``pending``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ImageTooLargeError
from app.core.ratelimit import RateLimiter
from app.db.session import get_session
from app.models.enums import AnalysisMode
from app.schemas.analysis import AnalysisError, AnalysisRead
from app.services.analysis_service import AnalysisService
from app.services.pipeline.explanation import build_explanation

router = APIRouter(prefix="/analyze", tags=["analyze"])

_upload_limiter = RateLimiter(scope="analyze")
_verify_limiter = RateLimiter(scope="analyze_verify")


def _to_read(analysis) -> AnalysisRead:
    read = AnalysisRead.model_validate(analysis)
    read.explanation = build_explanation(analysis)
    if analysis.error_code:
        read.error = AnalysisError(
            code=analysis.error_code,
            message=analysis.error_message or "Analysis failed.",
        )
    return read


@router.post(
    "",
    response_model=AnalysisRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an analysis from an uploaded image",
)
async def create_analysis(
    file: UploadFile = File(..., description="Image to analyze"),
    mode: AnalysisMode = Form(AnalysisMode.IDENTIFY),
    hint: str | None = Form(None, max_length=280),
    session: AsyncSession = Depends(get_session),
    _rl: None = Depends(_upload_limiter),
) -> AnalysisRead:
    # Read with a hard cap so an oversized stream can't exhaust memory.
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise ImageTooLargeError("Image exceeds the maximum allowed size.")

    service = AnalysisService(session)
    analysis = await service.create(
        data=data,
        declared_content_type=file.content_type,
        mode=mode,
        hint=hint,
    )
    return _to_read(analysis)


@router.post(
    "/{analysis_id}/verify",
    response_model=AnalysisRead,
    summary="Run the evidence pipeline for an analysis",
)
async def verify_analysis(
    analysis_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _rl: None = Depends(_verify_limiter),
) -> AnalysisRead:
    service = AnalysisService(session)
    analysis = await service.get(analysis_id)
    result = await service.run_full_pipeline(analysis)
    return _to_read(result)


@router.get("/{analysis_id}", response_model=AnalysisRead, summary="Get an analysis")
async def get_analysis(
    analysis_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> AnalysisRead:
    analysis = await AnalysisService(session).get(analysis_id)
    return _to_read(analysis)


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an analysis (privacy)",
)
async def delete_analysis(
    analysis_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    await AnalysisService(session).delete(analysis_id)
