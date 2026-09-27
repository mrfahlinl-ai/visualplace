"""Common API schemas shared across routers."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., examples=["IMAGE_TOO_LARGE"])
    message: str = Field(..., examples=["Image exceeds the maximum allowed size."])
    details: dict | None = None


class ErrorResponse(BaseModel):
    """The single error envelope returned by every failing endpoint."""

    error: ErrorDetail


class HealthComponent(BaseModel):
    name: str
    status: str  # "ok" | "degraded" | "down" | "not_configured"
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded"
    version: str
    environment: str
    components: list[HealthComponent] = Field(default_factory=list)
