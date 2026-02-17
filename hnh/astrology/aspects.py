"""
Major aspects and orb configuration (v0.1).
Config-driven orbs; no hardcoded magic constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Major aspects: (name, angle_degrees)
MAJOR_ASPECTS = [
    ("Conjunction", 0.0),
    ("Opposition", 180.0),
    ("Trine", 120.0),
    ("Square", 90.0),
    ("Sextile", 60.0),
]

# Default orbs (degrees) per aspect - can be overridden by config
DEFAULT_ORBS: dict[str, float] = {
    "Conjunction": 8.0,
    "Opposition": 8.0,
    "Trine": 8.0,
    "Square": 7.0,
    "Sextile": 6.0,
}


@dataclass(frozen=True)
class OrbConfig:
    """Orb configuration per aspect (explicit, versioned)."""

    conjunction: float = 8.0
    opposition: float = 8.0
    trine: float = 8.0
    square: float = 7.0
    sextile: float = 6.0

    def get_orb(self, aspect_name: str) -> float:
        orb_map = {
            "Conjunction": self.conjunction,
            "Opposition": self.opposition,
            "Trine": self.trine,
            "Square": self.square,
            "Sextile": self.sextile,
        }
        return orb_map.get(aspect_name, 6.0)


def _normalize_angle(degrees: float) -> float:
    """Normalize longitude to [0, 360)."""
    d = degrees % 360.0
    return d if d >= 0 else d + 360.0


def angular_separation(lon1: float, lon2: float) -> float:
    """Shortest angular separation between two longitudes (0–180)."""
    a = _normalize_angle(lon1)
    b = _normalize_angle(lon2)
    diff = abs(a - b)
    if diff > 180.0:
        diff = 360.0 - diff
    return diff


def detect_aspects(
    positions: list[dict[str, Any]],
    orb_config: OrbConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Detect major aspects between all pairs of positions.
    Returns list of {"planet1", "planet2", "aspect", "angle", "separation", "within_orb"}.
    """
    orb_config = orb_config or OrbConfig()
    aspects_found: list[dict[str, Any]] = []
    for i, p1 in enumerate(positions):
        for p2 in positions[i + 1 :]:  # noqa: E203
            lon1 = p1["longitude"]
            lon2 = p2["longitude"]
            sep = angular_separation(lon1, lon2)
            for aspect_name, angle_deg in MAJOR_ASPECTS:
                orb = orb_config.get_orb(aspect_name)
                if angle_deg == 0:  # Conjunction
                    within = sep <= orb or (360.0 - sep) <= orb
                else:
                    within = abs(sep - angle_deg) <= orb
                if within:
                    aspects_found.append({
                        "planet1": p1["planet"],
                        "planet2": p2["planet"],
                        "aspect": aspect_name,
                        "angle": angle_deg,
                        "separation": round(sep, 6),
                        "within_orb": True,
                    })
    return aspects_found


def aspects_between(
    positions_a: list[dict[str, Any]],
    positions_b: list[dict[str, Any]],
    orb_config: OrbConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Detect major aspects between two sets of positions (e.g. transit vs natal).
    Returns list of {"planet1", "planet2", "aspect", "angle", "separation", "within_orb"}.
    """
    orb_config = orb_config or OrbConfig()
    result: list[dict[str, Any]] = []
    for p1 in positions_a:
        for p2 in positions_b:
            lon1 = p1["longitude"]
            lon2 = p2["longitude"]
            sep = angular_separation(lon1, lon2)
            for aspect_name, angle_deg in MAJOR_ASPECTS:
                orb = orb_config.get_orb(aspect_name)
                if angle_deg == 0:
                    within = sep <= orb or (360.0 - sep) <= orb
                else:
                    within = abs(sep - angle_deg) <= orb
                if within:
                    result.append({
                        "planet1": p1["planet"],
                        "planet2": p2["planet"],
                        "aspect": aspect_name,
                        "angle": angle_deg,
                        "separation": round(sep, 6),
                        "within_orb": True,
                    })
    return result
