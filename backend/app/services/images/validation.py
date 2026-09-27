"""Secure image validation & inspection (spec §21, §22, §25).

Defends the upload path:
- **Magic-byte sniffing** — the real format is detected from content, not the
  client-supplied filename or Content-Type (both untrusted).
- **Size limit** — enforced against the actual byte length.
- **Decompression-bomb guard** — Pillow's ``MAX_IMAGE_PIXELS`` plus an explicit
  dimension check reject images that expand to huge rasters.
- **Corruption check** — the image must decode.
- **Hashing** — sha256 (dedup/cache) and a perceptual aHash (near-duplicate
  detection) are computed here.

Nothing here trusts the client. Filenames are never used for storage.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.core.errors import (
    ImageTooLargeError,
    InvalidImageError,
    UnsupportedMediaTypeError,
)

# Try to enable HEIC/HEIF decoding if pillow-heif is installed (optional).
try:  # pragma: no cover - depends on optional dependency
    import pillow_heif  # type: ignore

    pillow_heif.register_heif_opener()
    _HEIF_AVAILABLE = True
except Exception:  # noqa: BLE001
    _HEIF_AVAILABLE = False

# Magic-byte signatures → canonical MIME type.
_MAGIC: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
]


def _sniff_mime(data: bytes) -> str | None:
    for sig, mime in _MAGIC:
        if data.startswith(sig):
            return mime
    # RIFF....WEBP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    # ISO-BMFF (HEIC/HEIF): 'ftyp' at offset 4, brand indicates heic/heif/mif1.
    if data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand in (b"heic", b"heix", b"hevc", b"heim", b"heis", b"mif1", b"msf1"):
            return "image/heic"
    return None


@dataclass(frozen=True)
class InspectedImage:
    mime_type: str
    width: int | None
    height: int | None
    byte_size: int
    sha256: str
    phash: str | None


def _average_hash(img: Image.Image, hash_size: int = 8) -> str:
    """Simple perceptual aHash (no extra dependency)."""
    small = img.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    pixels = list(small.tobytes())  # one byte per pixel in "L" mode
    avg = sum(pixels) / len(pixels)
    bits = "".join("1" if p >= avg else "0" for p in pixels)
    return f"{int(bits, 2):0{hash_size * hash_size // 4}x}"


def inspect_and_validate(*, data: bytes, declared_content_type: str | None) -> InspectedImage:
    """Validate an uploaded image and return safe, inspected metadata.

    Raises the appropriate :class:`AppError` subclass on any violation.
    """
    byte_size = len(data)
    if byte_size == 0:
        raise InvalidImageError("Uploaded file is empty.")
    if byte_size > settings.max_upload_bytes:
        raise ImageTooLargeError("Image exceeds the maximum allowed size.")

    mime = _sniff_mime(data)
    if mime is None:
        raise UnsupportedMediaTypeError(
            "Unsupported or unrecognized image format. Allowed: JPG, PNG, WEBP, HEIC."
        )
    if mime not in settings.allowed_image_type_set:
        raise UnsupportedMediaTypeError(f"Image type '{mime}' is not allowed.")

    sha256 = hashlib.sha256(data).hexdigest()

    width = height = None
    phash: str | None = None

    if mime in ("image/heic", "image/heif") and not _HEIF_AVAILABLE:
        # Accept the upload but skip decode-dependent metadata; the pipeline
        # converts HEIC in a later phase. We do not fabricate dimensions.
        return InspectedImage(mime, None, None, byte_size, sha256, None)

    # Guard against decompression bombs before fully decoding.
    Image.MAX_IMAGE_PIXELS = settings.max_image_pixels
    try:
        with Image.open(io.BytesIO(data)) as probe:
            width, height = probe.size
            if width * height > settings.max_image_pixels:
                raise ImageTooLargeError("Image resolution exceeds the allowed limit.")
            # Fully load to detect truncation/corruption, then hash perceptually.
            probe.load()
            phash = _average_hash(probe)
    except Image.DecompressionBombError as exc:
        raise ImageTooLargeError("Image resolution exceeds the allowed limit.") from exc
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError("The image could not be decoded (corrupt or invalid).") from exc

    return InspectedImage(mime, width, height, byte_size, sha256, phash)
