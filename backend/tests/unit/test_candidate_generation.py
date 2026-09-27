"""Candidate generation + scoring tests (spec §12/§13)."""

from __future__ import annotations

from app.models.analysis import Analysis
from app.models.candidate import Candidate, CandidateEvidence
from app.models.clue import VisualClue
from app.models.enums import (
    CandidateSource,
    ClueCategory,
    ClueSource,
    ConfidenceBand,
    EvidenceCategory,
    EvidenceKind,
)
from app.models.image import ImageMetadata, UploadedImage
from app.services.pipeline.candidate_generation import MAX_CANDIDATES, CandidateGenerator
from app.services.pipeline.scoring import confidence_band, score_candidate


def _clue(cat: ClueCategory, value: str, conf: float) -> VisualClue:
    return VisualClue(category=cat, source=ClueSource.AI_VISION, value=value, confidence=conf)


def test_exif_gps_produces_top_candidate() -> None:
    analysis = Analysis()
    analysis.image = UploadedImage(
        storage_key="k", mime_type="image/jpeg", byte_size=1,
    )
    analysis.image.exif = ImageMetadata(
        has_gps=True, gps_valid=True, gps_latitude=24.89, gps_longitude=91.86
    )
    analysis.clues.append(_clue(ClueCategory.LANDMARK, "Some Bridge", 0.6))

    cands = CandidateGenerator().generate(analysis)
    assert cands[0].source == CandidateSource.EXIF
    assert cands[0].rank == 1
    assert cands[0].latitude == 24.89
    assert cands[0].score >= 0.9  # GPS dominates


def test_named_candidates_from_clues_without_gps() -> None:
    analysis = Analysis()
    analysis.image = UploadedImage(storage_key="k", mime_type="image/jpeg", byte_size=1)
    analysis.image.exif = ImageMetadata(has_gps=False)
    analysis.clues.extend(
        [
            _clue(ClueCategory.LANDMARK, "Shahjalal Bridge", 0.8),
            _clue(ClueCategory.GEOGRAPHIC, "Sylhet, Bangladesh", 0.6),
            _clue(ClueCategory.BUSINESS, "ABC Restaurant", 0.5),
        ]
    )
    cands = CandidateGenerator().generate(analysis)
    assert {c.source for c in cands} == {
        CandidateSource.AI,
        CandidateSource.SEARCH,
    }
    # Landmark (0.30*0.8) outranks geography (0.10*0.6) and business (0.15*0.5).
    assert cands[0].name == "Shahjalal Bridge"
    assert all(c.latitude is None for c in cands)  # geocoded later


def test_deduplicates_and_caps() -> None:
    analysis = Analysis()
    analysis.image = UploadedImage(storage_key="k", mime_type="image/jpeg", byte_size=1)
    analysis.image.exif = ImageMetadata(has_gps=False)
    for i in range(10):
        analysis.clues.append(_clue(ClueCategory.LANDMARK, f"Place {i}", 0.5))
    analysis.clues.append(_clue(ClueCategory.LANDMARK, "Place 0", 0.9))  # duplicate name
    cands = CandidateGenerator().generate(analysis)
    names = [c.name for c in cands]
    assert len(cands) <= MAX_CANDIDATES
    assert names.count("Place 0") == 1


def test_scoring_contradiction_lowers_score() -> None:
    cand = Candidate(name="X", source=CandidateSource.AI)
    cand.evidence.append(
        CandidateEvidence(
            category=EvidenceCategory.LANDMARK_MATCH,
            kind=EvidenceKind.MATCH,
            description="matches",
            weight=0.6,
        )
    )
    assert score_candidate(cand) == 0.6
    cand.evidence.append(
        CandidateEvidence(
            category=EvidenceCategory.GEOGRAPHY_MATCH,
            kind=EvidenceKind.CONTRADICTION,
            description="mountain not visible",
            weight=0.3,
        )
    )
    assert abs(score_candidate(cand) - 0.3) < 1e-9


def test_confidence_bands() -> None:
    assert confidence_band(0.95, has_exif_gps=True) == ConfidenceBand.EXACT_GPS
    assert confidence_band(0.95, has_exif_gps=False) == ConfidenceBand.STRONG
    assert confidence_band(0.6, has_exif_gps=False) == ConfidenceBand.PROBABLE
    assert confidence_band(0.4, has_exif_gps=False) == ConfidenceBand.APPROXIMATE
    assert confidence_band(0.2, has_exif_gps=False) == ConfidenceBand.WEAK
    assert confidence_band(0.05, has_exif_gps=False) == ConfidenceBand.UNKNOWN
