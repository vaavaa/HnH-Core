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


def _axis_of_param(param_name: str) -> str | None:
    """Return axis name for parameter, or None if unknown."""
    if param_name not in PARAMETERS:
        return None
    idx = list(PARAMETERS).index(param_name)
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
    param_list = list(PARAMETERS)
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
        for param_name, w in weights[aspect_name].items():
            if param_name not in param_list:
                continue
            # When aspect has planet1/planet2, only params of those axes get delta
            if affected_axes and _axis_of_param(param_name) not in affected_axes:
                continue
            idx = param_list.index(param_name)
            raw[idx] += w * intensity
    return tuple(raw)
