"""
W_age v1 (5×32) and compute_age_delta_32, apply_daily_lipschitz. Spec 010.
Canonical feature order: maturity, saturn_event, jupiter_return, nodal_return, uranus_opposition.
"""

from __future__ import annotations

from hnh.identity.schema import NUM_PARAMETERS, get_parameter_index

# Feature index: 0=maturity, 1=saturn_event, 2=jupiter_return, 3=nodal_return, 4=uranus_opposition
# Sparse W_age v1 from spec § Mapping age stages to 32 parameters
_W_AGE_SPARSE: list[tuple[int, str, float]] = [
    # maturity (j=0)
    (0, "patience", 0.6),
    (0, "resilience", 0.5),
    (0, "analytical_depth", 0.3),
    (0, "big_picture_focus", 0.2),
    (0, "structure_preference", 0.6),
    (0, "consistency", 0.5),
    (0, "rule_adherence", 0.5),
    (0, "planning_bias", 0.4),
    (0, "authority_presence", 0.3),
    (0, "pacing", 0.3),
    (0, "explanation_bias", 0.2),
    (0, "reactivity", -0.4),
    (0, "emotional_intensity", -0.4),
    (0, "verbosity", -0.2),
    # saturn_event (j=1)
    (1, "rule_adherence", 0.6),
    (1, "planning_bias", 0.4),
    (1, "correction_intensity", 0.4),
    (1, "tolerance_for_errors", -0.4),
    (1, "warmth", -0.2),
    # jupiter_return (j=2)
    (2, "warmth", 0.3),
    (2, "curiosity", 0.6),
    (2, "ambition", 0.4),
    (2, "initiative", 0.4),
    (2, "encouragement_level", 0.3),
    (2, "big_picture_focus", 0.2),
    # nodal_return (j=3)
    (3, "persistence", 0.5),
    (3, "initiative", 0.3),
    (3, "big_picture_focus", 0.3),
    (3, "abstraction_level", 0.2),
    (3, "authority_presence", 0.1),
    # uranus_opposition (j=4)
    (4, "directness", 0.4),
    (4, "questioning_frequency", 0.5),
    (4, "conflict_tolerance", 0.4),
    (4, "consistency", -0.3),
    (4, "rule_adherence", -0.4),
    (4, "reactivity", 0.2),
    (4, "initiative", 0.2),
]

# Build 5×32 matrix: W_age[j][i] = weight for feature j, parameter i
_W_AGE: list[list[float]] = [[0.0] * NUM_PARAMETERS for _ in range(5)]
for (j, param_name, w) in _W_AGE_SPARSE:
    i = get_parameter_index(param_name)
    _W_AGE[j][i] = w


def compute_age_delta_32(
    features: tuple[float, ...],
    age_strength: float,
    age_max_param_delta: float,
) -> tuple[float, ...]:
    """
    raw[i] = age_strength * sum_j (features[j] * W_age[j][i]);
    age_delta_32[i] = clamp(raw[i], -age_max_param_delta, +age_max_param_delta).
    features length must be 5. Returns length 32.
    """
    if len(features) != 5:
        raise ValueError(f"features must have length 5, got {len(features)}")
    result: list[float] = [0.0] * NUM_PARAMETERS
    for i in range(NUM_PARAMETERS):
        raw = age_strength * sum(features[j] * _W_AGE[j][i] for j in range(5))
        result[i] = max(
            -age_max_param_delta,
            min(age_max_param_delta, raw),
        )
    return tuple(result)


def apply_daily_lipschitz(
    prev_delta_32: tuple[float, ...] | None,
    raw_delta_32: tuple[float, ...],
    L: float,
) -> tuple[float, ...]:
    """
    Per-call Lipschitz: |age_delta_32[i] - prev[i]| <= L per component.
    If prev_delta_32 is None, return raw_delta_32 unchanged.
    Otherwise: for each i, clip (raw_delta_32[i] - prev_delta_32[i]) to [-L, +L], then add to prev.
    """
    if prev_delta_32 is None:
        return raw_delta_32
    if len(prev_delta_32) != NUM_PARAMETERS or len(raw_delta_32) != NUM_PARAMETERS:
        raise ValueError(
            f"prev_delta_32 and raw_delta_32 must have length {NUM_PARAMETERS}"
        )
    result: list[float] = []
    for i in range(NUM_PARAMETERS):
        diff = raw_delta_32[i] - prev_delta_32[i]
        clipped = max(-L, min(L, diff))
        result.append(prev_delta_32[i] + clipped)
    return tuple(result)
