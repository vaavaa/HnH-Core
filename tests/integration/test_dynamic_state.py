"""
T022, T029: Dynamic State replay — same inputs → identical state output.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hnh.core.identity import IdentityCore
from hnh.core.parameters import BehavioralVector
from hnh.state.replay import run_step

pytest.importorskip("swisseph")


@pytest.fixture(autouse=True)
def _clear_registry():
    from hnh.core.identity import _registry
    _registry.clear()
    yield
    _registry.clear()


def test_same_inputs_identical_state_output():
    """T022: Same Identity + time + relational → identical DynamicState."""
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.3,
        verbosity=0.6,
        correction_rate=0.4,
        humor_level=0.5,
        challenge_intensity=0.3,
        pacing=0.5,
    )
    identity = IdentityCore(
        identity_id="replay-test-1",
        base_traits=base,
        symbolic_input=None,
    )
    injected = datetime(2020, 3, 15, 14, 0, 0, tzinfo=timezone.utc)
    state1 = run_step(identity, injected, seed=42, relational_snapshot=None)
    state2 = run_step(identity, injected, seed=42, relational_snapshot=None)
    assert state1.identity_hash == state2.identity_hash
    assert state1.injected_time == state2.injected_time
    assert state1.final_behavior_vector.to_dict() == state2.final_behavior_vector.to_dict()
    assert state1.active_modifiers == state2.active_modifiers


def test_replay_identical_output_twice():
    """T029: Run replay twice with same inputs → identical outputs."""
    base = BehavioralVector(
        warmth=0.4,
        strictness=0.5,
        verbosity=0.5,
        correction_rate=0.3,
        humor_level=0.6,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    identity = IdentityCore(
        identity_id="replay-test-2",
        base_traits=base,
        symbolic_input=None,
    )
    injected = datetime(2021, 5, 20, 12, 0, 0, tzinfo=timezone.utc)
    rel = {
        "warmth": 0.6,
        "strictness": 0.4,
        "verbosity": 0.5,
        "correction_rate": 0.3,
        "humor_level": 0.5,
        "challenge_intensity": 0.3,
        "pacing": 0.6,
    }
    a = run_step(identity, injected, seed=123, relational_snapshot=rel)
    b = run_step(identity, injected, seed=123, relational_snapshot=rel)
    assert a.final_behavior_vector.to_dict() == b.final_behavior_vector.to_dict()
    assert a.injected_time == b.injected_time
