"""
T034: Relational memory update rules — same history → same modifiers.
"""

from __future__ import annotations

import pytest

from hnh.memory.relational import RelationalMemory
from hnh.memory.update_rules import compute_derived, compute_behavioral_modifier


def test_same_history_same_derived():
    """T034: Same event list → identical derived metrics."""
    events = [
        {"sequence": 1, "type": "interaction", "payload": {}},
        {"sequence": 2, "type": "error", "payload": {}},
        {"sequence": 3, "type": "interaction", "payload": {}},
    ]
    d1 = compute_derived(events)
    d2 = compute_derived(events)
    assert d1 == d2
    assert d1["interaction_count"] == 3
    assert d1["error_count"] == 1
    assert "error_rate" in d1
    assert "responsiveness_metric" in d1


def test_same_history_same_behavioral_modifier():
    """T034: Same history → same behavioral modifier (7 dims)."""
    events = [
        {"sequence": 1, "type": "interaction", "payload": {}},
        {"sequence": 2, "type": "interaction", "payload": {}},
    ]
    m1 = compute_behavioral_modifier(events)
    m2 = compute_behavioral_modifier(events)
    assert m1 == m2
    dims = ("warmth", "strictness", "verbosity", "correction_rate",
            "humor_level", "challenge_intensity", "pacing")
    for d in dims:
        assert d in m1
        assert 0.0 <= m1[d] <= 1.0


def test_relational_memory_same_events_same_modifier():
    """T034: Two memories with same events → same get_behavioral_modifier()."""
    mem1 = RelationalMemory("user-a")
    mem2 = RelationalMemory("user-b")
    for seq, t in [(1, "interaction"), (2, "interaction"), (3, "error")]:
        mem1.add_event(seq, t)
        mem2.add_event(seq, t)
    assert mem1.get_behavioral_modifier() == mem2.get_behavioral_modifier()


def test_snapshot_serializable():
    """T039: Snapshot is serializable and contains required structure."""
    mem = RelationalMemory("user-snap")
    mem.add_event(1, "interaction", {"key": "value"})
    snap = mem.snapshot()
    assert snap["user_id"] == "user-snap"
    assert len(snap["events"]) == 1
    assert snap["events"][0]["sequence"] == 1 and snap["events"][0]["type"] == "interaction"
    assert "derived" in snap
    assert "behavioral_modifier" in snap
    assert set(snap["behavioral_modifier"].keys()) == {
        "warmth", "strictness", "verbosity", "correction_rate",
        "humor_level", "challenge_intensity", "pacing",
    }
    # Serializable = can round-trip via dict (e.g. JSON)
    import json
    json.dumps(snap)
