"""
Raw delta calculation for 32 parameters (Spec 002).
raw_delta[p] = Σ(aspect_weight × mapping_weight × intensity_factor).
Only parameters whose axis is in affected_axes (from planet1/planet2) receive delta.
Deterministic; no system clock.
"""

from __future__ import annotations

from typing import Any

from hnh.identity.schema import (
    AXES,
    NUM_PARAMETERS,
    PARAMETERS,
    get_parameter_axis_index,
)

# Planet → axis or axes (names must match schema AXES). One planet can affect multiple axes.
PLANET_AXIS_MAP: dict[str, str | tuple[str, ...]] = {
    "Sun": "power_boundaries",
    "Moon": "emotional_tone",
    "Mercury": "cognitive_style",
    "Venus": "communication_style",
    "Mars": "teaching_style",
    "Jupiter": "motivation_drive",
    "Saturn": ("structure_discipline", "stability_regulation"),
    "Uranus": "cognitive_style",
    "Neptune": "emotional_tone",
    "Pluto": "power_boundaries",
}

# Planet categories for dynamic phase window: погода / сезон / эпоха
PLANET_CATEGORY: dict[str, str] = {
    "Sun": "personal",
    "Moon": "personal",
    "Mercury": "personal",
    "Venus": "personal",
    "Mars": "personal",
    "Jupiter": "social",
    "Saturn": "social",
    "Uranus": "outer",
    "Neptune": "outer",
    "Pluto": "outer",
}
# Rolling window (days) per category
PHASE_WINDOW_DAYS_BY_CATEGORY: dict[str, int] = {
    "personal": 7,   # погода
    "social": 30,    # сезон
    "outer": 365,    # эпоха
}

# Outer planets get higher weight than inner (Mars/Jupiter same as inner).
OUTER_PLANET_MULTIPLIER: dict[str, float] = {
    "Saturn": 1.2,
    "Uranus": 1.4,
    "Neptune": 1.3,
    "Pluto": 1.5,
}

# Default aspect → parameter weights (sparse). Same aspect can affect multiple params.
# Keys: aspect name; value: dict param_name -> weight (float).
# Weights for cognitive_style, structure_discipline, stability_regulation, power_boundaries
# spread across aspect types so those axes get delta when the relevant planet is in the aspect.
_DEFAULT_ASPECT_WEIGHTS_32: dict[str, dict[str, float]] = {
    "Conjunction": {
        "warmth": 0.02,
        "empathy": 0.01,
        "verbosity": 0.01,
        "analytical_depth": 0.01,
        "authority_presence": 0.01,
        "consistency": 0.01,
    },
    "Opposition": {
        "reactivity": 0.02,
        "challenge_level": 0.02,
        "conflict_tolerance": -0.01,
        "structure_preference": -0.01,
        "rule_adherence": -0.01,
        "detail_orientation": -0.01,
    },
    "Trine": {
        "warmth": 0.02,
        "patience": 0.01,
        "encouragement_level": 0.02,
        "pacing": -0.01,
        "detail_orientation": 0.01,
        "tolerance_for_errors": 0.01,
        "planning_bias": 0.01,
    },
    "Square": {
        "reactivity": 0.02,
        "challenge_level": 0.03,
        "correction_intensity": 0.02,
        "stress_response": 0.02,
        "analytical_depth": 0.01,
        "abstraction_level": -0.01,
        "dominance": -0.01,
        "rule_adherence": 0.01,
    },
    "Sextile": {
        "warmth": 0.01,
        "curiosity": 0.01,
        "encouragement_level": 0.01,
        "big_picture_focus": 0.01,
        "authority_presence": 0.01,
        "structure_preference": 0.01,
    },
}


# Name → index once (avoid repeated list(PARAMETERS).index in loops)
_PARAM_NAME_TO_INDEX: dict[str, int] = {p: i for i, p in enumerate(PARAMETERS)}


def _axis_of_param(param_name: str) -> str | None:
    """Return axis name for parameter, or None if unknown."""
    idx = _PARAM_NAME_TO_INDEX.get(param_name)
    if idx is None:
        return None
    axis_ix = get_parameter_axis_index(idx)
    return AXES[axis_ix]


def _intensity_factor(aspect: dict[str, Any], orb_scale: float = 1.0) -> float:
    """
    Intensity from exactness of aspect. Exact = 1.0; at orb edge = 0.0.
    orb_scale: optional config (default 1.0).
    """
    separation = aspect.get("separation")
    angle = aspect.get("angle", 0.0)
    if separation is None:
        return 1.0
    # Distance from exact angle (0 = exact)
    if angle == 0.0:  # Conjunction
        dev = min(separation, 360.0 - separation)
    else:
        dev = abs(separation - angle)
    # Assume orb ~8°; intensity = 1 - dev/8 (linear falloff)
    orb = 8.0 * orb_scale
    if orb <= 0:
        return 1.0
    return max(0.0, 1.0 - dev / orb)


def compute_raw_delta_32(
    aspects_to_natal: list[dict[str, Any]],
    aspect_weights: dict[str, dict[str, float]] | None = None,
    orb_scale: float = 1.0,
) -> tuple[float, ...]:
    """
    Map transit–natal aspects to raw_delta vector (32 params).
    Only parameters whose axis is in {axis(planet1), axis(planet2)} receive delta.
    Formula: raw_delta[p] = Σ(aspect_weight × mapping_weight × intensity_factor).
    Deterministic; same aspects → same output.
    """
    weights = aspect_weights or _DEFAULT_ASPECT_WEIGHTS_32
    raw = [0.0] * NUM_PARAMETERS
    for asp in aspects_to_natal:
        aspect_name = asp.get("aspect", "")
        if aspect_name not in weights:
            continue
        planet1 = asp.get("planet1")
        planet2 = asp.get("planet2")
        axis1 = PLANET_AXIS_MAP.get(planet1) if planet1 else None
        axis2 = PLANET_AXIS_MAP.get(planet2) if planet2 else None
        affected_axes: set[str] = set()
        for ax in (axis1, axis2):
            if ax is None:
                continue
            if isinstance(ax, str):
                affected_axes.add(ax)
            else:
                affected_axes.update(ax)
        has_planet_info = planet1 is not None or planet2 is not None
        if has_planet_info and not affected_axes:
            # Planet fields exist but none are mapped → don't affect any axis
            continue
        intensity = _intensity_factor(asp, orb_scale)
        outer_mul = max(
            OUTER_PLANET_MULTIPLIER.get(planet1, 1.0),
            OUTER_PLANET_MULTIPLIER.get(planet2, 1.0),
        )
        for param_name, w in weights[aspect_name].items():
            idx = _PARAM_NAME_TO_INDEX.get(param_name)
            if idx is None:
                continue
            # When aspect has planet1/planet2, only params of those axes get delta
            if affected_axes and _axis_of_param(param_name) not in affected_axes:
                continue
            raw[idx] += w * intensity * outer_mul
    return tuple(raw)


def _aspect_category(asp: dict[str, Any]) -> str:
    """Assign aspect to one category: outer > social > personal (slowest planet wins)."""
    p1 = asp.get("planet1")
    p2 = asp.get("planet2")
    c1 = PLANET_CATEGORY.get(p1, "personal")
    c2 = PLANET_CATEGORY.get(p2, "personal")
    if c1 == "outer" or c2 == "outer":
        return "outer"
    if c1 == "social" or c2 == "social":
        return "social"
    return "personal"


def compute_raw_delta_32_by_category(
    aspects_to_natal: list[dict[str, Any]],
    aspect_weights: dict[str, dict[str, float]] | None = None,
    orb_scale: float = 1.0,
) -> dict[str, tuple[float, ...]]:
    """
    Split aspects by planet category (personal/social/outer); return raw_delta per category.
    Each aspect counted in exactly one category. Sum of the three = compute_raw_delta_32(all).
    """
    by_cat: dict[str, list[dict[str, Any]]] = {"personal": [], "social": [], "outer": []}
    for asp in aspects_to_natal:
        cat = _aspect_category(asp)
        by_cat[cat].append(asp)
    return {
        cat: compute_raw_delta_32(by_cat[cat], aspect_weights=aspect_weights, orb_scale=orb_scale)
        for cat in ("personal", "social", "outer")
    }
