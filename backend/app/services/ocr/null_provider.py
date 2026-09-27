"""No-op OCR provider (default).

Returns no results — the vision model already supplies sign-text transcription.
Selecting a dedicated engine (Tesseract via ``pytesseract``, or a cloud OCR API)
is a later, optional enhancement wired behind this same interface.
"""

from __future__ import annotations

from app.services.ocr.base import OCRProvider, OCRResult


class NullOCRProvider(OCRProvider):
    name = "none"

    async def detect_text(self, *, image_bytes: bytes, media_type: str) -> list[OCRResult]:
        return []

    async def health(self) -> bool:
        return True
