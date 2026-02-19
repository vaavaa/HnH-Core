"""
Transit stress I_T(t), S_T(t) for Lifecycle 005. Contract: contracts/transit-stress.md.
Hard aspects only; orb_decay = max(0, 1 - dev/orb). Deterministic.
"""

from __future__ import annotations

from typing import Any

from hnh.lifecycle.constants import C_T_DEFAULT, HARD_ASPECTS, HARD_ASPECT_WEIGHT_DEFAULT

# Default orbs (degrees) for orb_decay; align with astrology DEFAULT_ORBS
_DEFAULT_ORBS: dict[str, float] = {
    "Conjunction": 8.0,
    "Opposition": 8.0,
    "Square": 7.0,
}


def _orb_decay(aspect: dict[str, Any], orb: float) -> float:
    """Linear falloff: exact = 1.0, at orb edge = 0.0. orb > 0 required."""
    separation = aspect.get("separation")
    angle = aspect.get("angle", 0.0)
    if separation is None:
        return 1.0
    if orb <= 0:
        return 1.0
    if angle == 0.0:  # Conjunction
        dev = min(separation, 360.0 - separation)
    else:
        dev = abs(separation - angle)
    return max(0.0, 1.0 - dev / orb)


def compute_raw_transit_intensity(
    aspects_to_natal: list[dict[str, Any]],
    hard_aspect_weights: dict[str, float] | None = None,
    orbs: dict[str, float] | None = None,
) -> float:
    """
    I_T(t) = Σ (hard_aspect_weight × orb_decay) over hard aspects only.
    Deterministic; same aspects → same result.
    """
    weights = hard_aspect_weights or {a: HARD_ASPECT_WEIGHT_DEFAULT for a in HARD_ASPECTS}
    orbs_map = orbs or _DEFAULT_ORBS
    total = 0.0
    for asp in aspects_to_natal:
        name = asp.get("aspect", "")
        if name not in HARD_ASPECTS:
            continue
        orb = orbs_map.get(name, 8.0)
        decay = _orb_decay(asp, orb)
        w = weights.get(name, HARD_ASPECT_WEIGHT_DEFAULT)
        total += w * decay
    return total


def compute_transit_stress(
    aspects_to_natal: list[dict[str, Any]],
    c_t: float = C_T_DEFAULT,
    hard_aspect_weights: dict[str, float] | None = None,
    orbs: dict[str, float] | None = None,
) -> tuple[float, float]:
    """
    Returns (I_T, S_T). S_T = clip(I_T / C_T, 0, 1). Deterministic.
    """
    i_t = compute_raw_transit_intensity(aspects_to_natal, hard_aspect_weights, orbs)
    s_t = max(0.0, min(1.0, i_t / c_t))
    return (i_t, s_t)
