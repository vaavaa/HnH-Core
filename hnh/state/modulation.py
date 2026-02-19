"""
Aspect→parameter weight config and base + modulation merge.
Deterministic: same natal + transit → same behavioral vector.
"""

from __future__ import annotations

from typing import Any

from hnh.core.parameters import BehavioralVector

# Default aspect→dimension weights (small deltas; config-driven, no magic constants)
# Key: aspect name, value: dict of dimension -> delta (float)
DEFAULT_ASPECT_WEIGHTS: dict[str, dict[str, float]] = {
    "Conjunction": {"warmth": 0.02, "verbosity": 0.01},
    "Opposition": {"strictness": 0.03, "challenge_intensity": 0.02},
    "Trine": {"warmth": 0.02, "humor_level": 0.02, "pacing": -0.01},
    "Square": {"strictness": 0.02, "challenge_intensity": 0.03, "correction_rate": 0.02},
    "Sextile": {"warmth": 0.01, "humor_level": 0.01},
}

DIMENSION_NAMES = (
    "warmth",
    "strictness",
    "verbosity",
    "correction_rate",
    "humor_level",
    "challenge_intensity",
    "pacing",
)


def aggregate_aspect_modifiers(
    aspects_to_natal: list[dict[str, Any]],
    aspect_weights: dict[str, dict[str, float]] | None = None,
) -> dict[str, float]:
    """
    Map list of transit–natal aspects to a single modifier vector (7 dims).
    Returns dict dimension -> delta (sum of weights per aspect type).
    """
    weights = aspect_weights or DEFAULT_ASPECT_WEIGHTS
    delta: dict[str, float] = {d: 0.0 for d in DIMENSION_NAMES}
    for a in aspects_to_natal:
        aspect_name = a.get("aspect", "")
        if aspect_name not in weights:
            continue
        for dim, w in weights[aspect_name].items():
            if dim in delta:
                delta[dim] += w
    return delta


def merge_vectors(
    base: BehavioralVector,
    transit_delta: dict[str, float],
    relational_modifier: dict[str, float] | None = None,
) -> BehavioralVector:
    """
    Merge base vector with transit delta and optional relational modifier.
    Result kept in [0, 1]. Rejects relational_modifier values outside [0, 1] (FR-006).
    """
    base_dict = base.to_dict()
    result: dict[str, float] = {}
    for dim in DIMENSION_NAMES:
        val = base_dict[dim] + transit_delta.get(dim, 0.0)
        if relational_modifier is not None:
            v = relational_modifier.get(dim)
            if v is not None:
                if not (0.0 <= v <= 1.0):
                    raise ValueError(
                        f"Relational modifier dimension {dim!r} must be in [0, 1], got {v}"
                    )
                val = (val + v) / 2.0
        result[dim] = max(0.0, min(1.0, val))
    return BehavioralVector(**result)
