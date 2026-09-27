"""Map structured vision output to ORM rows."""

from __future__ import annotations

import uuid

from app.models.clue import VisualClue
from app.models.enums import ClueCategory, ClueSource
from app.services.pipeline.schemas import Observation, VisionClues


def _obs_rows(
    analysis_id: uuid.UUID, category: ClueCategory, items: list[Observation]
) -> list[VisualClue]:
    rows: list[VisualClue] = []
    for obs in items:
        raw = obs.observation if category == ClueCategory.SIGN_TEXT else None
        rows.append(
            VisualClue(
                analysis_id=analysis_id,
                category=category,
                source=ClueSource.AI_VISION,
                value=obs.observation,
                confidence=obs.confidence,
                raw_text=raw,
            )
        )
    return rows


def clues_to_rows(analysis_id: uuid.UUID, clues: VisionClues) -> list[VisualClue]:
    """Flatten a :class:`VisionClues` payload into queryable clue rows."""
    rows: list[VisualClue] = []

    if clues.scene_type:
        rows.append(
            VisualClue(
                analysis_id=analysis_id,
                category=ClueCategory.SCENE_TYPE,
                source=ClueSource.AI_VISION,
                value=clues.scene_type,
            )
        )

    mapping: list[tuple[ClueCategory, list[Observation]]] = [
        (ClueCategory.COUNTRY, clues.country_clues),
        (ClueCategory.CITY, clues.city_clues),
        (ClueCategory.BUSINESS, clues.businesses),
        (ClueCategory.SIGN_TEXT, clues.sign_text),
        (ClueCategory.LANGUAGE, clues.languages),
        (ClueCategory.ROAD, clues.road_features),
        (ClueCategory.ARCHITECTURE, clues.architecture),
        (ClueCategory.NATURAL, clues.natural_features),
        (ClueCategory.VEHICLE, clues.vehicles),
        (ClueCategory.LICENSE_PLATE, clues.license_plate_style),
        (ClueCategory.GEOGRAPHIC, clues.geographic_clues),
        (ClueCategory.GEOGRAPHIC, clues.possible_regions),
    ]
    for category, items in mapping:
        rows.extend(_obs_rows(analysis_id, category, items))

    for lm in clues.landmarks:
        rows.append(
            VisualClue(
                analysis_id=analysis_id,
                category=ClueCategory.LANDMARK,
                source=ClueSource.AI_VISION,
                value=lm.name,
                confidence=lm.confidence,
                extra={"evidence": lm.evidence},
            )
        )

    if clues.visual_description:
        rows.append(
            VisualClue(
                analysis_id=analysis_id,
                category=ClueCategory.OTHER,
                source=ClueSource.AI_VISION,
                value=clues.visual_description,
            )
        )

    return rows
