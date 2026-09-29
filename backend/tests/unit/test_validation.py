"""Image validation tests (spec §22): sniffing, hashing, bomb guard, errors."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from app.core.config import settings
from app.core.errors import ImageTooLargeError, InvalidImageError, UnsupportedMediaTypeError
from app.services.images.validation import inspect_and_validate


def _img(fmt: str, size=(48, 32)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (120, 60, 30)).save(buf, format=fmt)
    return buf.getvalue()


def test_valid_png_inspected() -> None:
    result = inspect_and_validate(data=_img("PNG"), declared_content_type="image/png")
    assert result.mime_type == "image/png"
    assert result.width == 48 and result.height == 32
    assert len(result.sha256) == 64
    assert result.phash is not None


def test_valid_jpeg_and_webp_sniffed() -> None:
    assert inspect_and_validate(
        data=_img("JPEG"), declared_content_type="x"
    ).mime_type == "image/jpeg"
    assert inspect_and_validate(
        data=_img("WEBP"), declared_content_type="x"
    ).mime_type == "image/webp"


def test_unsupported_type_rejected() -> None:
    with pytest.raises(UnsupportedMediaTypeError):
        inspect_and_validate(data=b"GIF89a not really", declared_content_type="image/gif")


def test_empty_rejected() -> None:
    with pytest.raises(InvalidImageError):
        inspect_and_validate(data=b"", declared_content_type="image/png")


def test_decompression_bomb_guard() -> None:
    original = settings.max_image_pixels
    settings.max_image_pixels = 100  # 10x10 px ceiling
    try:
        with pytest.raises(ImageTooLargeError):
            inspect_and_validate(data=_img("PNG", size=(64, 64)), declared_content_type="image/png")
    finally:
        settings.max_image_pixels = original
