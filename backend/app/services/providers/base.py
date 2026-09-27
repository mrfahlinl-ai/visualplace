"""Provider abstractions.

VisualPlace never binds itself to a single vendor. Every external capability —
vision AI, map/place search, web/image search — is expressed as an abstract
interface here. Concrete implementations live alongside (``ai/``, ``map/``,
``search/``) and are selected at runtime by the registry based on config.

Result types are deliberately provider-agnostic Pydantic models so the pipeline
downstream never sees a vendor-specific shape.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Vision AI                                                                    #
# --------------------------------------------------------------------------- #
class VisionResult(BaseModel):
    """Raw, provider-agnostic output of a vision analysis call.

    The structured clue extraction (spec §7) is layered on top of this in the
    pipeline; here we only capture the model's returned content plus usage so
    cost/observability can be tracked (spec §35).
    """

    provider: str
    model: str
    content: str = Field(description="Model text/JSON output as returned")
    input_tokens: int | None = None
    output_tokens: int | None = None
    raw: dict | None = Field(default=None, description="Provider-specific payload for debugging")


class AIVisionProvider(ABC):
    """A vision-capable model that can describe an image under our control.

    Implementations MUST treat any text within the image as untrusted data and
    never as instructions (prompt-injection defence, spec §24). That separation
    is enforced by the caller's prompt construction, but providers must not add
    their own instruction-following of image content.
    """

    name: str

    @abstractmethod
    async def analyze_image(
        self,
        *,
        image_bytes: bytes,
        media_type: str,
        system_prompt: str,
        instruction: str,
        max_output_tokens: int | None = None,
    ) -> VisionResult:
        """Send an image plus a trusted instruction and return the raw result."""

    @abstractmethod
    async def health(self) -> bool:
        """Cheap check that the provider is reachable/configured."""


# --------------------------------------------------------------------------- #
# Maps / places                                                                #
# --------------------------------------------------------------------------- #
class Place(BaseModel):
    name: str
    latitude: float
    longitude: float
    address: str | None = None
    city: str | None = None
    country: str | None = None
    country_code: str | None = None
    place_type: str | None = None
    provider: str
    provider_place_id: str | None = None
    raw: dict | None = None


class MapProvider(ABC):
    """Geocoding + place search + static/tile map rendering."""

    name: str

    @abstractmethod
    async def search_places(
        self,
        query: str,
        *,
        near: tuple[float, float] | None = None,
        country_code: str | None = None,
        limit: int = 5,
    ) -> list[Place]:
        ...

    @abstractmethod
    async def reverse_geocode(self, latitude: float, longitude: float) -> Place | None:
        ...

    @abstractmethod
    async def health(self) -> bool:
        ...


# --------------------------------------------------------------------------- #
# Web / image search                                                           #
# --------------------------------------------------------------------------- #
class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str | None = None
    source: str | None = None
    provider: str


class SearchProvider(ABC):
    """Web and image search used for verification only (spec §15)."""

    name: str

    @abstractmethod
    async def web_search(self, query: str, *, limit: int = 5) -> list[SearchResult]:
        ...

    @abstractmethod
    async def image_search(self, query: str, *, limit: int = 5) -> list[SearchResult]:
        ...

    @abstractmethod
    async def health(self) -> bool:
        ...
