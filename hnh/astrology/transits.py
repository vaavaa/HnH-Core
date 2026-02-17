"""
Transit positions and transit–natal aspects.
Injected time only (no datetime.now()); deterministic transit_signature.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hnh.astrology import aspects as asp
from hnh.astrology import ephemeris as eph


def compute_transit_signature(
    injected_time_utc: datetime,
    natal_positions: dict[str, Any],
    orb_config: asp.OrbConfig | None = None,
) -> dict[str, Any]:
    """
    Compute deterministic transit signature for injected time and given natal.
    Same time + same natal → identical output. No system clock.
    """
    if injected_time_utc.tzinfo is None:
        injected_time_utc = injected_time_utc.replace(tzinfo=timezone.utc)
    elif injected_time_utc.tzinfo != timezone.utc:
        injected_time_utc = injected_time_utc.astimezone(timezone.utc)
    jd_ut = eph.datetime_to_julian_utc(injected_time_utc)
    transit_positions = eph.compute_positions(jd_ut)
    transit_rounded = [
        {"planet": p["planet"], "longitude": round(p["longitude"], 6)}
        for p in transit_positions
    ]
    natal_pos_list = natal_positions.get("positions", [])
    aspects_to_natal = asp.aspects_between(transit_positions, natal_pos_list, orb_config)
    return {
        "timestamp_utc": injected_time_utc.isoformat(),
        "jd_ut": round(jd_ut, 6),
        "positions": transit_rounded,
        "aspects_to_natal": aspects_to_natal,
    }
