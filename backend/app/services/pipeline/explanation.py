"""Human-readable "why we think this" explanation (spec §16).

Derived from the top candidate's supporting evidence so every conclusion the UI
shows is traceable to concrete observations. Contradictions are surfaced too —
the system is transparent about what argues against its answer (spec §14).
"""

from __future__ import annotations

from app.models.analysis import Analysis
from app.models.enums import AnalysisStatus, ConfidenceBand, EvidenceKind


def build_explanation(analysis: Analysis) -> list[str]:
    if analysis.status != AnalysisStatus.COMPLETED:
        return []
    if analysis.confidence_band == ConfidenceBand.UNKNOWN or not analysis.candidates:
        return [
            "We couldn't gather enough reliable evidence to identify where this "
            "photo was taken."
        ]

    top = min(analysis.candidates, key=lambda c: (c.rank is None, c.rank or 0))
    reasons = [ev.description for ev in top.evidence if ev.kind == EvidenceKind.MATCH]
    contradictions = [
        f"However: {ev.description}"
        for ev in top.evidence
        if ev.kind == EvidenceKind.CONTRADICTION
    ]
    return reasons + contradictions
