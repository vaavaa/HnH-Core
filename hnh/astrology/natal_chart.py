"""
NatalChart: immutable birth chart from birth_data (Spec 006).
Builds via ephemeris/houses/aspects; stores planets and aspects as tuples.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from hnh.astrology import aspects as asp
from hnh.astrology.aspect_model import Aspect, aspect_from_dict
from hnh.astrology.planet import Planet

# Optional: use core.natal for variant A (datetime + lat/lon)
try:
    from hnh.core.natal import build_natal_positions
except ImportError:
    build_natal_positions = None  # type: ignore[assignment]


def _parse_birth_data(birth_data: dict[str, Any]) -> tuple[tuple[Planet, ...], tuple[Aspect, ...], dict[str, Any]]:
    """
    Build (planets, aspects, natal_data) from birth_data.
    Variant A: datetime_utc, lat, lon -> ephemeris + houses + aspects.
    Variant B: positions (list/tuple of dicts), optional aspects.
    Returns immutable tuples and legacy natal_data dict for downstream.
    """
    if "positions" in birth_data:
        # Variant B: ready positions
        positions = birth_data["positions"]
        if hasattr(positions, "__iter__") and not isinstance(positions, dict):
            positions = list(positions)
        else:
            positions = []
        aspects_raw = birth_data.get("aspects") or []
        orb_config = getattr(asp, "OrbConfig", None)
        if not aspects_raw and positions and asp.detect_aspects:
            aspects_raw = asp.detect_aspects(
                [{"planet": p.get("planet", ""), "longitude": float(p.get("longitude", 0))} for p in positions],
                orb_config() if orb_config else None,
            )
        planets_list: list[Planet] = []
        for p in positions:
            name = p.get("planet", "")
            lon = float(p.get("longitude", 0))
            house = p.get("house") if p.get("house") is not None else None
            if isinstance(house, (int, float)):
                house = int(house)
            else:
                house = None
            planets_list.append(Planet(name=name, longitude=lon, house=house))
        aspects_list = [aspect_from_dict(a) for a in aspects_raw]
        # Build full positions (sign, house, angular_strength) for legacy format
        from hnh.astrology.houses import ANGULAR_STRENGTH_BY_HOUSE
        full_positions = []
        for pl in planets_list:
            h = pl.house or 0
            strength = ANGULAR_STRENGTH_BY_HOUSE[h - 1] if 1 <= h <= 12 else 0.0
            full_positions.append({
                "planet": pl.name,
                "longitude": pl.longitude,
                "sign": pl.sign_index,
                "house": h,
                "angular_strength": round(strength, 6),
            })
        natal_data = {"positions": full_positions, "aspects": aspects_raw}
        return (tuple(planets_list), tuple(aspects_list), natal_data)

    # Variant A: datetime_utc, lat, lon
    if build_natal_positions is None:
        raise RuntimeError("Variant A (datetime_utc, lat, lon) requires hnh.core.natal.build_natal_positions")
    dt = birth_data.get("datetime_utc")
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    if dt is None:
        raise ValueError("datetime_utc is required for Variant A (datetime_utc, lat, lon)")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    lat = float(birth_data["lat"])
    lon = float(birth_data["lon"])
    orb_config = getattr(asp, "OrbConfig", None)()
    raw = build_natal_positions(dt, lat, lon, orb_config)
    positions = raw.get("positions", [])
    aspects_raw = raw.get("aspects", [])
    planets_list = []
    for p in positions:
        planets_list.append(Planet(
            name=p.get("planet", ""),
            longitude=float(p.get("longitude", 0)),
            house=int(p["house"]) if p.get("house") is not None else None,
        ))
    aspects_list = [aspect_from_dict(a) for a in aspects_raw]
    return (tuple(planets_list), tuple(aspects_list), raw)


@dataclass(frozen=True)
class NatalChart:
    """
    Immutable natal chart. Planets and aspects stored as tuples (no lists).
    Built from birth_data (variant A: datetime_utc, lat, lon; variant B: positions [, aspects]).
    """

    planets: tuple[Planet, ...]
    aspects: tuple[Aspect, ...]
    _natal_data: tuple[dict[str, Any], ...]  # internal cache for to_natal_data; single-element tuple to be hashable

    def __post_init__(self) -> None:
        # Ensure we have _natal_data; avoid mutable default
        if not hasattr(self, "_natal_data") or not self._natal_data:
            object.__setattr__(self, "_natal_data", (self._build_natal_data(),))

    def _build_natal_data(self) -> dict[str, Any]:
        """Build legacy natal_data dict from planets and aspects."""
        from hnh.astrology.houses import ANGULAR_STRENGTH_BY_HOUSE

        positions = []
        for p in self.planets:
            house = p.house or 0
            strength = ANGULAR_STRENGTH_BY_HOUSE[house - 1] if 1 <= house <= 12 else 0.0
            positions.append({
                "planet": p.name,
                "longitude": p.longitude,
                "sign": p.sign_index,
                "house": house,
                "angular_strength": round(strength, 6),
            })
        aspects = [
            {"planet1": a.planet_a, "planet2": a.planet_b, "aspect": a.type, "angle": a.angle, "separation": a.separation}
            for a in self.aspects
        ]
        return {"positions": positions, "aspects": aspects}

    @classmethod
    def from_birth_data(cls, birth_data: dict[str, Any]) -> NatalChart:
        """Build NatalChart from birth_data (variant A or B). Deterministic."""
        planets, aspects, natal_data = _parse_birth_data(birth_data)
        return cls(planets=planets, aspects=aspects, _natal_data=(natal_data,))

    def to_natal_data(self) -> dict[str, Any]:
        """Legacy format for sensitivity/replay: positions + aspects (list of dicts)."""
        return self._natal_data[0] if self._natal_data else self._build_natal_data()

    def compute_base_energy(self) -> dict[str, Any]:
        """Export for next layer: same as to_natal_data (positions for BehavioralCore/identity)."""
        return self.to_natal_data()
