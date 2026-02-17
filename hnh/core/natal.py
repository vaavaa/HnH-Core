"""
Natal chart: birth datetime (UTC), location validation, deterministic natal_positions.
Orchestrates ephemeris + aspects → stable structure for Identity Core symbolic_input.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hnh.astrology import aspects as asp
from hnh.astrology import ephemeris as eph


def build_natal_positions(
    birth_datetime_utc: datetime,
    latitude: float,
    longitude: float,
    orb_config: asp.OrbConfig | None = None,
) -> dict[str, Any]:
    """
    Build deterministic natal_positions structure from birth data (UTC + lat/lon).
    Same input → identical output (reproducible).
    """
    eph.validate_location(latitude, longitude)
    # Normalize to UTC if needed
    if birth_datetime_utc.tzinfo is None:
        birth_datetime_utc = birth_datetime_utc.replace(tzinfo=timezone.utc)
    jd_ut = eph.datetime_to_julian_utc(birth_datetime_utc)
    positions = eph.compute_positions(jd_ut)
    # Round for stable serialization
    positions_rounded = [
        {"planet": p["planet"], "longitude": round(p["longitude"], 6)}
        for p in positions
    ]
    aspects_list = asp.detect_aspects(positions, orb_config)
    return {
        "birth_datetime_utc": birth_datetime_utc.isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "jd_ut": round(jd_ut, 6),
        "positions": positions_rounded,
        "aspects": aspects_list,
    }
