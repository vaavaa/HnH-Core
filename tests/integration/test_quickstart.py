"""
T041: Quickstart validation scenarios (specs/001-deterministic-personality-engine/quickstart.md).
"""

from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO

import pytest

from hnh.core.identity import IdentityCore
from hnh.core.parameters import BehavioralVector
from hnh.logging.state_logger import build_record, write_record
from hnh.memory.relational import RelationalMemory
from hnh.state.replay import run_step


@pytest.fixture(autouse=True)
def _clear_registry():
    from hnh.core.identity import _registry
    _registry.clear()
    yield
    _registry.clear()


def test_quickstart_1_identity_core() -> None:
    """Quickstart §1: Identity Core — create, base vector, hash, same inputs → same vector, reject duplicate id, reject out-of-range."""
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.3,
        verbosity=0.6,
        correction_rate=0.4,
        humor_level=0.5,
        challenge_intensity=0.3,
        pacing=0.5,
    )
    c1 = IdentityCore(identity_id="qs-1", base_traits=base)
    c2 = IdentityCore(identity_id="qs-2", base_traits=base)
    assert c1.base_behavior_vector.to_dict() == c2.base_behavior_vector.to_dict()
    assert c1.identity_hash and c2.identity_hash
    hash(c1)
    c1.model_dump()
    with pytest.raises(ValueError, match="already exists"):
        IdentityCore(identity_id="qs-1", base_traits=base)
    with pytest.raises(ValueError, match="0.0, 1.0"):
        BehavioralVector(**{**base.to_dict(), "warmth": 1.5})


def test_quickstart_2_dynamic_state() -> None:
    """Quickstart §2: Dynamic State — compute with identity, seed, time; output has vector and modifiers; Identity unchanged; same inputs → same output."""
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.4,
        verbosity=0.5,
        correction_rate=0.3,
        humor_level=0.5,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    identity = IdentityCore(identity_id="qs-dyn", base_traits=base)
    injected = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    state1 = run_step(identity, injected, seed=42, relational_snapshot=None)
    state2 = run_step(identity, injected, seed=42, relational_snapshot=None)
    assert "final_behavior_vector" in state1.model_dump()
    assert state1.active_modifiers is not None
    assert state1.final_behavior_vector.to_dict() == state2.final_behavior_vector.to_dict()
    assert identity.base_behavior_vector.to_dict() == base.to_dict()


def test_quickstart_3_logging() -> None:
    """Quickstart §3: One step → one log record; required fields; JSON Lines; diffable."""
    base = BehavioralVector(warmth=0.5, strictness=0.4, verbosity=0.5, correction_rate=0.3,
                            humor_level=0.5, challenge_intensity=0.4, pacing=0.5)
    identity = IdentityCore(identity_id="qs-log", base_traits=base)
    state = run_step(identity, datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc), seed=0)
    buf = StringIO()
    write_record(state, buf)
    lines = [l for l in buf.getvalue().strip().split("\n") if l]
    assert len(lines) == 1
    record = build_record(state)
    for f in ("seed", "injected_time", "identity_hash", "active_modifiers", "final_behavioral_vector"):
        assert f in record


def test_quickstart_4_replay() -> None:
    """Quickstart §4: Replay with same seed, time, identity, snapshot → identical output."""
    base = BehavioralVector(warmth=0.5, strictness=0.4, verbosity=0.5, correction_rate=0.3,
                            humor_level=0.5, challenge_intensity=0.4, pacing=0.5)
    identity = IdentityCore(identity_id="qs-replay", base_traits=base)
    injected = datetime(2024, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
    state1 = run_step(identity, injected, seed=1, relational_snapshot=None)
    state2 = run_step(identity, injected, seed=1, relational_snapshot=None)
    assert state1.final_behavior_vector.to_dict() == state2.final_behavior_vector.to_dict()


def test_quickstart_5_relational_memory() -> None:
    """Quickstart §5: Relational Memory — user_id, events, snapshot into Dynamic State; Identity unchanged; deterministic."""
    base = BehavioralVector(warmth=0.5, strictness=0.4, verbosity=0.5, correction_rate=0.3,
                            humor_level=0.5, challenge_intensity=0.4, pacing=0.5)
    identity = IdentityCore(identity_id="qs-rel", base_traits=base)
    mem = RelationalMemory("user-qs")
    mem.add_event(1, "interaction")
    mem.add_event(2, "interaction")
    modifier = mem.get_behavioral_modifier()
    injected = datetime(2024, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
    state = run_step(identity, injected, seed=0, relational_snapshot=modifier)
    assert state.final_behavior_vector is not None
    assert identity.base_behavior_vector.to_dict() == base.to_dict()
    state2 = run_step(identity, injected, seed=0, relational_snapshot=modifier)
    assert state.final_behavior_vector.to_dict() == state2.final_behavior_vector.to_dict()
