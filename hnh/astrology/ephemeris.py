"""
Planetary positions via Swiss Ephemeris (pyswisseph).
All times in UTC; datetime normalization and location validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Optional: fail at import if not installed when astrology is used
try:
    import swisseph as swe
except ImportError:
    swe = None  # type: ignore[assignment]

# Standard planet IDs for natal (v0.1)
PLANETS_NATAL = [
    ("Sun", 0),
    ("Moon", 1),
    ("Mercury", 2),
    ("Venus", 3),
    ("Mars", 4),
    ("Jupiter", 5),
    ("Saturn", 6),
]

# Lat/lon bounds
LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0


def normalize_birth_datetime_utc(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: float = 0.0,
) -> datetime:
    """Normalize birth time to UTC (no timezone conversion; assume input is already UTC)."""
    return datetime(
        year, month, day, hour, minute, int(second), int((second % 1) * 1_000_000),
        tzinfo=timezone.utc,
    )


def validate_location(lat: float, lon: float) -> None:
    """Validate latitude and longitude bounds. Raises ValueError if out of range."""
    if not (LAT_MIN <= lat <= LAT_MAX):
        raise ValueError(f"Latitude must be in [{LAT_MIN}, {LAT_MAX}], got {lat}")
    if not (LON_MIN <= lon <= LON_MAX):
        raise ValueError(f"Longitude must be in [{LON_MIN}, {LON_MAX}], got {lon}")


def datetime_to_julian_utc(dt: datetime) -> float:
    """Convert datetime (UTC) to Julian Day UT for Swiss Ephemeris."""
    if swe is None:
        raise RuntimeError("pyswisseph is not installed; install with pip install hnh[astrology]")
    if dt.tzinfo is not None and dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)
    ut = dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + dt.microsecond / 3600e6
    jd = swe.julday(dt.year, dt.month, dt.day, ut)
    return jd


def compute_positions(jd_ut: float) -> list[dict[str, Any]]:
    """
    Compute ecliptic longitudes for standard planets at given Julian Day UT.
    Returns list of {"planet": str, "longitude": float} (deterministic order).
    """
    if swe is None:
        raise RuntimeError("pyswisseph is not installed; install with pip install hnh[astrology]")
    swe.set_ephe_path(None)  # use built-in ephemeris
    result: list[dict[str, Any]] = []
    for name, pid in PLANETS_NATAL:
        xx, _ret = swe.calc_ut(jd_ut, pid)  # (position_tuple, flags)
        longitude = float(xx[0])  # ecliptic longitude
        result.append({"planet": name, "longitude": longitude})
    return result
