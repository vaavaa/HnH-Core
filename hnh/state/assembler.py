"""
State assembly for 32-parameter model (Spec 002).
final[p] = clamp01(base[p] + transit_effect[p] + memory_delta[p]).
Default transit_effect = bounded_delta[p] × sensitivity[p]; optional precomputed (e.g. 0.7*daily + 0.3*phase).
Axis aggregation: axis_final = mean(final sub-parameters). Deterministic.
"""

from __future__ import annotations

from hnh.identity.schema import NUM_PARAMETERS, NUM_AXES, _PARAMETER_LIST


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def assemble_state(
    base_vector: tuple[float, ...],
    sensitivity_vector: tuple[float, ...],
    bounded_delta: tuple[float, ...],
    memory_delta: tuple[float, ...] | None = None,
    *,
    precomputed_transit_effect: tuple[float, ...] | None = None,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """
    Compute params_final (32) and axis_final (8).
    Formula: final[p] = clamp01(base[p] + transit_effect[p] + memory_delta[p]).
    transit_effect = precomputed_transit_effect if provided, else bounded_delta[p]*sensitivity_vector[p].
    memory_delta default: zeros.
    """
    if len(base_vector) != NUM_PARAMETERS or len(sensitivity_vector) != NUM_PARAMETERS or len(bounded_delta) != NUM_PARAMETERS:
        raise ValueError(f"Vectors must have length {NUM_PARAMETERS}")
    mem = memory_delta if memory_delta is not None else (0.0,) * NUM_PARAMETERS
    if len(mem) != NUM_PARAMETERS:
        raise ValueError(f"memory_delta length must be {NUM_PARAMETERS}")
    if precomputed_transit_effect is not None and len(precomputed_transit_effect) != NUM_PARAMETERS:
        raise ValueError(f"precomputed_transit_effect length must be {NUM_PARAMETERS}")
    use_precomputed = precomputed_transit_effect is not None
    params_final = [0.0] * NUM_PARAMETERS
    for p in range(NUM_PARAMETERS):
        transit = precomputed_transit_effect[p] if use_precomputed else bounded_delta[p] * sensitivity_vector[p]
        params_final[p] = clamp01(base_vector[p] + transit + mem[p])
    # Axis aggregation: ровно 4 параметра на ось
    axis_final = [0.0] * NUM_AXES
    for p_ix, (axis_ix, _) in enumerate(_PARAMETER_LIST):
        axis_final[axis_ix] += params_final[p_ix]
    for a in range(NUM_AXES):
        axis_final[a] /= 4.0
    return (tuple(params_final), tuple(axis_final))
