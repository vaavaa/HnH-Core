"""
Raw delta calculation for 32 parameters (Spec 002).
raw_delta[p] = Σ(aspect_weight × mapping_weight × intensity_factor).
Deterministic; no system clock.
"""

from __future__ import annotations

from typing import Any

from hnh.identity.schema import NUM_PARAMETERS, PARAMETERS

# Default aspect → parameter weights (sparse). Same aspect can affect multiple params.
# Keys: aspect name; value: dict param_name -> weight (float).
_DEFAULT_ASPECT_WEIGHTS_32: dict[str, dict[str, float]] = {
    "Conjunction": {"warmth": 0.02, "empathy": 0.01, "verbosity": 0.01},
    "Opposition": {"reactivity": 0.02, "challenge_level": 0.02, "conflict_tolerance": -0.01},
    "Trine": {"warmth": 0.02, "patience": 0.01, "encouragement_level": 0.02, "pacing": -0.01},
    "Square": {"reactivity": 0.02, "challenge_level": 0.03, "correction_intensity": 0.02, "stress_response": 0.02},
    "Sextile": {"warmth": 0.01, "curiosity": 0.01, "encouragement_level": 0.01},
}


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
        intensity = _intensity_factor(asp, orb_scale)
        for param_name, w in weights[aspect_name].items():
            if param_name in param_list:
                idx = param_list.index(param_name)
                raw[idx] += w * intensity
    return tuple(raw)
