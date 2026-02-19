"""
Zodiac Expression Layer (Spec 004).
12 signs × 4 dimensions (intensity, stability, expressiveness, adaptability).
Read-only; derived from positions and aspects; no impact on 32 behavioral parameters.
"""

from __future__ import annotations

from typing import Any

# Contract 004 sign-rulers: Modern default. Sign index 0..11 → ruler planet name.
SIGN_RULER_MODERN: tuple[str, ...] = (
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Pluto", "Jupiter", "Saturn", "Uranus", "Neptune",
)

# Element (Fire, Earth, Air, Water) → sign indices. Spec §9: dominant_element = element with max sum of intensity.
ELEMENT_SIGNS: tuple[tuple[int, ...], ...] = (
    (0, 4, 8),   # Fire: Aries, Leo, Sagittarius
    (1, 5, 9),   # Earth: Taurus, Virgo, Capricorn
    (2, 6, 10),  # Air: Gemini, Libra, Aquarius
    (3, 7, 11),  # Water: Cancer, Scorpio, Pisces
)
ELEMENT_NAMES: tuple[str, ...] = ("Fire", "Earth", "Air", "Water")

# Sign index 0..11 → element name (for display: element OF the dominant sign).
SIGN_TO_ELEMENT: tuple[str, ...] = (
    "Fire", "Earth", "Air", "Water",   # 0–3: Aries, Taurus, Gemini, Cancer
    "Fire", "Earth", "Air", "Water",   # 4–7: Leo, Virgo, Libra, Scorpio
    "Fire", "Earth", "Air", "Water",   # 8–11: Sagittarius, Capricorn, Aquarius, Pisces
)

# Hard vs soft aspects for tension/harmony. Spec: intensity ← hard_aspects_weight; stability/adaptability ← tension_vs_harmony.
HARD_ASPECTS: frozenset[str] = frozenset({"Conjunction", "Opposition", "Square"})
SOFT_ASPECTS: frozenset[str] = frozenset({"Trine", "Sextile"})

# Normalization: max planets 10; max aspect count per sign we cap for normalization.
MAX_PLANETS = 10
MAX_ASPECT_WEIGHT = 10.0


def _positions_by_planet(positions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build planet name → position dict (with sign, house, angular_strength)."""
    by_planet: dict[str, dict[str, Any]] = {}
    for p in positions:
        name = p.get("planet")
        if name is not None:
            by_planet[name] = p
    return by_planet


def _planets_per_sign(positions: list[dict[str, Any]]) -> tuple[tuple[str, ...], ...]:
    """For each sign 0..11, tuple of planet names in that sign."""
    per_sign: list[list[str]] = [list() for _ in range(12)]
    for p in positions:
        sign_ix = p.get("sign")
        if sign_ix is not None and 0 <= sign_ix <= 11:
            per_sign[sign_ix].append(p.get("planet", ""))
    return tuple(tuple(x) for x in per_sign)


def _ruler_strength_for_sign(sign_ix: int, positions_by_planet: dict[str, dict[str, Any]]) -> float:
    """Strength of sign ruler: angular_strength of ruler planet; [0, 1]."""
    ruler = SIGN_RULER_MODERN[sign_ix]
    pos = positions_by_planet.get(ruler)
    if pos is None:
        return 0.0
    strength = pos.get("angular_strength")
    if strength is None:
        return 0.0
    return max(0.0, min(1.0, float(strength)))


def _aspect_counts_for_sign(
    sign_ix: int,
    planets_in_sign: tuple[str, ...],
    positions_by_planet: dict[str, dict[str, Any]],
    aspects: list[dict[str, Any]],
) -> tuple[int, int]:
    """Return (hard_count, soft_count) for aspects involving planets in this sign (or ruler if sign empty)."""
    if planets_in_sign:
        relevant = set(planets_in_sign)
    else:
        ruler = SIGN_RULER_MODERN[sign_ix]
        relevant = {ruler} if ruler in positions_by_planet else set()
    hard = 0
    soft = 0
    for a in aspects:
        p1 = a.get("planet1", "")
        p2 = a.get("planet2", "")
        if p1 not in relevant and p2 not in relevant:
            continue
        name = a.get("aspect", "")
        if name in HARD_ASPECTS:
            hard += 1
        elif name in SOFT_ASPECTS:
            soft += 1
    return (hard, soft)


def _angular_weighting_for_sign(
    planets_in_sign: tuple[str, ...],
    positions_by_planet: dict[str, dict[str, Any]],
) -> float:
    """Average angular_strength of planets in sign; 0 if none. [0, 1]."""
    if not planets_in_sign:
        return 0.0
    total = 0.0
    for name in planets_in_sign:
        p = positions_by_planet.get(name)
        if p is not None:
            a = p.get("angular_strength")
            if a is not None:
                total += float(a)
    return max(0.0, min(1.0, total / len(planets_in_sign)))


def compute_zodiac_expression(
    positions: list[dict[str, Any]],
    aspects: list[dict[str, Any]],
) -> tuple[list[tuple[float, float, float, float]], int, str]:
    """
    Compute sign_energy_vector (12×4), dominant_sign, dominant_element.
    Positions: list of dicts with planet, longitude, sign, house, angular_strength.
    Aspects: list of dicts with planet1, planet2, aspect.
    Returns (sign_energy_vector, dominant_sign_index, dominant_element_name).
    Deterministic; all values in [0, 1]; no read of params_final/base.
    """
    positions_by_planet = _positions_by_planet(positions)
    planets_per_sign = _planets_per_sign(positions)

    sign_energy_vector: list[tuple[float, float, float, float]] = []
    for sign_ix in range(12):
        planets_in_sign = planets_per_sign[sign_ix]
        n_planets = len(planets_in_sign)

        # Inputs per spec §4.2
        ruler_str = _ruler_strength_for_sign(sign_ix, positions_by_planet)
        hard, soft = _aspect_counts_for_sign(sign_ix, planets_in_sign, positions_by_planet, aspects)
        angular_w = _angular_weighting_for_sign(planets_in_sign, positions_by_planet)

        # Normalize to [0,1]
        planetary_presence = n_planets / MAX_PLANETS if MAX_PLANETS else 0.0
        hard_norm = min(1.0, hard / 5.0)  # cap at 5 aspects
        # Tension vs harmony balance: (soft+1)/(hard+soft+2) → more harmony = higher
        total_aspects = hard + soft
        if total_aspects == 0:
            tension_harmony_balance = 0.5
        else:
            tension_harmony_balance = (soft + 1.0) / (total_aspects + 2.0)
        tension_harmony_balance = max(0.0, min(1.0, tension_harmony_balance))

        # Dimension mapping per spec §4.2
        intensity = 0.5 * planetary_presence + 0.5 * hard_norm
        stability = 0.5 * ruler_str + 0.5 * tension_harmony_balance
        expressiveness = 0.5 * planetary_presence + 0.5 * angular_w
        adaptability = tension_harmony_balance

        # Clamp to [0,1]
        intensity = max(0.0, min(1.0, intensity))
        stability = max(0.0, min(1.0, stability))
        expressiveness = max(0.0, min(1.0, expressiveness))
        adaptability = max(0.0, min(1.0, adaptability))

        sign_energy_vector.append((intensity, stability, expressiveness, adaptability))

    # dominant_sign: sign with maximum intensity (spec §9)
    dominant_sign = 0
    max_intensity = sign_energy_vector[0][0]
    for sign_ix in range(1, 12):
        if sign_energy_vector[sign_ix][0] > max_intensity:
            max_intensity = sign_energy_vector[sign_ix][0]
            dominant_sign = sign_ix

    # dominant_element: element with max sum of intensity over its 3 signs (spec §9)
    element_sums: list[float] = []
    for elem_inds in ELEMENT_SIGNS:
        s = sum(sign_energy_vector[i][0] for i in elem_inds)
        element_sums.append(s)
    dominant_element_ix = 0
    for e in range(1, 4):
        if element_sums[e] > element_sums[dominant_element_ix]:
            dominant_element_ix = e
    dominant_element = ELEMENT_NAMES[dominant_element_ix]

    return (sign_energy_vector, dominant_sign, dominant_element)


def compute_zodiac_output(
    positions: list[dict[str, Any]],
    aspects: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Entry point: returns sign_energy_vector, dominant_sign, dominant_element.
    Positions must include sign, house, angular_strength (e.g. from natal).
    dominant_element = element with max sum of intensity (spec §9).
    dominant_sign_element = element of the dominant sign (for display: Scorpio → Water).
    """
    sign_energy_vector, dominant_sign, dominant_element = compute_zodiac_expression(positions, aspects)
    return {
        "sign_energy_vector": sign_energy_vector,
        "dominant_sign": dominant_sign,
        "dominant_sign_name": _sign_index_to_name(dominant_sign),
        "dominant_sign_element": SIGN_TO_ELEMENT[dominant_sign] if 0 <= dominant_sign <= 11 else "",
        "dominant_element": dominant_element,
    }


def _sign_index_to_name(sign_ix: int) -> str:
    """Sign index 0..11 → name (Aries..Pisces)."""
    names = (
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    )
    return names[sign_ix] if 0 <= sign_ix <= 11 else ""
