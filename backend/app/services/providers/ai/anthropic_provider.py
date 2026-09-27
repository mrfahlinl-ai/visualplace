"""Anthropic (Claude) vision provider.

The default AI provider. This class owns *how* we talk to Anthropic; the rest
of the app depends only on :class:`AIVisionProvider`.

NOTE (integration point — Phase 4): the concrete vision call is implemented in
the AI-analysis phase, after confirming the current Messages API + vision
payload against official docs (spec §45). Until then ``analyze_image`` raises a
clear, honest error rather than returning fabricated results (spec §44). Config
detection and health already work so the app boots and reports status.
"""

from __future__ import annotations

from app.core.errors import ProviderNotConfiguredError
from app.services.providers.base import AIVisionProvider, VisionResult


class AnthropicVisionProvider(AIVisionProvider):
    name = "anthropic"

    def __init__(self, *, api_key: str | None, model: str) -> None:
        self._api_key = api_key
        self._model = model

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    async def analyze_image(
        self,
        *,
        image_bytes: bytes,
        media_type: str,
        system_prompt: str,
        instruction: str,
        max_output_tokens: int | None = None,
    ) -> VisionResult:
        if not self.configured:
            raise ProviderNotConfiguredError(
                "Anthropic AI provider is not configured. Set AI_API_KEY.",
            )
        # Implemented in Phase 4 (image analysis). See module docstring.
        raise NotImplementedError(
            "AnthropicVisionProvider.analyze_image is wired in Phase 4 "
            "(vision Messages API call)."
        )

    async def health(self) -> bool:
        # A configured key is the cheap health signal; a live ping is added when
        # the call is implemented.
        return self.configured
