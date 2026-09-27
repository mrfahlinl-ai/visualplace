"""Schema/model + repository tests against an in-memory SQLite engine.

Verifies the ORM metadata is coherent (all tables/relationships build and
create), and exercises the analysis repository end-to-end (insert an analysis
with an image, EXIF, a clue, and a scored candidate + evidence; read it back
with relations loaded).
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base_class import Base
from app.models import (
    Analysis,
    Candidate,
    CandidateEvidence,
    ImageMetadata,
    Location,
    UploadedImage,
    VisualClue,
)
from app.models.enums import (
    AnalysisMode,
    AnalysisStatus,
    CandidateSource,
    ClueCategory,
    ClueSource,
    ConfidenceBand,
    EvidenceCategory,
    EvidenceKind,
)
from app.repositories.analysis import AnalysisRepository


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


async def test_metadata_has_all_tables() -> None:
    expected = {
        "users",
        "analyses",
        "uploaded_images",
        "image_metadata",
        "visual_clues",
        "locations",
        "candidates",
        "candidate_evidence",
        "api_usage",
        "search_cache",
        "audit_logs",
    }
    assert expected <= set(Base.metadata.tables.keys())


async def test_analysis_graph_roundtrip(session) -> None:
    repo = AnalysisRepository(session)

    analysis = Analysis(mode=AnalysisMode.FIND_EXACT, status=AnalysisStatus.PENDING)
    analysis.image = UploadedImage(
        storage_key="uploads/x.jpg",
        mime_type="image/jpeg",
        byte_size=12345,
        width=1600,
        height=1200,
        sha256="deadbeef",
    )
    analysis.image.exif = ImageMetadata(has_gps=False)
    analysis.clues.append(
        VisualClue(
            category=ClueCategory.SIGN_TEXT,
            source=ClueSource.OCR,
            value="Shahjalal",
            confidence=0.72,
            raw_text="Shahjalal",
            language="bn",
        )
    )
    candidate = Candidate(
        name="Shahjalal Bridge",
        latitude=24.8949,
        longitude=91.8687,
        city="Sylhet",
        country="Bangladesh",
        country_code="BD",
        source=CandidateSource.AI,
        score=0.87,
        rank=1,
    )
    candidate.evidence.append(
        CandidateEvidence(
            category=EvidenceCategory.LANDMARK_MATCH,
            kind=EvidenceKind.MATCH,
            description="Distinctive bridge silhouette matches",
            weight=0.3,
        )
    )
    analysis.candidates.append(candidate)

    await repo.add(analysis)
    await session.commit()

    loaded = await repo.get_with_relations(analysis.id)
    assert loaded is not None
    assert loaded.mode == AnalysisMode.FIND_EXACT
    assert loaded.image is not None
    assert loaded.image.exif is not None and loaded.image.exif.has_gps is False
    assert len(loaded.clues) == 1
    assert loaded.clues[0].category == ClueCategory.SIGN_TEXT
    assert len(loaded.candidates) == 1
    assert loaded.candidates[0].rank == 1
    assert loaded.candidates[0].score == pytest.approx(0.87)


async def test_confidence_band_enum_persists(session) -> None:
    a = Analysis(status=AnalysisStatus.COMPLETED, confidence_band=ConfidenceBand.APPROXIMATE)
    session.add(a)
    await session.commit()
    fetched = await session.get(Analysis, a.id)
    assert fetched is not None
    assert fetched.confidence_band == ConfidenceBand.APPROXIMATE


async def test_location_model(session) -> None:
    loc = Location(
        name="Sylhet", latitude=24.9, longitude=91.87, country_code="BD", provider="osm"
    )
    session.add(loc)
    await session.commit()
    assert (await session.get(Location, loc.id)) is not None
