"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-27

Creates the full VisualPlace schema (spec §26). Portable UUID PKs (native on
PostgreSQL), enums stored as VARCHAR + CHECK, and JSONB for flexible payloads.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from app.models.enums import (
    AnalysisMode,
    AnalysisStatus,
    CandidateSource,
    ClueCategory,
    ClueSource,
    ConfidenceBand,
    EvidenceCategory,
    EvidenceKind,
)

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _ts() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_ts(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "locations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=256), nullable=True),
        sa.Column("country", sa.String(length=256), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("place_type", sa.String(length=128), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_place_id", sa.String(length=256), nullable=True),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        *_ts(),
    )
    op.create_index("ix_locations_country_code", "locations", ["country_code"])
    op.create_index(
        "uq_locations_provider_place",
        "locations",
        ["provider", "provider_place_id"],
        unique=True,
        postgresql_where=sa.text("provider_place_id IS NOT NULL"),
    )

    op.create_table(
        "analyses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "mode",
            sa.Enum(AnalysisMode, native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(AnalysisStatus, native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.Column(
            "final_location_id",
            sa.Uuid(),
            sa.ForeignKey("locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "confidence_band",
            sa.Enum(ConfidenceBand, native_enum=False, length=20),
            nullable=True,
        ),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("processing_ms", sa.Integer(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
    )
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"])
    op.create_index("ix_analyses_status", "analyses", ["status"])
    op.create_index("ix_analyses_expires_at", "analyses", ["expires_at"])

    op.create_table(
        "uploaded_images",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.Uuid(),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_provider", sa.String(length=20), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("phash", sa.String(length=64), nullable=True),
        sa.Column("retained", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
    )
    op.create_index(
        "ix_uploaded_images_analysis_id", "uploaded_images", ["analysis_id"], unique=True
    )
    op.create_index("ix_uploaded_images_sha256", "uploaded_images", ["sha256"])
    op.create_index("ix_uploaded_images_phash", "uploaded_images", ["phash"])

    op.create_table(
        "image_metadata",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "image_id",
            sa.Uuid(),
            sa.ForeignKey("uploaded_images.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("has_gps", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("gps_latitude", sa.Float(), nullable=True),
        sa.Column("gps_longitude", sa.Float(), nullable=True),
        sa.Column("gps_valid", sa.Boolean(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("camera_make", sa.String(length=128), nullable=True),
        sa.Column("camera_model", sa.String(length=128), nullable=True),
        sa.Column("software", sa.String(length=128), nullable=True),
        sa.Column("orientation", sa.Integer(), nullable=True),
        *_ts(),
    )
    op.create_index("ix_image_metadata_image_id", "image_metadata", ["image_id"], unique=True)

    op.create_table(
        "visual_clues",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.Uuid(),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.Enum(ClueCategory, native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.Enum(ClueSource, native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        *_ts(),
    )
    op.create_index("ix_visual_clues_analysis_id", "visual_clues", ["analysis_id"])
    op.create_index("ix_visual_clues_category", "visual_clues", ["category"])

    op.create_table(
        "candidates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.Uuid(),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.Uuid(),
            sa.ForeignKey("locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("city", sa.String(length=256), nullable=True),
        sa.Column("country", sa.String(length=256), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("place_type", sa.String(length=128), nullable=True),
        sa.Column(
            "source",
            sa.Enum(CandidateSource, native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("radius_m", sa.Float(), nullable=True),
        *_ts(),
    )
    op.create_index("ix_candidates_analysis_id", "candidates", ["analysis_id"])
    op.create_index("ix_candidates_rank", "candidates", ["rank"])

    op.create_table(
        "candidate_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "candidate_id",
            sa.Uuid(),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.Enum(EvidenceCategory, native_enum=False, length=32),
            nullable=False,
        ),
        sa.Column(
            "kind",
            sa.Enum(EvidenceKind, native_enum=False, length=16),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=True),
        *_ts(),
    )
    op.create_index("ix_candidate_evidence_candidate_id", "candidate_evidence", ["candidate_id"])

    op.create_table(
        "api_usage",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.Uuid(),
            sa.ForeignKey("analyses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("cost_estimate_usd", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        *_ts(),
    )
    op.create_index("ix_api_usage_analysis_id", "api_usage", ["analysis_id"])
    op.create_index("ix_api_usage_provider", "api_usage", ["provider"])

    op.create_table(
        "search_cache",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("cache_key", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("response", postgresql.JSONB(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
    )
    op.create_index("ix_search_cache_cache_key", "search_cache", ["cache_key"], unique=True)
    op.create_index("ix_search_cache_expires_at", "search_cache", ["expires_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.Uuid(),
            sa.ForeignKey("analyses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor", sa.String(length=128), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        *_ts(),
    )
    op.create_index("ix_audit_logs_analysis_id", "audit_logs", ["analysis_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    for table in (
        "audit_logs",
        "search_cache",
        "api_usage",
        "candidate_evidence",
        "candidates",
        "visual_clues",
        "image_metadata",
        "uploaded_images",
        "analyses",
        "locations",
        "users",
    ):
        op.drop_table(table)
