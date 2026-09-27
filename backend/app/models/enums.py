"""Domain enumerations.

Stored as strings (``native_enum=False``) so values are readable in the DB and
schema evolution stays simple.
"""

from __future__ import annotations

from enum import StrEnum


class AnalysisMode(StrEnum):
    IDENTIFY = "identify"          # spec §19 mode 1
    FIND_EXACT = "find_exact"      # spec §19 mode 2 (more aggressive verification)


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class ConfidenceBand(StrEnum):
    """How a result is characterised to the user (spec §1, §33).

    Ordered strongest → weakest. The UI never shows an exact pin below
    ``STRONG``/``EXACT_GPS``.
    """

    EXACT_GPS = "exact_gps"        # trustworthy GPS EXIF
    STRONG = "strong"             # strong landmark / unambiguous match
    PROBABLE = "probable"         # good multi-signal match
    APPROXIMATE = "approximate"   # region-level inference only
    WEAK = "weak"                 # speculative
    UNKNOWN = "unknown"           # insufficient evidence — "I don't know"


class ClueCategory(StrEnum):
    SCENE_TYPE = "scene_type"
    COUNTRY = "country"
    CITY = "city"
    LANDMARK = "landmark"
    BUSINESS = "business"
    SIGN_TEXT = "sign_text"
    LANGUAGE = "language"
    ROAD = "road"
    ARCHITECTURE = "architecture"
    NATURAL = "natural"
    VEHICLE = "vehicle"
    LICENSE_PLATE = "license_plate"
    GEOGRAPHIC = "geographic"
    OTHER = "other"


class ClueSource(StrEnum):
    AI_VISION = "ai_vision"
    OCR = "ocr"
    EXIF = "exif"


class CandidateSource(StrEnum):
    AI = "ai"
    MAP = "map"
    SEARCH = "search"
    EXIF = "exif"


class EvidenceCategory(StrEnum):
    LANDMARK_MATCH = "landmark_match"
    TEXT_MATCH = "text_match"
    BUSINESS_MATCH = "business_match"
    ARCHITECTURE_MATCH = "architecture_match"
    ROAD_MATCH = "road_match"
    GEOGRAPHY_MATCH = "geography_match"
    VISUAL_MATCH = "visual_match"
    EXTERNAL_VERIFICATION = "external_verification"
    EXIF_GPS = "exif_gps"


class EvidenceKind(StrEnum):
    """Evidence either supports a candidate or contradicts it (spec §14)."""

    MATCH = "match"
    CONTRADICTION = "contradiction"
