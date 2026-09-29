"""Candidate verification (spec §14).

Cross-checks candidates against the *other* evidence we hold and records the
result as additional evidence — corroboration (positive) or **contradiction**
(negative). Contradictions are first-class (spec §14): they visibly pull a
candidate's score down and appear in the explanation.

Checks implemented (all from data already gathered — no extra API cost):
- **Country consistency** — does the geocoded candidate's country agree with the
  vision country clues?
- **EXIF proximity** — for non-GPS candidates, does the location sit near the
  photo's embedded GPS point?
- **Geocoding corroboration** — did a named clue resolve to a real place?

Street-view / imagery comparison (spec §14) is a future enhancement behind the
map-provider abstraction; it is intentionally not faked here.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from app.models.analysis import Analysis
from app.models.candidate import Candidate, CandidateEvidence
from app.models.enums import (
    CandidateSource,
    ClueCategory,
    EvidenceCategory,
    EvidenceKind,
)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))


def _add(
    candidate: Candidate,
    category: EvidenceCategory,
    kind: EvidenceKind,
    description: str,
    weight: float,
) -> None:
    candidate.evidence.append(
        CandidateEvidence(category=category, kind=kind, description=description, weight=weight)
    )


class Verifier:
    def verify(self, analysis: Analysis) -> None:
        country_clues = [
            c.value.strip().lower()
            for c in analysis.clues
            if c.category == ClueCategory.COUNTRY and c.value
        ]
        exif = next(
            (c for c in analysis.candidates if c.source == CandidateSource.EXIF), None
        )
        exif_pt = (
            (exif.latitude, exif.longitude)
            if exif and exif.latitude is not None and exif.longitude is not None
            else None
        )

        for cand in analysis.candidates:
            # Country consistency.
            if cand.country and country_clues:
                cc = cand.country.strip().lower()
                if any(cc in cl or cl in cc for cl in country_clues):
                    _add(
                        cand,
                        EvidenceCategory.EXTERNAL_VERIFICATION,
                        EvidenceKind.MATCH,
                        f"Country ({cand.country}) is consistent with detected country clues.",
                        0.1,
                    )
                else:
                    _add(
                        cand,
                        EvidenceCategory.GEOGRAPHY_MATCH,
                        EvidenceKind.CONTRADICTION,
                        f"Candidate country ({cand.country}) conflicts with detected "
                        "country clues.",
                        0.15,
                    )

            # EXIF proximity (non-GPS candidates only).
            if (
                exif_pt is not None
                and cand.source != CandidateSource.EXIF
                and cand.latitude is not None
                and cand.longitude is not None
            ):
                dist = haversine_km(exif_pt[0], exif_pt[1], cand.latitude, cand.longitude)
                if dist <= 50:
                    _add(
                        cand,
                        EvidenceCategory.EXIF_GPS,
                        EvidenceKind.MATCH,
                        "Location agrees with the photo's GPS metadata "
                        f"(~{dist:.0f} km away).",
                        0.3,
                    )
                elif dist >= 500:
                    _add(
                        cand,
                        EvidenceCategory.EXIF_GPS,
                        EvidenceKind.CONTRADICTION,
                        "Location is far from the photo's GPS metadata "
                        f"(~{dist:.0f} km away).",
                        0.1,
                    )

            # Geocoding corroboration for named candidates.
            if cand.location_id is not None and cand.source in (
                CandidateSource.AI,
                CandidateSource.SEARCH,
            ):
                _add(
                    cand,
                    EvidenceCategory.EXTERNAL_VERIFICATION,
                    EvidenceKind.MATCH,
                    "Resolved to a real place via the map provider.",
                    0.05,
                )
