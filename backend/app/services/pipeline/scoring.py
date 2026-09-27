"""Transparent candidate scoring (spec §13).

Design principle: a candidate's score is the **sum of its evidence**, where each
piece of evidence contributes a signed weight (matches positive, contradictions
negative). This keeps the number explainable — the UI can show exactly which
observations produced the confidence, and contradictions visibly pull it down
(spec §14). No fabricated mathematical certainty (spec §13).

The base weights below are deliberate, tunable defaults — not claims of precision.
EXIF GPS dominates because embedded coordinates are direct evidence, not
inference; everything else is weighed against corroboration and contradiction.
"""

from __future__ import annotations

from app.models.candidate import Candidate
from app.models.enums import ConfidenceBand, EvidenceCategory, EvidenceKind

# Base contribution of a single supporting piece of evidence, before it is
# scaled by the underlying clue's confidence.
EVIDENCE_BASE_WEIGHTS: dict[EvidenceCategory, float] = {
    EvidenceCategory.EXIF_GPS: 0.95,
    EvidenceCategory.LANDMARK_MATCH: 0.30,
    EvidenceCategory.TEXT_MATCH: 0.20,
    EvidenceCategory.BUSINESS_MATCH: 0.15,
    EvidenceCategory.ARCHITECTURE_MATCH: 0.10,
    EvidenceCategory.ROAD_MATCH: 0.10,
    EvidenceCategory.GEOGRAPHY_MATCH: 0.10,
    EvidenceCategory.VISUAL_MATCH: 0.10,
    EvidenceCategory.EXTERNAL_VERIFICATION: 0.15,
}


def base_weight(category: EvidenceCategory) -> float:
    return EVIDENCE_BASE_WEIGHTS.get(category, 0.05)


def score_candidate(candidate: Candidate) -> float:
    """Sum signed evidence weights into a score clamped to [0, 1]."""
    total = 0.0
    for ev in candidate.evidence:
        w = ev.weight if ev.weight is not None else base_weight(ev.category)
        total += w if ev.kind == EvidenceKind.MATCH else -abs(w)
    return max(0.0, min(1.0, total))


def confidence_band(score: float, *, has_exif_gps: bool) -> ConfidenceBand:
    """Map a score to a user-facing band (spec §1, §33).

    We never label something ``STRONG``/``EXACT_GPS`` on a weak score. Only
    validated EXIF GPS earns ``EXACT_GPS``; below the ``PROBABLE`` line the UI
    must present an area, not a pin (spec §17/§33).
    """
    if has_exif_gps and score >= 0.9:
        return ConfidenceBand.EXACT_GPS
    if score >= 0.8:
        return ConfidenceBand.STRONG
    if score >= 0.55:
        return ConfidenceBand.PROBABLE
    if score >= 0.35:
        return ConfidenceBand.APPROXIMATE
    if score >= 0.15:
        return ConfidenceBand.WEAK
    return ConfidenceBand.UNKNOWN
