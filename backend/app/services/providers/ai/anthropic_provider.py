"""Anthropic (Claude) vision provider.

The default AI provider. Owns *how* we talk to Anthropic; the rest of the app
depends only on :class:`AIVisionProvider`.

The image is sent as a base64 content block placed *before* the trusted text
instruction (per the current Messages API vision shape). Any text inside the
image is untrusted data — the injection boundary is enforced by the system
prompt built in the pipeline (spec §24), not here.
"""

from __future__ import annotations

import base64

from app.core.errors import ProviderNotConfiguredError, ProviderUnavailableError
from app.services.providers.base import AIVisionProvider, VisionResult


class AnthropicVisionProvider(AIVisionProvider):
    name = "anthropic"

    def __init__(self, *, api_key: str | None, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client = None  # lazily created AsyncAnthropic

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._client

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

        b64 = base64.standard_b64encode(image_bytes).decode("ascii")
        client = self._get_client()
        try:
            message = await client.messages.create(
                model=self._model,
                max_tokens=max_output_tokens or 2048,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": b64,
                                },
                            },
                            {"type": "text", "text": instruction},
                        ],
                    }
                ],
            )
        except Exception as exc:  # noqa: BLE001 - normalise SDK/network errors
            raise ProviderUnavailableError(
                f"Anthropic vision request failed: {type(exc).__name__}"
            ) from exc

        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
        return VisionResult(
            provider=self.name,
            model=self._model,
            content=text,
            input_tokens=getattr(message.usage, "input_tokens", None),
            output_tokens=getattr(message.usage, "output_tokens", None),
        )

    async def health(self) -> bool:
        # A configured key is the cheap health signal; a live ping would add cost.
        return self.configured
