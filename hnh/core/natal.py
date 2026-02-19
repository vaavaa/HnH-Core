"""
Natal chart: birth datetime (UTC), location validation, deterministic natal_positions.
Orchestrates ephemeris + houses + aspects → stable structure for Identity Core symbolic_input.
Spec 004: 10 planets, house (1–12), sign (0–11), angular_strength per planet.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hnh.astrology import aspects as asp
from hnh.astrology import ephemeris as eph
from hnh.astrology import houses as hou


def build_natal_positions(
    birth_datetime_utc: datetime,
    latitude: float,
    longitude: float,
    orb_config: asp.OrbConfig | None = None,
) -> dict[str, Any]:
    """
    Build deterministic natal_positions structure from birth data (UTC + lat/lon).
    Same input → identical output (reproducible).
    Positions: 10 planets with longitude, sign (0–11), house (1–12), angular_strength.
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
    # Round longitude for output; then add sign, house, angular_strength (Spec 004)
    n_pos = len(positions)
    positions_with_lon: list[dict[str, Any]] = [
        {"planet": p["planet"], "longitude": round(p["longitude"], 6)} for p in positions
    ]
    cusps, ascmc = hou.compute_houses(jd_ut, latitude, longitude)
    positions_with_houses = hou.assign_houses_and_strength(positions_with_lon, cusps)
    aspects_list = asp.detect_aspects(positions, orb_config)
    return {
        "birth_datetime_utc": dt_utc.isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "jd_ut": round(jd_ut, 6),
        "positions": positions_with_houses,
        "aspects": aspects_list,
        "houses": {"cusps": list(cusps), "ascendant": ascmc[0] if ascmc else None, "mc": ascmc[1] if len(ascmc) > 1 else None},
    }
