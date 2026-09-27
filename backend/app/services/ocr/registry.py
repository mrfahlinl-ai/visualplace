"""OCR provider factory (config-driven)."""

from __future__ import annotations

from functools import lru_cache

from app.services.ocr.base import OCRProvider
from app.services.ocr.null_provider import NullOCRProvider


@lru_cache
def get_ocr_provider() -> OCRProvider:
    # Config key reserved for when a real engine is added (e.g. OCR_PROVIDER).
    return NullOCRProvider()
