"""
SectEngine (Spec 008, FR-007, FR-013).
sect_score ∈ {-1, 0, +1}: day (+1), night (-1), unknown (0).
Preferred: Sun altitude; fallback: Sun house (7–12 day, 1–6 night).
"""

from __future__ import annotations

from typing import Any

# FR-013: altitude > 0 → +1, < 0 → -1, == 0 → 0
# Fallback: houses 7,8,9,10,11,12 → day (+1); 1,2,3,4,5,6 → night (-1). Boundary 6/7 exclusive.


def sect_score_from_altitude(sun_altitude_deg: float | None) -> int:
    """Preferred: Sun altitude. > 0 → +1, < 0 → -1, == 0 or None → 0."""
    if sun_altitude_deg is None:
        return 0
    if sun_altitude_deg > 0:
        return 1
    if sun_altitude_deg < 0:
        return -1
    return 0


def sect_score_from_house(sun_house: int | None) -> int:
    """Fallback: Sun house 1..12. Houses 7–12 → day (+1), 1–6 → night (-1). Missing → 0."""
    if sun_house is None:
        return 0
    if 7 <= sun_house <= 12:
        return 1
    if 1 <= sun_house <= 6:
        return -1
    return 0


def sect_score(
    sun_altitude_deg: float | None = None,
    sun_house: int | None = None,
) -> int:
    """
    FR-007: sect_score ∈ {-1, 0, +1}.
    Preferred: sun_altitude_deg (if not None); else fallback sun_house.
    """
    s = sect_score_from_altitude(sun_altitude_deg)
    if s != 0:
        return s
    return sect_score_from_house(sun_house)


def sect_score_from_natal(natal_data: Any) -> int:
    """
    Compute sect_score from natal_data (e.g. positions with Sun's house/altitude).
    natal_data: dict with "positions" (list of dicts: planet, house, optionally altitude),
    or object with .positions. Sun altitude may be under a key like sun_altitude_deg.
    """
    positions = getattr(natal_data, "positions", None) or (natal_data.get("positions") if isinstance(natal_data, dict) else [])
    sun_alt: float | None = None
    sun_house: int | None = None
    if isinstance(natal_data, dict) and "sun_altitude_deg" in natal_data:
        sun_alt = natal_data.get("sun_altitude_deg")
    for p in positions or []:
        name = (p.get("planet") or getattr(p, "planet", "") or "").strip()
        if name.lower() != "sun":
            continue
        if sun_house is None:
            h = p.get("house") or getattr(p, "house", None)
            if h is not None:
                sun_house = int(h)
        if sun_alt is None and "altitude" in p:
            sun_alt = float(p.get("altitude", 0))
    return sect_score(sun_altitude_deg=sun_alt, sun_house=sun_house)
