"""
House cusps and house assignment (Spec 004).
Default system Placidus; angular strength from house only (contract angular-strength.md).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_EPHE_PATH = str(Path(__file__).resolve().parent.parent.parent / "ephe")

try:
    import swisseph as swe
    swe.set_ephe_path(_EPHE_PATH)
except ImportError:
    swe = None  # type: ignore[assignment]

# Contract 004 angular-strength: house 1..12 → [0, 1]
# Angular (1,4,7,10)=1.0, Succedent (2,5,8,11)=0.6, Cadent (3,6,9,12)=0.3
ANGULAR_STRENGTH_BY_HOUSE: tuple[float, ...] = (
    1.0, 0.6, 0.3, 1.0, 0.6, 0.3, 1.0, 0.6, 0.3, 1.0, 0.6, 0.3,
)

DEFAULT_HOUSE_SYSTEM = "P"  # Placidus


def _norm360(lon: float) -> float:
    """Normalize longitude to [0, 360)."""
    x = lon % 360.0
    return x if x >= 0 else x + 360.0


def compute_houses(
    jd_ut: float,
    geolat: float,
    geolon: float,
    hsys: str = DEFAULT_HOUSE_SYSTEM,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """
    Compute house cusps and ASC/MC for given Julian day and location.
    Returns (cusps_1_to_12, ascmc). Cusps are longitudes of house 1..12 cusps.
    """
    if swe is None:
        raise RuntimeError("pyswisseph is not installed; install with pip install hnh[astrology]")
    hsys_bytes = hsys.encode("ascii") if isinstance(hsys, str) else hsys
    cusps, ascmc = swe.houses(jd_ut, geolat, geolon, hsys_bytes)
    # cusps: 12 elements, index 0 = cusp 1, index 11 = cusp 12
    if hasattr(cusps, "__len__") and len(cusps) >= 12:
        cusps_tuple = tuple(float(cusps[i]) for i in range(12))
    else:
        cusps_tuple = tuple(float(c) for c in cusps[:12])
    ascmc_tuple = tuple(float(ascmc[i]) for i in range(min(8, len(ascmc))))
    return (cusps_tuple, ascmc_tuple)


def longitude_to_house_number(lon: float, cusps: tuple[float, ...]) -> int:
    """
    Assign longitude to house 1..12 given 12 cusp longitudes (cusps[0]=cusp1 .. cusps[11]=cusp12).
    Deterministic; handles 360 wrap.
    """
    lon_n = _norm360(lon)
    for i in range(12):
        c1 = _norm360(cusps[i])
        c2 = _norm360(cusps[(i + 1) % 12])
        if c1 <= c2:
            if c1 <= lon_n < c2:
                return i + 1
        else:
            if lon_n >= c1 or lon_n < c2:
                return i + 1
    return 12


def angular_strength_for_house(house: int) -> float:
    """Return angular strength in [0, 1] for house 1..12 per contract."""
    if not 1 <= house <= 12:
        return 0.0
    return ANGULAR_STRENGTH_BY_HOUSE[house - 1]


def assign_houses_and_strength(
    positions: list[dict[str, Any]],
    cusps: tuple[float, ...],
) -> list[dict[str, Any]]:
    """
    For each position with "longitude", add "sign" (0..11), "house" (1..12), "angular_strength" (0..1).
    Does not mutate input; returns new list of dicts with extra keys.
    """
    result: list[dict[str, Any]] = []
    for p in positions:
        lon = float(p["longitude"])
        sign_ix = longitude_to_sign_index(lon)
        house = longitude_to_house_number(lon, cusps)
        strength = angular_strength_for_house(house)
        new_p = dict(p)
        new_p["sign"] = sign_ix
        new_p["house"] = house
        new_p["angular_strength"] = round(strength, 6)
        result.append(new_p)
    return result


def longitude_to_sign_index(lon: float) -> int:
    """Longitude [0, 360) → sign index 0..11 (Aries=0, Pisces=11)."""
    return int(_norm360(lon) / 30.0) % 12
