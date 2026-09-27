"""EXIF extraction tests (spec §9).

Builds JPEGs with/without GPS EXIF via Pillow and asserts extraction, GPS
validation, and graceful handling of absent/invalid metadata.
"""

from __future__ import annotations

import io

from PIL import ExifTags, Image

from app.services.images.exif import extract_exif


def _jpeg(exif: Image.Exif | None = None) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (48, 32), (100, 100, 100))
    if exif is not None:
        img.save(buf, format="JPEG", exif=exif)
    else:
        img.save(buf, format="JPEG")
    return buf.getvalue()


def _gps_exif(lat_ref: str, lat, lng_ref: str, lng) -> Image.Exif:
    exif = Image.Exif()
    exif[ExifTags.Base.Make] = "TestCam"
    exif[ExifTags.Base.Model] = "Model-X"
    exif[ExifTags.Base.Software] = "VisualPlaceTest"
    exif[ExifTags.IFD.GPSInfo] = {
        ExifTags.GPS.GPSLatitudeRef: lat_ref,
        ExifTags.GPS.GPSLatitude: lat,
        ExifTags.GPS.GPSLongitudeRef: lng_ref,
        ExifTags.GPS.GPSLongitude: lng,
    }
    return exif


def test_extract_valid_gps() -> None:
    # Sylhet ~ 24.8949 N, 91.8687 E
    exif = _gps_exif("N", (24, 53, 41.64), "E", (91, 52, 7.32))
    data = extract_exif(_jpeg(exif))
    assert data.has_gps is True
    assert data.gps_valid is True
    assert data.gps_latitude is not None and abs(data.gps_latitude - 24.8949) < 0.01
    assert data.gps_longitude is not None and abs(data.gps_longitude - 91.8687) < 0.01
    assert data.camera_make == "TestCam"
    assert data.camera_model == "Model-X"


def test_southern_western_hemisphere_signs() -> None:
    exif = _gps_exif("S", (33, 51, 54.0), "W", (70, 39, 0.0))
    data = extract_exif(_jpeg(exif))
    assert data.gps_latitude is not None and data.gps_latitude < 0
    assert data.gps_longitude is not None and data.gps_longitude < 0


def test_null_island_is_invalid() -> None:
    exif = _gps_exif("N", (0, 0, 0), "E", (0, 0, 0))
    data = extract_exif(_jpeg(exif))
    assert data.has_gps is True
    assert data.gps_valid is False
    assert data.gps_latitude is None  # invalid coords are not surfaced


def test_no_exif_reports_no_gps() -> None:
    data = extract_exif(_jpeg())
    assert data.has_gps is False
    assert data.gps_valid is None
    assert data.gps_latitude is None


def test_corrupt_bytes_do_not_raise() -> None:
    data = extract_exif(b"not an image")
    assert data.has_gps is False
