"""
T008/T009: Unit tests for TransitEngine and LifecycleEngine (Spec 006).
TransitEngine: state(date, config) -> TransitState; LifecycleEngine: F, W, state, update_lifecycle.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from hnh.astrology.natal_chart import NatalChart
from hnh.astrology.transits import TransitEngine
from hnh.config.replay_config import ReplayConfig
from hnh.identity.schema import NUM_PARAMETERS
from hnh.lifecycle.engine import LifecycleEngine, LifecycleState


# --- TransitEngine ---


def test_transit_engine_state_returns_transit_state():
    """TransitEngine: state(date, config) returns TransitState with stress, raw_delta, bounded_delta."""
    birth_data = {
        "positions": [{"planet": "Sun", "longitude": 100.0}, {"planet": "Moon", "longitude": 200.0}],
    }
    natal = NatalChart.from_birth_data(birth_data)
    engine = TransitEngine(natal)
    config = ReplayConfig(global_max_delta=0.1, shock_threshold=0.5, shock_multiplier=1.0)
    dt = datetime(2020, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    state = engine.state(dt, config)
    assert hasattr(state, "stress")
    assert hasattr(state, "raw_delta")
    assert hasattr(state, "bounded_delta")
    assert len(state.raw_delta) == NUM_PARAMETERS
    assert len(state.bounded_delta) == NUM_PARAMETERS
    assert 0 <= state.stress <= 1.0


def test_transit_engine_deterministic():
    """TransitEngine: same (natal, date, config) -> same TransitState."""
    birth_data = {"positions": [{"planet": "Sun", "longitude": 90.0}]}
    natal = NatalChart.from_birth_data(birth_data)
    engine = TransitEngine(natal)
    config = ReplayConfig(global_max_delta=0.08, shock_threshold=0.4, shock_multiplier=1.2)
    d = date(2021, 1, 1)
    s1 = engine.state(d, config)
    s2 = engine.state(d, config)
    assert s1.stress == s2.stress
    assert s1.bounded_delta == s2.bounded_delta


# --- LifecycleEngine ---


def test_lifecycle_engine_f_w_state():
    """LifecycleEngine: F, W, state exposed; initial ALIVE."""
    le = LifecycleEngine(initial_f=0.0, initial_w=0.0)
    assert le.F == 0.0
    assert le.W == 0.0
    assert le.state == LifecycleState.ALIVE


def test_lifecycle_engine_update_lifecycle_alive():
    """LifecycleEngine: update_lifecycle(stress, resilience) updates F without killing."""
    le = LifecycleEngine(initial_f=0.0, initial_w=0.0)
    le.update_lifecycle(stress=0.1, resilience=0.6)
    assert le.state == LifecycleState.ALIVE
    assert le.F >= 0.0


def test_lifecycle_engine_transcendence_if_high_w():
    """LifecycleEngine: if initial W >= w_transcend, state becomes TRANSCENDED."""
    le = LifecycleEngine(initial_f=0.0, initial_w=0.996)
    assert le.state == LifecycleState.TRANSCENDED


def test_lifecycle_engine_no_mutate_after_death():
    """LifecycleEngine: after DISABLED/TRANSCENDED, update_lifecycle does not change state."""
    le = LifecycleEngine(initial_f=0.0, initial_w=0.996)
    assert le.state == LifecycleState.TRANSCENDED
    le.update_lifecycle(stress=0.5, resilience=0.5)
    assert le.state == LifecycleState.TRANSCENDED
