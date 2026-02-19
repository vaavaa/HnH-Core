"""
Lifecycle engine (Spec 005): A_g, behavioral degradation, death, will, transcendence, Age_psy.
State ALIVE | DISABLED | TRANSCENDED. O(1) per day; running sum_v, sum_burn for will at death.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from hnh.identity.schema import NUM_PARAMETERS, NUM_AXES, PARAMETERS, _PARAMETER_LIST
from hnh.state.assembler import assemble_state

from hnh.lifecycle.constants import (
    ACTIVITY_SUPPRESSION_CAP,
    DAYS_PER_YEAR,
    DELTA_P,
    DELTA_W_MAX,
    DELTA_W_MIN,
    ETA_0,
    ETA_1,
    ETA_W,
    KAPPA,
    LifecycleConstants,
    Q_CRIT,
    RHO,
    W_TRANSCEND,
    XI_W,
    DEFAULT_LIFECYCLE_CONSTANTS,
)
from hnh.lifecycle.fatigue import (
    fatigue_limit,
    load,
    recovery,
    normalized_fatigue,
    update_fatigue,
)

# Activity-sensitive params for degradation (§7.2): initiative, curiosity, persistence, pacing, challenge_level, verbosity
_ACTIVITY_PARAM_NAMES = (
    "initiative",
    "curiosity",
    "persistence",
    "pacing",
    "challenge_level",
    "verbosity",
)
ACTIVITY_SENSITIVE_INDICES: tuple[int, ...] = tuple(
    PARAMETERS.index(n) for n in _ACTIVITY_PARAM_NAMES if n in PARAMETERS
)


class LifecycleState(str, Enum):
    ALIVE = "ALIVE"
    DISABLED = "DISABLED"
    TRANSCENDED = "TRANSCENDED"


def activity_factor(q: float, c: LifecycleConstants = DEFAULT_LIFECYCLE_CONSTANTS) -> float:
    """A_g(t) = clip(1 - q^rho, 0, 1)."""
    return max(0.0, min(1.0, 1.0 - (q ** c.rho)))


def age_psy_years(chrono_days: float, q: float, c: LifecycleConstants = DEFAULT_LIFECYCLE_CONSTANTS) -> float:
    """Age_psy in years: (A(t) * (eta_0 + eta_1 * q^kappa)) / DAYS_PER_YEAR. Spec §8."""
    raw = chrono_days * (c.eta_0 + c.eta_1 * (q ** c.kappa))
    return raw / DAYS_PER_YEAR


def apply_behavioral_degradation(
    params_final: tuple[float, ...],
    a_g: float,
    c: LifecycleConstants = DEFAULT_LIFECYCLE_CONSTANTS,
) -> tuple[float, ...]:
    """
    For activity-sensitive params: x_p -= delta_p*(1-A_g), clamp [0,1]; cap absolute reduction at 0.1.
    """
    out = list(params_final)
    reduction = min(ACTIVITY_SUPPRESSION_CAP, c.delta_p * (1.0 - a_g))
    for p_ix in ACTIVITY_SENSITIVE_INDICES:
        out[p_ix] = max(0.0, min(1.0, out[p_ix] - reduction))
    return tuple(out)


def aggregate_axis(params: tuple[float, ...]) -> tuple[float, ...]:
    """Axis aggregate = mean of 4 params per axis."""
    axis_final = [0.0] * NUM_AXES
    for p_ix, (axis_ix, _) in enumerate(_PARAMETER_LIST):
        axis_final[axis_ix] += params[p_ix]
    for a in range(NUM_AXES):
        axis_final[a] /= 4.0
    return tuple(axis_final)


@dataclass(frozen=True)
class LifecycleSnapshot:
    """Final snapshot at DISABLED/TRANSCENDED (spec §9.1). orjson when logging."""

    F: float
    L: float
    q: float
    W: float
    state: str
    sum_v: float
    sum_burn: float
    count_days: int
    params_final: tuple[float, ...]
    axis_final: tuple[float, ...]
    Age_psy: float | None = None


@dataclass
class LifecycleStepState:
    """Per-step lifecycle state (mutable for O(1) updates)."""

    F: float
    W: float
    state: LifecycleState
    sum_v: float
    sum_burn: float
    count_days: int

    def to_snapshot(
        self,
        L: float,
        q: float,
        params_final: tuple[float, ...],
        axis_final: tuple[float, ...],
        age_psy: float | None = None,
    ) -> LifecycleSnapshot:
        return LifecycleSnapshot(
            F=self.F,
            L=L,
            q=q,
            W=self.W,
            state=self.state.value,
            sum_v=self.sum_v,
            sum_burn=self.sum_burn,
            count_days=self.count_days,
            params_final=params_final,
            axis_final=axis_final,
            Age_psy=age_psy,
        )


def lifecycle_step(
    base_vector: tuple[float, ...],
    sensitivity_vector: tuple[float, ...],
    daily_transit_effect: tuple[float, ...],
    memory_delta: tuple[float, ...],
    s_t: float,
    r: float,
    s_g: float,
    chrono_age_days: float,
    state: LifecycleStepState,
    c: LifecycleConstants = DEFAULT_LIFECYCLE_CONSTANTS,
) -> tuple[LifecycleStepState, tuple[float, ...], tuple[float, ...], LifecycleSnapshot | None]:
    """
    One lifecycle step. Call only when mode=research and lifecycle_enabled.
    Edge case: if F(0)>=L or W(0)>=0.995, caller should have set state DISABLED/TRANSCENDED before first step.
    Returns: (updated_state, params_final, axis_final, snapshot_if_death_or_transcendence).
    """
    if state.state != LifecycleState.ALIVE:
        # Already dead or transcended; return frozen
        return (state, (0.0,) * NUM_PARAMETERS, (0.0,) * NUM_AXES, None)

    L = fatigue_limit(r, s_g, c)
    q = normalized_fatigue(state.F, L)

    # Check death
    if state.F >= L:
        delta_w = c.eta_w * (state.sum_v / max(1, state.count_days)) - c.xi_w * (
            state.sum_burn / max(1, state.count_days)
        )
        delta_w = max(c.delta_w_min, min(c.delta_w_max, delta_w))
        w_new = max(0.0, min(1.0, state.W + delta_w))
        next_state = LifecycleStepState(
            F=state.F,
            W=w_new,
            state=LifecycleState.DISABLED,
            sum_v=state.sum_v,
            sum_burn=state.sum_burn,
            count_days=state.count_days,
        )
        # params at freeze: use A_g=0 effectively (full suppression) for final assembly
        a_g = 0.0
        effective_transit = tuple(x * a_g for x in daily_transit_effect)
        effective_memory = tuple(x * a_g for x in memory_delta)
        params_final, axis_final = assemble_state(
            base_vector, sensitivity_vector, (0.0,) * NUM_PARAMETERS, effective_memory, precomputed_transit_effect=effective_transit
        )
        params_final = apply_behavioral_degradation(params_final, a_g, c)
        axis_final = aggregate_axis(params_final)
        snap = next_state.to_snapshot(L, q, params_final, axis_final, age_psy_years(chrono_age_days, q, c))
        return (next_state, params_final, axis_final, snap)

    # Check transcendence (W from previous step)
    if state.W >= c.w_transcend:
        next_state = LifecycleStepState(
            F=state.F,
            W=state.W,
            state=LifecycleState.TRANSCENDED,
            sum_v=state.sum_v,
            sum_burn=state.sum_burn,
            count_days=state.count_days,
        )
        a_g = 1.0  # no suppression
        params_final, axis_final = assemble_state(
            base_vector, sensitivity_vector, daily_transit_effect, memory_delta
        )
        snap = next_state.to_snapshot(L, q, params_final, axis_final, age_psy_years(chrono_age_days, q, c))
        return (next_state, params_final, axis_final, snap)

    # Normal step
    load_val = load(s_t, r, s_g, c)
    rec_val = recovery(s_t, r, c)
    f_new = update_fatigue(state.F, load_val, rec_val, c)
    q_new = normalized_fatigue(f_new, L)
    a_g = activity_factor(q_new, c)

    v_t = a_g * s_t
    burn_t = max(0.0, q_new - c.q_crit)

    next_state = LifecycleStepState(
        F=f_new,
        W=state.W,
        state=LifecycleState.ALIVE,
        sum_v=state.sum_v + v_t,
        sum_burn=state.sum_burn + burn_t,
        count_days=state.count_days + 1,
    )

    effective_transit = tuple(x * a_g for x in daily_transit_effect)
    effective_memory = tuple(x * a_g for x in memory_delta)
    params_final, axis_final = assemble_state(
        base_vector,
        sensitivity_vector,
        (0.0,) * NUM_PARAMETERS,
        effective_memory,
        precomputed_transit_effect=effective_transit,
    )
    params_final = apply_behavioral_degradation(params_final, a_g, c)
    axis_final = aggregate_axis(params_final)

    return (next_state, params_final, axis_final, None)


def check_init_death_or_transcendence(
    f0: float, w0: float, L: float, w_transcend: float = W_TRANSCEND
) -> LifecycleState | None:
    """
    Edge case §9: if F(0)>=L or W(0)>=0.995, return DISABLED or TRANSCENDED before first step.
    Otherwise return None (proceed with step).
    """
    if f0 >= L:
        return LifecycleState.DISABLED
    if w0 >= w_transcend:
        return LifecycleState.TRANSCENDED
    return None
