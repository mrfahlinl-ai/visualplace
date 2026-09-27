"""Image processing for the vision stage.

Downscales large uploads before they reach the (expensive) vision model — a core
cost control (spec §25/§39). Returns web-safe JPEG/PNG bytes plus the media type
to send to the provider.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image

from app.core.config import settings

# Media types the vision API accepts directly.
_VISION_SAFE = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@dataclass(frozen=True)
class VisionImage:
    data: bytes
    media_type: str
    width: int
    height: int


def prepare_for_vision(data: bytes, *, source_mime: str) -> VisionImage:
    """Resize (longest side ≤ ``vision_max_dimension``) and normalise the format.

    HEIC/unsupported inputs are transcoded to JPEG when decodable. Raises nothing
    the caller can't handle — decode errors propagate for the pipeline to record.
    """
    Image.MAX_IMAGE_PIXELS = settings.max_image_pixels
    with Image.open(io.BytesIO(data)) as img:
        img = img.convert("RGB") if img.mode not in ("RGB", "L") else img
        max_dim = settings.vision_max_dimension
        w, h = img.size
        scale = min(1.0, max_dim / max(w, h))
        if scale < 1.0:
            img = img.resize((round(w * scale), round(h * scale)), Image.Resampling.LANCZOS)

        out_mime = source_mime if source_mime in _VISION_SAFE else "image/jpeg"
        fmt = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}.get(
            out_mime, "JPEG"
        )
        buf = io.BytesIO()
        save_kwargs = {"quality": 85} if fmt in ("JPEG", "WEBP") else {}
        img.save(buf, format=fmt, **save_kwargs)
        return VisionImage(buf.getvalue(), out_mime, img.width, img.height)
