"""Analysis orchestration service.

Owns the analysis lifecycle: create from an uploaded image (validate → store →
EXIF → persist), fetch, privacy delete, and the evidence pipeline stages —
vision → candidates → geocoding → verify/finalize — plus a `run_full_pipeline`
convenience that chains them. Stages accept injectable providers so they run in
tests without network or API keys.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError, NotFoundError
from app.core.logging import get_logger
from app.models.analysis import Analysis
from app.models.enums import AnalysisMode, AnalysisStatus, CandidateSource, ConfidenceBand
from app.models.image import ImageMetadata, UploadedImage
from app.models.location import Location
from app.models.system import ApiUsage
from app.repositories.analysis import AnalysisRepository
from app.services.images.exif import extract_exif
from app.services.images.processing import prepare_for_vision
from app.services.images.validation import inspect_and_validate
from app.services.pipeline.candidate_generation import CandidateGenerator
from app.services.pipeline.geocoding import GeocodingStage
from app.services.pipeline.persistence import clues_to_rows
from app.services.pipeline.scoring import confidence_band, score_candidate
from app.services.pipeline.verification import Verifier
from app.services.pipeline.vision_analysis import VisionAnalyzer
from app.services.providers.base import MapProvider
from app.services.providers.registry import get_ai_provider, get_map_provider
from app.services.storage.registry import get_storage

log = get_logger(__name__)

# Approximate-area radius (metres) by band when the location is uncertain (§17).
_BAND_RADIUS_M: dict[ConfidenceBand, float] = {
    ConfidenceBand.PROBABLE: 5_000,
    ConfidenceBand.APPROXIMATE: 25_000,
    ConfidenceBand.WEAK: 100_000,
}


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
        # Reload with relations so the response serializes without triggering
        # async lazy-loads (empty clues/candidates included explicitly).
        reloaded = await self.repo.get_with_relations(analysis.id)
        assert reloaded is not None
        return reloaded

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
        # Append to the relationship so the in-memory collection stays consistent
        # with the DB (a later reload would otherwise keep a stale empty list).
        for row in rows:
            analysis.clues.append(row)
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

    async def run_candidate_stage(self, analysis: Analysis) -> Analysis:
        """Stage 2: generate scored candidate locations from the evidence (spec §12).

        Reloads relations so freshly-persisted clues/EXIF are visible, then
        persists candidates with their evidence.
        """
        loaded = await self.repo.get_with_relations(analysis.id)
        if loaded is None:
            raise NotFoundError("Analysis not found.")

        candidates = CandidateGenerator().generate(loaded)
        for cand in candidates:
            loaded.candidates.append(cand)  # keeps the collection consistent
        await self.session.flush()

        log.info(
            "candidate_stage_complete",
            analysis_id=str(loaded.id),
            candidate_count=len(candidates),
        )
        return loaded

    async def run_geocoding_stage(
        self, analysis: Analysis, *, map_provider: MapProvider | None = None
    ) -> Analysis:
        """Stage 3: resolve named candidates to real coordinates (spec §7)."""
        loaded = await self.repo.get_with_relations(analysis.id)
        if loaded is None:
            raise NotFoundError("Analysis not found.")

        provider = map_provider or get_map_provider()
        await GeocodingStage(self.session, provider).resolve(list(loaded.candidates))
        await self.session.flush()

        log.info(
            "geocoding_stage_complete",
            analysis_id=str(loaded.id),
            located=sum(1 for c in loaded.candidates if c.latitude is not None),
        )
        return loaded

    async def _ensure_location(self, candidate) -> Location | None:
        """Return the candidate's Location, creating one from its coords if needed."""
        if candidate.location_id is not None:
            return await self.session.get(Location, candidate.location_id)
        if candidate.latitude is None or candidate.longitude is None:
            return None
        loc = Location(
            name=candidate.name,
            latitude=candidate.latitude,
            longitude=candidate.longitude,
            city=candidate.city,
            country=candidate.country,
            country_code=candidate.country_code,
            place_type=candidate.place_type,
            provider=candidate.source.value,
        )
        self.session.add(loc)
        await self.session.flush()
        candidate.location_id = loc.id
        return loc

    async def run_finalize_stage(self, analysis: Analysis) -> Analysis:
        """Stage 4: verify, re-score, pick the result, set confidence (spec §13/§14/§33).

        Comfortable with "unable to determine": a below-threshold top score yields
        band UNKNOWN and no final location — never a misleading pin (spec §17/§33).
        """
        loaded = await self.repo.get_with_relations(analysis.id)
        if loaded is None:
            raise NotFoundError("Analysis not found.")

        Verifier().verify(loaded)
        for cand in loaded.candidates:
            cand.score = score_candidate(cand)
        ranked = sorted(loaded.candidates, key=lambda c: c.score, reverse=True)
        for i, cand in enumerate(ranked, start=1):
            cand.rank = i

        top = ranked[0] if ranked else None
        if top is None or top.score < 0.15:
            loaded.confidence = top.score if top else 0.0
            loaded.confidence_band = ConfidenceBand.UNKNOWN
            loaded.final_location_id = None
        else:
            band = confidence_band(
                top.score, has_exif_gps=(top.source == CandidateSource.EXIF)
            )
            loaded.confidence = top.score
            loaded.confidence_band = band
            top.radius_m = _BAND_RADIUS_M.get(band)
            location = await self._ensure_location(top)
            loaded.final_location_id = location.id if location else None

        loaded.status = AnalysisStatus.COMPLETED
        await self.session.flush()
        log.info(
            "finalize_complete",
            analysis_id=str(loaded.id),
            band=loaded.confidence_band.value if loaded.confidence_band else None,
            confidence=round(loaded.confidence or 0.0, 3),
        )
        return loaded

    async def run_full_pipeline(
        self,
        analysis: Analysis,
        *,
        analyzer: VisionAnalyzer | None = None,
        map_provider: MapProvider | None = None,
    ) -> Analysis:
        """Run the whole evidence pipeline: vision → candidates → geocode → finalize."""
        result = await self.run_vision_stage(analysis, analyzer=analyzer)
        if result.status == AnalysisStatus.FAILED:
            return result
        await self.run_candidate_stage(analysis)
        await self.run_geocoding_stage(analysis, map_provider=map_provider)
        return await self.run_finalize_stage(analysis)

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
