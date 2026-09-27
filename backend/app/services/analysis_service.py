"""Analysis orchestration service.

Phase 3 scope: create an analysis from an uploaded image (validate → store →
persist), fetch it, and delete it (privacy). The evidence pipeline (AI, EXIF,
OCR, candidates, scoring) is layered on in later phases and will advance the
analysis ``status`` from ``pending``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.models.analysis import Analysis
from app.models.enums import AnalysisMode, AnalysisStatus
from app.models.image import UploadedImage
from app.repositories.analysis import AnalysisRepository
from app.services.images.validation import inspect_and_validate
from app.services.storage.registry import get_storage

log = get_logger(__name__)


def _storage_key(analysis_id: uuid.UUID, mime_type: str) -> str:
    ext = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/heic": "heic",
        "image/heif": "heif",
    }.get(mime_type, "bin")
    # App-generated key only — user filename is never used.
    return f"analyses/{analysis_id}/original.{ext}"


class AnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AnalysisRepository(session)
        self.storage = get_storage()

    async def create(
        self,
        *,
        data: bytes,
        declared_content_type: str | None,
        mode: AnalysisMode,
        hint: str | None,
    ) -> Analysis:
        # 1) Validate + inspect (raises AppError on any violation).
        inspected = inspect_and_validate(
            data=data, declared_content_type=declared_content_type
        )

        # 2) Create the analysis + image records.
        expires_at = (
            datetime.now(UTC) + timedelta(hours=settings.retention_hours)
            if settings.retention_hours > 0
            else datetime.now(UTC)
        )
        analysis = Analysis(
            mode=mode,
            status=AnalysisStatus.PENDING,
            hint=hint,
            expires_at=expires_at,
        )
        await self.repo.add(analysis)  # flush to obtain id

        key = _storage_key(analysis.id, inspected.mime_type)
        analysis.image = UploadedImage(
            analysis_id=analysis.id,
            storage_provider=self.storage.name,
            storage_key=key,
            mime_type=inspected.mime_type,
            byte_size=inspected.byte_size,
            width=inspected.width,
            height=inspected.height,
            sha256=inspected.sha256,
            phash=inspected.phash,
            retained=settings.retain_images,
        )
        await self.session.flush()

        # 3) Persist the binary to storage.
        await self.storage.save(key, data, content_type=inspected.mime_type)

        log.info(
            "analysis_created",
            analysis_id=str(analysis.id),
            mode=mode.value,
            mime=inspected.mime_type,
            bytes=inspected.byte_size,
            dims=f"{inspected.width}x{inspected.height}",
        )
        return analysis

    async def get(self, analysis_id: uuid.UUID) -> Analysis:
        analysis = await self.repo.get_with_relations(analysis_id)
        if analysis is None or analysis.status == AnalysisStatus.DELETED:
            raise NotFoundError("Analysis not found.")
        return analysis

    async def delete(self, analysis_id: uuid.UUID) -> None:
        """Privacy delete (spec §21): remove the stored image, soft-delete the row."""
        analysis = await self.repo.get_with_relations(analysis_id)
        if analysis is None or analysis.status == AnalysisStatus.DELETED:
            raise NotFoundError("Analysis not found.")

        if analysis.image is not None:
            await self.storage.delete(analysis.image.storage_key)
            analysis.image.deleted_at = datetime.now(UTC)

        analysis.status = AnalysisStatus.DELETED
        analysis.deleted_at = datetime.now(UTC)
        await self.session.flush()

        log.info("analysis_deleted", analysis_id=str(analysis_id))
