"""EXIF metadata extraction (spec §9).

Inspected *before* any AI inference. We extract only useful fields (privacy,
spec §21): GPS, capture time, camera make/model, software, orientation. GPS
presence is recorded explicitly and coordinates are **validated** — the app
never assumes EXIF GPS is correct just because it exists.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import UTC, datetime

from PIL import ExifTags, Image


@dataclass(frozen=True)
class ExifData:
    has_gps: bool = False
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    gps_valid: bool | None = None
    captured_at: datetime | None = None
    camera_make: str | None = None
    camera_model: str | None = None
    software: str | None = None
    orientation: int | None = None


def _to_degrees(value) -> float | None:
    try:
        d, m, s = (float(x) for x in value)
        return d + m / 60.0 + s / 3600.0
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _valid_coords(lat: float | None, lng: float | None) -> bool:
    if lat is None or lng is None:
        return False
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        return False
    # Exactly (0, 0) is almost always a null/placeholder, not a real fix.
    return not (abs(lat) < 1e-9 and abs(lng) < 1e-9)


def _clean_str(value) -> str | None:
    if value is None:
        return None
    text = value.decode("utf-8", "ignore") if isinstance(value, bytes) else str(value)
    text = text.replace("\x00", "").strip()
    return text or None


def _parse_datetime(value) -> datetime | None:
    text = _clean_str(value)
    if not text:
        return None
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def extract_exif(data: bytes) -> ExifData:
    """Best-effort EXIF extraction; never raises on malformed metadata."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            exif = img.getexif()
    except Exception:  # noqa: BLE001 - absent/corrupt EXIF is normal
        return ExifData()

    if not exif:
        return ExifData()

    make = _clean_str(exif.get(ExifTags.Base.Make))
    model = _clean_str(exif.get(ExifTags.Base.Model))
    software = _clean_str(exif.get(ExifTags.Base.Software))
    orientation = exif.get(ExifTags.Base.Orientation)
    orientation = int(orientation) if isinstance(orientation, int) else None

    # Capture time: prefer DateTimeOriginal (Exif IFD), fall back to DateTime.
    captured_at = None
    try:
        exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
        captured_at = _parse_datetime(exif_ifd.get(ExifTags.Base.DateTimeOriginal))
    except Exception:  # noqa: BLE001, S110 - missing Exif IFD is normal
        captured_at = None
    if captured_at is None:
        captured_at = _parse_datetime(exif.get(ExifTags.Base.DateTime))

    # GPS.
    lat = lng = None
    has_gps = False
    try:
        gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
    except Exception:  # noqa: BLE001
        gps = None
    if gps:
        lat_val = gps.get(ExifTags.GPS.GPSLatitude)
        lng_val = gps.get(ExifTags.GPS.GPSLongitude)
        lat_ref = _clean_str(gps.get(ExifTags.GPS.GPSLatitudeRef))
        lng_ref = _clean_str(gps.get(ExifTags.GPS.GPSLongitudeRef))
        if lat_val is not None and lng_val is not None:
            has_gps = True
            lat = _to_degrees(lat_val)
            lng = _to_degrees(lng_val)
            if lat is not None and lat_ref and lat_ref.upper().startswith("S"):
                lat = -lat
            if lng is not None and lng_ref and lng_ref.upper().startswith("W"):
                lng = -lng

    gps_valid = _valid_coords(lat, lng) if has_gps else None
    if gps_valid is False:
        # Keep the flag but don't surface invalid coordinates downstream.
        lat = lng = None

    return ExifData(
        has_gps=has_gps,
        gps_latitude=lat,
        gps_longitude=lng,
        gps_valid=gps_valid,
        captured_at=captured_at,
        camera_make=make,
        camera_model=model,
        software=software,
        orientation=orientation,
    )
