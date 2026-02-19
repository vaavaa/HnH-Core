"""
Fatigue engine (Spec 005 §5–6): R from base_vector, S_g, load, recovery, F update, L, q.
Deterministic; R constant per identity (Stability axis from base_vector).
"""

from __future__ import annotations

from hnh.identity.schema import NUM_PARAMETERS, _PARAMETER_LIST
from hnh.lifecycle.constants import (
    ALPHA_SHOCK,
    BETA_R,
    BETA_S,
    DELTA_R,
    DELTA_S,
    GAMMA_0,
    GAMMA_C,
    GAMMA_R,
    L0,
    LAMBDA_DOWN,
    LAMBDA_UP,
    THETA_SHOCK,
    LifecycleConstants,
)

STABILITY_AXIS_INDEX = 1  # stability_regulation


def resilience_from_base_vector(base_vector: tuple[float, ...]) -> float:
    """
    R = mean of 4 parameters of Stability axis (index 1) from base_vector.
    Range [0, 1]. Constant per identity. Spec §3, Clarifications.
    """
    if len(base_vector) != NUM_PARAMETERS:
        raise ValueError(f"base_vector must have length {NUM_PARAMETERS}, got {len(base_vector)}")
    total = 0.0
    count = 0
    for p_ix, (axis_ix, _) in enumerate(_PARAMETER_LIST):
        if axis_ix == STABILITY_AXIS_INDEX:
            total += base_vector[p_ix]
            count += 1
    if count == 0:
        return 0.5
    return max(0.0, min(1.0, total / count))


def global_sensitivity(sensitivity_vector: tuple[float, ...]) -> float:
    """S_g = mean of 32 sensitivity parameters. [0, 1]."""
    if len(sensitivity_vector) != NUM_PARAMETERS:
        raise ValueError(
            f"sensitivity_vector must have length {NUM_PARAMETERS}, got {len(sensitivity_vector)}"
        )
    return max(0.0, min(1.0, sum(sensitivity_vector) / NUM_PARAMETERS))


def shock_multiplier(s_t: float, c: LifecycleConstants) -> float:
    """1 + alpha_shock if S_T >= theta_shock else 1."""
    return (1.0 + c.alpha_shock) if s_t >= c.theta_shock else 1.0


def load(s_t: float, r: float, s_g: float, c: LifecycleConstants) -> float:
    """load(t) = shock_mult * S_T * (1 + beta_s*S_g) * (1 - beta_r*R)."""
    mult = shock_multiplier(s_t, c)
    return mult * s_t * (1.0 + c.beta_s * s_g) * (1.0 - c.beta_r * r)


def recovery(s_t: float, r: float, c: LifecycleConstants) -> float:
    """recovery(t) = gamma_0 + gamma_r*R + gamma_c*(1 - S_T)."""
    return c.gamma_0 + c.gamma_r * r + c.gamma_c * (1.0 - s_t)


def fatigue_limit(r: float, s_g: float, c: LifecycleConstants) -> float:
    """L = L0 * (1 + delta_r*R) * (1 - delta_s*S_g). Must be > 0."""
    l_val = c.l0 * (1.0 + c.delta_r * r) * (1.0 - c.delta_s * s_g)
    return max(1e-9, l_val)


def update_fatigue(
    f: float, load_val: float, recovery_val: float, c: LifecycleConstants
) -> float:
    """F(t+1) = max(0, F(t) + lambda_up*load - lambda_down*recovery)."""
    return max(0.0, f + c.lambda_up * load_val - c.lambda_down * recovery_val)


def normalized_fatigue(f: float, l: float) -> float:
    """q(t) = clip(F(t)/L, 0, 1)."""
    if l <= 0:
        return 1.0
    return max(0.0, min(1.0, f / l))
