"""
T030: Log format matches contract; replay from same inputs produces identical state and log.
"""

from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO

import pytest

from hnh.core.identity import IdentityCore
from hnh.core.parameters import BehavioralVector
from hnh.logging.contracts import STATE_LOG_REQUIRED_FIELDS
from hnh.logging.state_logger import (
    build_record,
    emit_line,
    parse_line,
    validate_record,
    write_record,
)
from hnh.state.dynamic_state import DynamicState
from hnh.state.replay import run_step

@pytest.fixture(autouse=True)
def _clear_registry():
    from hnh.core.identity import _registry
    _registry.clear()
    yield
    _registry.clear()


def test_log_format_matches_contract():
    """T030: Log record contains all required fields per contract."""
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
        identity_id="log-test-1",
        base_traits=base,
        symbolic_input=None,
    )
    injected = datetime(2020, 3, 15, 14, 0, 0, tzinfo=timezone.utc)
    state = run_step(identity, injected, seed=42, relational_snapshot=None)
    record = build_record(state)
    for field in STATE_LOG_REQUIRED_FIELDS:
        assert field in record, f"Missing required field: {field!r}"
    assert set(record["final_behavioral_vector"].keys()) == {
        "warmth", "strictness", "verbosity", "correction_rate",
        "humor_level", "challenge_intensity", "pacing",
    }
    validate_record(record)


def test_one_line_per_record_diffable():
    """T033: One record per transition; one line per record; JSON parseable."""
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
        identity_id="log-test-2",
        base_traits=base,
        symbolic_input=None,
    )
    injected = datetime(2021, 5, 20, 12, 0, 0, tzinfo=timezone.utc)
    state = run_step(identity, injected, seed=123, relational_snapshot=None)
    buf = StringIO()
    write_record(state, buf)
    content = buf.getvalue()
    lines = [ln for ln in content.strip().split("\n") if ln]
    assert len(lines) == 1
    parsed = parse_line(lines[0])
    validate_record(parsed)
    assert parsed["identity_hash"] == state.identity_hash
    assert parsed["final_behavioral_vector"] == state.final_behavior_vector.to_dict()


def test_parse_line_empty_raises():
    """parse_line rejects empty line."""
    from hnh.logging.state_logger import parse_line
    with pytest.raises(ValueError, match="Empty"):
        parse_line("")
    with pytest.raises(ValueError, match="Empty"):
        parse_line("   \n  ")


def test_validate_record_missing_field_raises():
    """validate_record raises on missing required field."""
    record = {
        "seed": 0,
        "injected_time": "2024-01-01T12:00:00+00:00",
        "identity_hash": "abc",
        "active_modifiers": {},
        "final_behavioral_vector": {k: 0.5 for k in (
            "warmth", "strictness", "verbosity", "correction_rate",
            "humor_level", "challenge_intensity", "pacing",
        )},
    }
    validate_record(record)
    del record["identity_hash"]
    with pytest.raises(ValueError, match="Missing required"):
        validate_record(record)


def test_validate_record_fbv_not_dict_raises():
    """validate_record raises when final_behavioral_vector is not an object."""
    record = {
        "seed": 0,
        "injected_time": "2024-01-01T12:00:00+00:00",
        "identity_hash": "x",
        "active_modifiers": {},
        "final_behavioral_vector": "not-a-dict",
    }
    with pytest.raises(ValueError, match="must be an object"):
        validate_record(record)


def test_validate_record_fbv_missing_dimension_raises():
    """validate_record raises when final_behavioral_vector misses a dimension."""
    record = {
        "seed": 0,
        "injected_time": "2024-01-01T12:00:00+00:00",
        "identity_hash": "x",
        "active_modifiers": {},
        "final_behavioral_vector": {"warmth": 0.5},  # missing others
    }
    with pytest.raises(ValueError, match="missing dimension"):
        validate_record(record)


def test_replay_from_same_inputs_produces_identical_state_and_log():
    """T030: Run step → log; run step again with same inputs → same state, same log line."""
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.4,
        verbosity=0.5,
        correction_rate=0.3,
        humor_level=0.5,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    identity = IdentityCore(
        identity_id="log-replay-1",
        base_traits=base,
        symbolic_input=None,
    )
    injected = datetime(2022, 1, 10, 10, 0, 0, tzinfo=timezone.utc)
    state1 = run_step(identity, injected, seed=999, relational_snapshot=None)
    state2 = run_step(identity, injected, seed=999, relational_snapshot=None)
    assert state1.final_behavior_vector.to_dict() == state2.final_behavior_vector.to_dict()
    assert state1.identity_hash == state2.identity_hash
    record1 = build_record(state1)
    record2 = build_record(state2)
    assert record1 == record2
    line1 = emit_line(record1)
    line2 = emit_line(record2)
    assert line1 == line2
