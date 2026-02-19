"""Tests for lifecycle engine: A_g, degradation, death, transcendence (Spec 005 §7-11)."""

import pytest

from hnh.identity.schema import NUM_PARAMETERS, NUM_AXES, PARAMETERS
from hnh.lifecycle.engine import (
    activity_factor,
    age_psy_years,
    apply_behavioral_degradation,
    check_init_death_or_transcendence,
    lifecycle_step,
    LifecycleState,
    LifecycleStepState,
)
from hnh.lifecycle.constants import DEFAULT_LIFECYCLE_CONSTANTS, W_TRANSCEND
from hnh.lifecycle.fatigue import fatigue_limit


def test_activity_factor_curve() -> None:
    assert abs(activity_factor(0) - 1.0) < 1e-6
    assert activity_factor(0.4) > 0.8  # minimal suppression
    assert activity_factor(0.8) < 0.5   # strong suppression
    assert abs(activity_factor(1.0) - 0.0) < 1e-6


def test_age_psy_years() -> None:
    # chrono 365 days, q=0 -> raw = 365 * 0.8 = 292, years = 292/365.25
    y = age_psy_years(365.25, 0.0)
    assert y > 0 and y < 1.5


def test_behavioral_degradation_cap() -> None:
    params = (0.5,) * NUM_PARAMETERS
    degraded = apply_behavioral_degradation(params, 0.0)  # max reduction
    for p_ix in [PARAMETERS.index("initiative"), PARAMETERS.index("verbosity")]:
        diff = params[p_ix] - degraded[p_ix]
        assert diff <= 0.1 + 1e-9  # cap 0.1


def test_check_init_death() -> None:
    L = 14.0
    assert check_init_death_or_transcendence(14.0, 0.5, L) == LifecycleState.DISABLED
    assert check_init_death_or_transcendence(15.0, 0.0, L) == LifecycleState.DISABLED


def test_check_init_transcendence() -> None:
    L = 14.0
    assert check_init_death_or_transcendence(0.0, 0.995, L) == LifecycleState.TRANSCENDED
    assert check_init_death_or_transcendence(1.0, 0.996, L) == LifecycleState.TRANSCENDED


def test_check_init_alive() -> None:
    L = 14.0
    assert check_init_death_or_transcendence(0.0, 0.5, L) is None
    assert check_init_death_or_transcendence(5.0, 0.9, L) is None


def test_lifecycle_step_alive() -> None:
    base = (0.5,) * NUM_PARAMETERS
    sens = (0.5,) * NUM_PARAMETERS
    daily = (0.01,) * NUM_PARAMETERS
    mem = (0.0,) * NUM_PARAMETERS
    state = LifecycleStepState(F=0.0, W=0.0, state=LifecycleState.ALIVE, sum_v=0.0, sum_burn=0.0, count_days=0)
    next_state, params, axis, snap = lifecycle_step(
        base, sens, daily, mem, s_t=0.2, r=0.5, s_g=0.5, chrono_age_days=0.0, state=state
    )
    assert next_state.state == LifecycleState.ALIVE
    assert snap is None
    assert len(params) == NUM_PARAMETERS and len(axis) == NUM_AXES


def test_lifecycle_step_death_trigger() -> None:
    """When F >= L, state becomes DISABLED and snapshot is returned."""
    base = (0.5,) * NUM_PARAMETERS
    sens = (0.5,) * NUM_PARAMETERS
    daily = (0.0,) * NUM_PARAMETERS
    mem = (0.0,) * NUM_PARAMETERS
    c = DEFAULT_LIFECYCLE_CONSTANTS
    L = fatigue_limit(0.5, 0.5, c)
    state = LifecycleStepState(F=L, W=0.5, state=LifecycleState.ALIVE, sum_v=10.0, sum_burn=2.0, count_days=100)
    next_state, params, axis, snap = lifecycle_step(
        base, sens, daily, mem, s_t=0.0, r=0.5, s_g=0.5, chrono_age_days=100.0, state=state, c=c
    )
    assert next_state.state == LifecycleState.DISABLED
    assert snap is not None
    assert snap.state == "DISABLED"
    assert snap.count_days == 100


def test_lifecycle_step_already_disabled() -> None:
    base = (0.5,) * NUM_PARAMETERS
    sens = (0.5,) * NUM_PARAMETERS
    state = LifecycleStepState(F=20.0, W=0.5, state=LifecycleState.DISABLED, sum_v=1.0, sum_burn=0.5, count_days=100)
    next_state, params, axis, snap = lifecycle_step(
        base, sens, (0.0,) * NUM_PARAMETERS, (0.0,) * NUM_PARAMETERS,
        s_t=0.5, r=0.5, s_g=0.5, chrono_age_days=100.0, state=state
    )
    assert next_state.state == LifecycleState.DISABLED
    assert snap is None
    assert all(p == 0.0 for p in params)
