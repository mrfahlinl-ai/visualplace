"""OCR abstraction (spec §8).

Text detection is expressed as a provider so a dedicated OCR engine (Tesseract,
or a cloud vision OCR API) can be swapped in without touching callers. The
default is a no-op: the vision model already transcribes visible sign text
(persisted as ``sign_text`` clues with raw text + language), so OCR augments
rather than blocks the pipeline.

Per spec §8, providers preserve the original text and never silently "correct"
it: ``raw_text`` is verbatim, ``normalized_text`` is a separate, additive field.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class OCRResult(BaseModel):
    raw_text: str
    normalized_text: str | None = None
    language: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class OCRProvider(ABC):
    name: str

    @abstractmethod
    async def detect_text(self, *, image_bytes: bytes, media_type: str) -> list[OCRResult]:
        ...

    @abstractmethod
    async def health(self) -> bool:
        ...
