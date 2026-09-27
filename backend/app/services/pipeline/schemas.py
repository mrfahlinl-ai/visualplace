"""Structured vision-analysis output (spec §7).

The model returns evidence, not a verdict. Every observation is an
:class:`Observation` carrying its own confidence so the pipeline can weigh
uncertain clues appropriately and never presents a guess as fact.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Observation(BaseModel):
    """One uncertain observation with a confidence in [0, 1]."""

    observation: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class LandmarkCandidate(BaseModel):
    name: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    evidence: list[str] = Field(default_factory=list)


class VisionClues(BaseModel):
    """The structured clue set extracted from an image (spec §7).

    All fields are optional/defaulted so a partial or conservative model
    response still validates — missing evidence is represented as empty, never
    invented.
    """

    scene_type: str | None = None
    country_clues: list[Observation] = Field(default_factory=list)
    city_clues: list[Observation] = Field(default_factory=list)
    landmarks: list[LandmarkCandidate] = Field(default_factory=list)
    businesses: list[Observation] = Field(default_factory=list)
    sign_text: list[Observation] = Field(default_factory=list)
    languages: list[Observation] = Field(default_factory=list)
    road_features: list[Observation] = Field(default_factory=list)
    architecture: list[Observation] = Field(default_factory=list)
    natural_features: list[Observation] = Field(default_factory=list)
    vehicles: list[Observation] = Field(default_factory=list)
    license_plate_style: list[Observation] = Field(default_factory=list)
    geographic_clues: list[Observation] = Field(default_factory=list)
    visual_description: str = ""
    possible_regions: list[Observation] = Field(default_factory=list)


class VisionExtraction(BaseModel):
    """Result of the vision stage: the clues plus provider/usage metadata."""

    clues: VisionClues
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
