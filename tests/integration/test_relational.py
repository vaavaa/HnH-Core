"""
T035: Replay with identical relational history → same behavior; Identity unchanged.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hnh.core.identity import IdentityCore
from hnh.core.parameters import BehavioralVector
from hnh.memory.relational import RelationalMemory
from hnh.state.replay import run_step

@pytest.fixture(autouse=True)
def _clear_registry():
    from hnh.core.identity import _registry
    _registry.clear()
    yield
    _registry.clear()


def test_replay_with_identical_relational_history_same_behavior():
    """T035: Same identity + time + same relational history → identical state output."""
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
        identity_id="rel-replay-1",
        base_traits=base,
        symbolic_input=None,
    )
    mem = RelationalMemory("user-1")
    mem.add_event(1, "interaction")
    mem.add_event(2, "interaction")
    mem.add_event(3, "error")
    modifier = mem.get_behavioral_modifier()
    injected = datetime(2022, 2, 20, 12, 0, 0, tzinfo=timezone.utc)
    state1 = run_step(identity, injected, seed=1, relational_snapshot=modifier)
    state2 = run_step(identity, injected, seed=1, relational_snapshot=modifier)
    assert state1.final_behavior_vector.to_dict() == state2.final_behavior_vector.to_dict()
    assert state1.identity_hash == state2.identity_hash


def test_identity_unchanged_after_relational_replay():
    """T035 / US4: Identity Core not modified by Relational Memory or Dynamic State."""
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
        identity_id="rel-identity-1",
        base_traits=base,
        symbolic_input=None,
    )
    hash_before = identity.identity_hash
    vec_before = identity.base_behavior_vector.to_dict()
    mem = RelationalMemory("user-2")
    mem.add_event(1, "interaction")
    run_step(identity, datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc), relational_snapshot=mem.get_behavioral_modifier())
    assert identity.identity_hash == hash_before
    assert identity.base_behavior_vector.to_dict() == vec_before


def test_same_memory_state_same_modifier_into_dynamic_state():
    """Same events in memory → same modifier → same final vector when replayed."""
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.5,
        verbosity=0.5,
        correction_rate=0.5,
        humor_level=0.5,
        challenge_intensity=0.5,
        pacing=0.5,
    )
    identity = IdentityCore(
        identity_id="rel-same-1",
        base_traits=base,
        symbolic_input=None,
    )
    mem1 = RelationalMemory("u1")
    mem2 = RelationalMemory("u2")
    for seq, t in [(1, "interaction"), (2, "interaction")]:
        mem1.add_event(seq, t)
        mem2.add_event(seq, t)
    injected = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    s1 = run_step(identity, injected, seed=0, relational_snapshot=mem1.get_behavioral_modifier())
    s2 = run_step(identity, injected, seed=0, relational_snapshot=mem2.get_behavioral_modifier())
    assert s1.final_behavior_vector.to_dict() == s2.final_behavior_vector.to_dict()
