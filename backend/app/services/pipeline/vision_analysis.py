"""Vision analysis stage: image → structured clues.

Sends the prepared image plus the trusted instruction to the configured AI
vision provider, then parses the model's JSON into :class:`VisionClues`. Parsing
is defensive (models sometimes wrap JSON in prose/markdown); a parse failure is
surfaced as a clear error rather than fabricated clues.
"""

from __future__ import annotations

import json

from app.core.config import settings
from app.core.errors import AppError, ErrorCode
from app.core.logging import get_logger
from app.services.pipeline.prompts import SYSTEM_PROMPT, build_instruction
from app.services.pipeline.schemas import VisionClues, VisionExtraction
from app.services.providers.base import AIVisionProvider

log = get_logger(__name__)


def _extract_json_object(text: str) -> dict:
    """Pull the first JSON object out of a model response, tolerating fences/prose."""
    s = text.strip()
    if s.startswith("```"):
        # Strip a ```json ... ``` fence.
        s = s.split("```", 2)[1] if s.count("```") >= 2 else s
        if s.lstrip().lower().startswith("json"):
            s = s.lstrip()[4:]
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise AppError(
            "Vision model did not return parseable JSON.",
            code=ErrorCode.ANALYSIS_FAILED,
            status_code=502,
        )
    try:
        return json.loads(s[start : end + 1])
    except json.JSONDecodeError as exc:
        raise AppError(
            "Vision model returned invalid JSON.",
            code=ErrorCode.ANALYSIS_FAILED,
            status_code=502,
        ) from exc


class VisionAnalyzer:
    def __init__(self, provider: AIVisionProvider) -> None:
        self.provider = provider

    async def extract_clues(
        self, *, image_bytes: bytes, media_type: str, hint: str | None = None
    ) -> VisionExtraction:
        result = await self.provider.analyze_image(
            image_bytes=image_bytes,
            media_type=media_type,
            system_prompt=SYSTEM_PROMPT,
            instruction=build_instruction(hint),
            max_output_tokens=settings.ai_max_output_tokens,
        )

        raw = _extract_json_object(result.content)
        try:
            clues = VisionClues.model_validate(raw)
        except Exception as exc:  # noqa: BLE001 - normalise to a clean error
            raise AppError(
                "Vision model output did not match the expected schema.",
                code=ErrorCode.ANALYSIS_FAILED,
                status_code=502,
            ) from exc

        log.info(
            "vision_clues_extracted",
            provider=result.provider,
            model=result.model,
            landmarks=len(clues.landmarks),
            sign_text=len(clues.sign_text),
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )
        return VisionExtraction(
            clues=clues,
            provider=result.provider,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )
