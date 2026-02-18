"""
State assembly for 32-parameter model (Spec 002).
final[p] = clamp01(base[p] + (bounded_delta[p] × sensitivity[p]) + memory_delta[p]).
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
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """
    Compute params_final (32) and axis_final (8).
    Formula: final[p] = clamp01(base[p] + bounded_delta[p]*sensitivity[p] + memory_delta[p]).
    memory_delta default: zeros.
    """
    if len(base_vector) != NUM_PARAMETERS or len(sensitivity_vector) != NUM_PARAMETERS or len(bounded_delta) != NUM_PARAMETERS:
        raise ValueError(f"Vectors must have length {NUM_PARAMETERS}")
    mem = memory_delta if memory_delta is not None else (0.0,) * NUM_PARAMETERS
    if len(mem) != NUM_PARAMETERS:
        raise ValueError(f"memory_delta length must be {NUM_PARAMETERS}")
    params_final: list[float] = []
    for p in range(NUM_PARAMETERS):
        val = base_vector[p] + bounded_delta[p] * sensitivity_vector[p] + mem[p]
        params_final.append(clamp01(val))
    # Axis aggregation: mean of 4 sub-params per axis
    axis_final: list[float] = [0.0] * NUM_AXES
    counts = [0] * NUM_AXES
    for p_ix, (axis_ix, _) in enumerate(_PARAMETER_LIST):
        axis_final[axis_ix] += params_final[p_ix]
        counts[axis_ix] += 1
    for a in range(NUM_AXES):
        axis_final[a] /= max(1, counts[a])
    return (tuple(params_final), tuple(axis_final))
