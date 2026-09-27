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
from app.core.errors import AppError, NotFoundError
from app.core.logging import get_logger
from app.models.analysis import Analysis
from app.models.enums import AnalysisMode, AnalysisStatus
from app.models.image import ImageMetadata, UploadedImage
from app.models.system import ApiUsage
from app.repositories.analysis import AnalysisRepository
from app.services.images.exif import extract_exif
from app.services.images.processing import prepare_for_vision
from app.services.images.validation import inspect_and_validate
from app.services.pipeline.persistence import clues_to_rows
from app.services.pipeline.vision_analysis import VisionAnalyzer
from app.services.providers.registry import get_ai_provider
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

        # 3) Inspect EXIF metadata BEFORE any AI inference (spec §9).
        exif = extract_exif(data)
        analysis.image.exif = ImageMetadata(
            image_id=analysis.image.id,
            has_gps=exif.has_gps,
            gps_latitude=exif.gps_latitude,
            gps_longitude=exif.gps_longitude,
            gps_valid=exif.gps_valid,
            captured_at=exif.captured_at,
            camera_make=exif.camera_make,
            camera_model=exif.camera_model,
            software=exif.software,
            orientation=exif.orientation,
        )
        await self.session.flush()

        # 4) Persist the binary to storage.
        await self.storage.save(key, data, content_type=inspected.mime_type)

        log.info(
            "analysis_created",
            analysis_id=str(analysis.id),
            mode=mode.value,
            mime=inspected.mime_type,
            bytes=inspected.byte_size,
            dims=f"{inspected.width}x{inspected.height}",
            has_gps=exif.has_gps,
        )
        return analysis

    async def run_vision_stage(
        self, analysis: Analysis, *, analyzer: VisionAnalyzer | None = None
    ) -> Analysis:
        """Stage 1 of the pipeline: extract structured visual clues (spec §7).

        Loads the stored image, downsizes it for cost control, calls the vision
        provider, and persists the resulting clue rows + API-usage record. On
        failure the analysis is marked ``failed`` with a structured error rather
        than raising into the caller.
        """
        if analysis.image is None:
            raise NotFoundError("Analysis has no image to analyze.")

        analyzer = analyzer or VisionAnalyzer(get_ai_provider())
        analysis.status = AnalysisStatus.PROCESSING
        await self.session.flush()

        try:
            data = await self.storage.load(analysis.image.storage_key)
            vision_img = prepare_for_vision(data, source_mime=analysis.image.mime_type)
            extraction = await analyzer.extract_clues(
                image_bytes=vision_img.data,
                media_type=vision_img.media_type,
                hint=analysis.hint,
            )
        except AppError as exc:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_code = exc.code
            analysis.error_message = exc.message
            await self.session.flush()
            log.warning("vision_stage_failed", analysis_id=str(analysis.id), code=exc.code)
            return analysis

        rows = clues_to_rows(analysis.id, extraction.clues)
        for row in rows:
            self.session.add(row)
        self.session.add(
            ApiUsage(
                analysis_id=analysis.id,
                provider=extraction.provider,
                operation="vision_analysis",
                model=extraction.model,
                input_tokens=extraction.input_tokens,
                output_tokens=extraction.output_tokens,
            )
        )
        await self.session.flush()

        log.info(
            "vision_stage_complete",
            analysis_id=str(analysis.id),
            clue_count=len(rows),
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
