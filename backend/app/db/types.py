"""Portable column types.

``JSONB_or_JSON`` uses PostgreSQL ``JSONB`` in production and falls back to
generic ``JSON`` on other dialects (e.g. SQLite in unit tests).
"""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

# Use as: mapped_column(JSONB_OR_JSON)
JSONB_OR_JSON = JSON().with_variant(JSONB, "postgresql")
