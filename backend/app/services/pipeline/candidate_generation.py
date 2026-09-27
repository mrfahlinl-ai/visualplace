"""Candidate generation (spec §12).

Turns the collected evidence — validated EXIF GPS plus the vision clues — into
multiple candidate locations, each with attached, weighted evidence. We never
return just the first AI guess: EXIF, landmarks, regions, and business/sign text
all seed candidates, capped for cost (spec §25) and de-duplicated by name.

Named candidates (landmark/region/business) start without coordinates; they are
geocoded against the map/place provider in Phase 7 and re-scored after
verification in Phase 8.
"""

from __future__ import annotations

from app.models.analysis import Analysis
from app.models.candidate import Candidate, CandidateEvidence
from app.models.enums import (
    CandidateSource,
    ClueCategory,
    EvidenceCategory,
    EvidenceKind,
)
from app.services.pipeline.scoring import base_weight, score_candidate

# Cap on candidates carried forward to (expensive) verification (spec §25).
MAX_CANDIDATES = 6


def _evidence(category: EvidenceCategory, description: str, weight: float) -> CandidateEvidence:
    return CandidateEvidence(
        category=category,
        kind=EvidenceKind.MATCH,
        description=description,
        weight=weight,
    )


class CandidateGenerator:
    def generate(self, analysis: Analysis) -> list[Candidate]:
        candidates: list[Candidate] = []

        # 1) EXIF GPS — the strongest signal when present and validated (spec §9).
        exif = analysis.image.exif if analysis.image else None
        if exif and exif.has_gps and exif.gps_valid and exif.gps_latitude is not None:
            gps = Candidate(
                name="Photo GPS location",
                latitude=exif.gps_latitude,
                longitude=exif.gps_longitude,
                source=CandidateSource.EXIF,
            )
            gps.evidence.append(
                _evidence(
                    EvidenceCategory.EXIF_GPS,
                    "GPS coordinates embedded in the photo's EXIF metadata.",
                    base_weight(EvidenceCategory.EXIF_GPS),
                )
            )
            candidates.append(gps)

        # 2) Clue-derived candidates (named; geocoded later).
        seen: set[str] = set()

        def add_named(
            name: str,
            source: CandidateSource,
            category: EvidenceCategory,
            confidence: float | None,
            description: str,
        ) -> None:
            key = name.strip().lower()
            if not key or key in seen:
                return
            seen.add(key)
            weight = base_weight(category) * (confidence if confidence is not None else 0.5)
            cand = Candidate(name=name.strip(), source=source)
            cand.evidence.append(_evidence(category, description, weight))
            candidates.append(cand)

        for clue in analysis.clues:
            match clue.category:
                case ClueCategory.LANDMARK:
                    add_named(
                        clue.value,
                        CandidateSource.AI,
                        EvidenceCategory.LANDMARK_MATCH,
                        clue.confidence,
                        f"AI identified a possible landmark: {clue.value}.",
                    )
                case ClueCategory.GEOGRAPHIC:
                    add_named(
                        clue.value,
                        CandidateSource.AI,
                        EvidenceCategory.GEOGRAPHY_MATCH,
                        clue.confidence,
                        f"Geographic/region inference: {clue.value}.",
                    )
                case ClueCategory.BUSINESS:
                    add_named(
                        clue.value,
                        CandidateSource.SEARCH,
                        EvidenceCategory.BUSINESS_MATCH,
                        clue.confidence,
                        f"Business identified in image: {clue.value}.",
                    )
                case _:
                    continue

        # Provisional score + rank; refined after verification (Phase 8).
        for cand in candidates:
            cand.score = score_candidate(cand)
        candidates.sort(key=lambda c: c.score, reverse=True)
        candidates = candidates[:MAX_CANDIDATES]
        for i, cand in enumerate(candidates, start=1):
            cand.rank = i

        return candidates
