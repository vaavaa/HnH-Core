"""
SignPolarityEngine (Spec 008, FR-005, FR-006, FR-011, FR-012).
Planet-weighted sign polarity score in [-1, +1]. Only planets with known sign.
"""

from __future__ import annotations

from typing import Any

# FR-011: +1 Aries, Gemini, Leo, Libra, Sagittarius, Aquarius; -1 else (Taurus, Cancer, ...)
# Sign index 0..11: Aries=0, Taurus=1, ..., Pisces=11
_POSITIVE_SIGN_INDICES: frozenset[int] = frozenset({0, 2, 4, 6, 8, 10})  # Aries, Gemini, Leo, Libra, Sagittarius, Aquarius


def sign_polarity(sign_index: int) -> int:
    """FR-005: sign_polarity(sign) ∈ {+1, -1}. Input: sign index 0..11 (Aries=0, Pisces=11)."""
    if not 0 <= sign_index <= 11:
        raise ValueError(f"sign_index must be 0..11, got {sign_index}")
    return 1 if sign_index in _POSITIVE_SIGN_INDICES else -1


# FR-012 default planet weights
DEFAULT_PLANET_WEIGHTS: dict[str, float] = {
    "Sun": 2.0,
    "Moon": 2.0,
    "Mercury": 1.5,
    "Venus": 1.5,
    "Mars": 1.5,
    "Jupiter": 1.0,
    "Saturn": 1.0,
    "Uranus": 0.5,
    "Neptune": 0.5,
    "Pluto": 0.5,
}


def sign_polarity_score(
    planet_signs: dict[str, int] | list[tuple[str, int]] | Any,
    weights: dict[str, float] | None = None,
) -> float:
    """
    FR-006: sign_polarity_score = (Σ weight_p × sign_polarity(sign_p)) / (Σ weight_p)
    over planets with known sign only. Returns value in [-1, 1].
    If no planet has a known sign, caller (infer path) must handle (e.g. raise); we do not return a value.
    planet_signs: mapping planet_name -> sign_index (0..11), or list of (name, sign_index).
    weights: planet name -> weight; default FR-012.
    """
    if weights is None:
        weights = DEFAULT_PLANET_WEIGHTS
    if hasattr(planet_signs, "get") and not isinstance(planet_signs, dict):
        planet_signs = getattr(planet_signs, "positions", planet_signs)
    if isinstance(planet_signs, (list, tuple)):
        # list of dicts with "planet" and "sign" or (name, sign_index) pairs
        pairs: list[tuple[str, int]] = []
        for item in planet_signs:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                name, si = item[0], item[1]
                if isinstance(si, int) and 0 <= si <= 11:
                    pairs.append((str(name).strip(), si))
            elif isinstance(item, dict):
                si = item.get("sign")
                if si is not None and 0 <= si <= 11:
                    name = item.get("planet", "")
                    pairs.append((str(name).strip(), int(si)))
        planet_signs = dict(pairs)
    else:
        planet_signs = dict(planet_signs) if isinstance(planet_signs, dict) else {}
    num = 0.0
    den = 0.0
    for name, sign_index in planet_signs.items():
        if not (0 <= sign_index <= 11):
            continue
        w = weights.get(name) if isinstance(weights, dict) else DEFAULT_PLANET_WEIGHTS.get(name)
        if w is None or w <= 0:
            continue
        num += w * sign_polarity(sign_index)
        den += w
    if den <= 0:
        raise ValueError("sign_polarity_score undefined: no planet with known sign (infer mode must fail-fast)")
    return max(-1.0, min(1.0, num / den))
