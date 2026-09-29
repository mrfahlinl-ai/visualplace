"""Verification cross-checks (spec §14)."""

from __future__ import annotations

from app.models.analysis import Analysis
from app.models.candidate import Candidate
from app.models.clue import VisualClue
from app.models.enums import (
    CandidateSource,
    ClueCategory,
    ClueSource,
    EvidenceCategory,
    EvidenceKind,
)
from app.services.pipeline.verification import Verifier, haversine_km


def test_haversine_reasonable() -> None:
    # Sylhet → Dhaka ~ 200 km.
    d = haversine_km(24.8949, 91.8687, 23.8103, 90.4125)
    assert 180 < d < 230


def _cats(cand: Candidate, kind: EvidenceKind) -> set[EvidenceCategory]:
    return {ev.category for ev in cand.evidence if ev.kind == kind}


def test_exif_proximity_and_country_checks() -> None:
    analysis = Analysis()
    analysis.clues.append(
        VisualClue(
            category=ClueCategory.COUNTRY, source=ClueSource.AI_VISION, value="Bangladesh"
        )
    )
    exif = Candidate(
        name="Photo GPS location", source=CandidateSource.EXIF,
        latitude=24.8949, longitude=91.8687,
    )
    near = Candidate(
        name="Shahjalal Bridge", source=CandidateSource.AI,
        latitude=24.90, longitude=91.87, country="Bangladesh", location_id=None,
    )
    far = Candidate(
        name="Eiffel Tower", source=CandidateSource.AI,
        latitude=48.8584, longitude=2.2945, country="France",
    )
    analysis.candidates.extend([exif, near, far])

    Verifier().verify(analysis)

    # Near candidate: agrees with GPS + country.
    assert EvidenceCategory.EXIF_GPS in _cats(near, EvidenceKind.MATCH)
    assert EvidenceCategory.EXTERNAL_VERIFICATION in _cats(near, EvidenceKind.MATCH)

    # Far candidate: contradicted by both GPS distance and country mismatch.
    assert EvidenceCategory.EXIF_GPS in _cats(far, EvidenceKind.CONTRADICTION)
    assert EvidenceCategory.GEOGRAPHY_MATCH in _cats(far, EvidenceKind.CONTRADICTION)
