"""
Aspect: angle between two planets/longitudes, type classification (Spec 006).
tension_score() for hard aspects per transit-stress contract 005.
"""

from __future__ import annotations

from dataclasses import dataclass
from hnh.astrology.aspects import DEFAULT_ORBS, OrbConfig
from hnh.lifecycle.constants import (
    HARD_ASPECTS,
    HARD_ASPECT_WEIGHT_DEFAULT,
)


def _orb_decay(separation: float, angle_exact: float, orb: float) -> float:
    """Linear falloff: exact = 1.0, at orb edge = 0.0. orb > 0 required."""
    if orb <= 0:
        return 1.0
    if angle_exact == 0.0:  # Conjunction
        dev = min(separation, 360.0 - separation)
    else:
        dev = abs(separation - angle_exact)
    return max(0.0, 1.0 - dev / orb)


@dataclass(frozen=True)
class Aspect:
    """
    Immutable aspect: two planets (or longitudes), angle between, aspect type.
    tension_score() for hard aspects (Conjunction, Opposition, Square) per contract 005.
    """

    planet_a: str  # planet name or "lon" for longitude pair
    planet_b: str
    angle: float  # exact angle in degrees (0, 60, 90, 120, 180)
    type: str  # Conjunction, Opposition, Square, Trine, Sextile
    separation: float  # actual angular separation in degrees [0, 180]

    def tension_score(
        self,
        orb_config: OrbConfig | None = None,
        hard_weights: dict[str, float] | None = None,
    ) -> float:
        """
        Tension score for transit-stress contract (005): hard aspects only.
        Returns weight * orb_decay; 0 for non-hard aspects.
        """
        if self.type not in HARD_ASPECTS:
            return 0.0
        orb = orb_config.get_orb(self.type) if orb_config else DEFAULT_ORBS.get(self.type, 8.0)
        weight = (hard_weights or {}).get(self.type, HARD_ASPECT_WEIGHT_DEFAULT)
        decay = _orb_decay(self.separation, self.angle, orb)
        return weight * decay


def aspect_from_dict(a: dict) -> Aspect:
    """Build Aspect from legacy dict (planet1, planet2, aspect, angle, separation)."""
    return Aspect(
        planet_a=a.get("planet1", ""),
        planet_b=a.get("planet2", ""),
        angle=float(a.get("angle", 0)),
        type=a.get("aspect", "Conjunction"),
        separation=float(a.get("separation", 0)),
    )
