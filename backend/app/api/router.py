"""Aggregate API router.

Feature routers (analyze, location, ...) are added here as later phases land,
each mounted under the configured API prefix by ``main``.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import analyze, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(analyze.router)

# Phase 7+: api_router.include_router(location.router)
