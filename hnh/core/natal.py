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
    if birth_datetime_utc.tzinfo is None:
        dt_utc = birth_datetime_utc.replace(tzinfo=timezone.utc)
    elif birth_datetime_utc.tzinfo != timezone.utc:
        dt_utc = birth_datetime_utc.astimezone(timezone.utc)
    else:
        dt_utc = birth_datetime_utc
    jd_ut = eph.datetime_to_julian_utc(dt_utc)
    positions = eph.compute_positions(jd_ut)
    n_pos = len(positions)
    positions_rounded: list[dict[str, Any]] = [None] * n_pos
    for i in range(n_pos):
        p = positions[i]
        positions_rounded[i] = {"planet": p["planet"], "longitude": round(p["longitude"], 6)}
    aspects_list = asp.detect_aspects(positions, orb_config)
    return {
        "birth_datetime_utc": dt_utc.isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "jd_ut": round(jd_ut, 6),
        "positions": positions_rounded,
        "aspects": aspects_list,
    }
