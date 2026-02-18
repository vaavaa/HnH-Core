"""
Delta boundaries: hierarchy resolution and clamping (Spec 002 T4.3, T4.4).
bounded_delta[p] = clamp(raw_delta[p], -effective_max_delta[p], +effective_max_delta[p]).
Shock: effective_max_delta = max_delta × shock_multiplier (cap 2.0).
"""

from __future__ import annotations

from hnh.config.replay_config import ReplayConfig, resolve_max_delta
from hnh.identity.schema import AXES, NUM_PARAMETERS, PARAMETERS, get_parameter_axis_index


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
    effective: list[float] = []
    bounded: list[float] = []
    for p_ix in range(NUM_PARAMETERS):
        axis_ix = get_parameter_axis_index(p_ix)
        axis_name = AXES[axis_ix]
        max_d = resolve_max_delta(p_ix, config, axis_name)
        eff = max_d * multiplier
        effective.append(eff)
        raw_val = raw_delta[p_ix]
        bounded.append(max(-eff, min(eff, raw_val)))
    return (tuple(bounded), tuple(effective))
