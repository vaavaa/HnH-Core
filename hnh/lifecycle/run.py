"""
Integration: run replay step then lifecycle step when mode=research and lifecycle_enabled.
Caller passes aspects_to_natal (from transit), chrono_age_days, and lifecycle state.
"""

from __future__ import annotations

from typing import Any

from hnh.config.replay_config import ReplayConfig
from hnh.identity.schema import IdentityCore

from hnh.lifecycle.engine import (
    LifecycleSnapshot,
    LifecycleState,
    LifecycleStepState,
    check_init_death_or_transcendence,
    lifecycle_step,
)
from hnh.lifecycle.fatigue import fatigue_limit, global_sensitivity, resilience_from_base_vector
from hnh.lifecycle.stress import compute_transit_stress
from hnh.lifecycle.constants import DEFAULT_LIFECYCLE_CONSTANTS, C_T_DEFAULT


def is_lifecycle_active(config: ReplayConfig) -> bool:
    """True if mode=research and lifecycle_enabled. Spec §2."""
    return getattr(config, "mode", "product") == "research" and getattr(
        config, "lifecycle_enabled", False
    )


def run_step_with_lifecycle(
    identity: IdentityCore,
    config: ReplayConfig,
    daily_transit_effect: tuple[float, ...],
    memory_delta: tuple[float, ...],
    aspects_to_natal: list[dict[str, Any]],
    chrono_age_days: float,
    state: LifecycleStepState,
    c_t: float = C_T_DEFAULT,
) -> tuple[LifecycleStepState, tuple[float, ...], tuple[float, ...], LifecycleSnapshot | None]:
    """
    One lifecycle-aware step. Call only when is_lifecycle_active(config).
    Uses identity.base_vector, identity.sensitivity_vector; computes S_T from aspects,
    R from base_vector, S_g from sensitivity; runs lifecycle_step.
    Returns (next_state, params_final, axis_final, snapshot_if_death_or_transcendence).
    """
    _, s_t = compute_transit_stress(aspects_to_natal, c_t=c_t)
    r = resilience_from_base_vector(identity.base_vector)
    s_g = global_sensitivity(identity.sensitivity_vector)
    c = DEFAULT_LIFECYCLE_CONSTANTS
    L = fatigue_limit(r, s_g, c)
    init_check = check_init_death_or_transcendence(state.F, state.W, L, c.w_transcend)
    if init_check is not None:
        # Edge case: already at death/transcendence before step; state should be set by caller
        if state.state == LifecycleState.ALIVE:
            next_state = LifecycleStepState(
                F=state.F,
                W=state.W,
                state=init_check,
                sum_v=state.sum_v,
                sum_burn=state.sum_burn,
                count_days=state.count_days,
            )
            a_g = 0.0 if init_check == LifecycleState.DISABLED else 1.0
            from hnh.state.assembler import assemble_state
            from hnh.identity.schema import NUM_PARAMETERS
            effective_transit = tuple(x * a_g for x in daily_transit_effect)
            effective_memory = tuple(x * a_g for x in memory_delta)
            params_final, axis_final = assemble_state(
                identity.base_vector,
                identity.sensitivity_vector,
                (0.0,) * NUM_PARAMETERS,
                effective_memory,
                precomputed_transit_effect=effective_transit,
            )
            from hnh.lifecycle.engine import apply_behavioral_degradation, aggregate_axis
            params_final = apply_behavioral_degradation(params_final, a_g, c)
            axis_final = aggregate_axis(params_final)
            q = state.F / L if L > 0 else 1.0
            from hnh.lifecycle.engine import age_psy_years
            snap = next_state.to_snapshot(L, q, params_final, axis_final, age_psy_years(chrono_age_days, q, c))
            return (next_state, params_final, axis_final, snap)
    return lifecycle_step(
        identity.base_vector,
        identity.sensitivity_vector,
        daily_transit_effect,
        memory_delta,
        s_t,
        r,
        s_g,
        chrono_age_days,
        state,
        c,
    )
