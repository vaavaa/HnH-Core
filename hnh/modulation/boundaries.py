"""
Delta boundaries: hierarchy resolution and clamping (Spec 002 T4.3, T4.4).
bounded_delta[p] = clamp(raw_delta[p], -effective_max_delta[p], +effective_max_delta[p]).
Shock: effective_max_delta = max_delta × shock_multiplier (cap 2.0).
"""

from __future__ import annotations

from hnh.config.replay_config import ReplayConfig, resolve_max_delta
from hnh.identity.schema import AXES, NUM_PARAMETERS, get_parameter_axis_index

# Имя оси для каждого параметра (0..31), один раз при загрузке — без вызовов get_parameter_axis_index в цикле
_PARAM_AXIS_NAME: tuple[str, ...] = tuple(
    AXES[get_parameter_axis_index(p_ix)] for p_ix in range(NUM_PARAMETERS)
)


def apply_bounds(
    raw_delta: tuple[float, ...],
    config: ReplayConfig,
    shock_active: bool = False,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """
    Apply hierarchy and optional shock to get effective_max_delta per param,
    then clamp raw_delta to bounded_delta.
    Returns (bounded_delta, effective_max_delta) both length 32.
    """
    if len(raw_delta) != NUM_PARAMETERS:
        raise ValueError(f"raw_delta length must be {NUM_PARAMETERS}, got {len(raw_delta)}")
    multiplier = config.shock_multiplier if shock_active else 1.0
    effective = [0.0] * NUM_PARAMETERS
    bounded = [0.0] * NUM_PARAMETERS
    for p_ix in range(NUM_PARAMETERS):
        max_d = resolve_max_delta(p_ix, config, _PARAM_AXIS_NAME[p_ix])
        eff = max_d * multiplier
        effective[p_ix] = eff
        raw_val = raw_delta[p_ix]
        bounded[p_ix] = max(-eff, min(eff, raw_val))
    return (tuple(bounded), tuple(effective))
