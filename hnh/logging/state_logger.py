"""
Structured state transition logger per state-log-spec.
One record per state transition; one JSON line per record; diffable.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, TextIO

from hnh.logging.contracts import STATE_LOG_REQUIRED_FIELDS
from hnh.state.dynamic_state import DynamicState


def _hash_dict(d: dict[str, Any]) -> str:
    """Deterministic hash of a dict (sorted keys)."""
    blob = json.dumps(d, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def build_record(state: DynamicState) -> dict[str, Any]:
    """
    Build one log record from DynamicState.
    Required: seed, injected_time, identity_hash, active_modifiers, final_behavioral_vector.
    Optional: transit_signature (hash), relational_snapshot_hash.
    """
    record: dict[str, Any] = {
        "seed": state.seed,
        "injected_time": state.injected_time,
        "identity_hash": state.identity_hash,
        "active_modifiers": state.active_modifiers,
        "final_behavioral_vector": state.final_behavior_vector.to_dict(),
    }
    if state.transit_signature is not None:
        record["transit_signature"] = _hash_dict(state.transit_signature)
    if state.relational_modifier is not None:
        record["relational_snapshot_hash"] = _hash_dict(state.relational_modifier)
    return record


def emit_line(record: dict[str, Any]) -> str:
    """Serialize record to one JSON line (no trailing newline). JSON Lines = one line per record."""
    return json.dumps(record, sort_keys=True, ensure_ascii=True)


def write_record(state: DynamicState, stream: TextIO) -> None:
    """Append one state transition record to stream (one line, JSON)."""
    record = build_record(state)
    line = emit_line(record)
    stream.write(line + "\n")


def parse_line(line: str) -> dict[str, Any]:
    """Parse one JSON Lines record. Raises ValueError if invalid."""
    line = line.strip()
    if not line:
        raise ValueError("Empty log line")
    return json.loads(line)


def validate_record(record: dict[str, Any]) -> None:
    """Ensure record has all required fields per contract. Raises ValueError if missing."""
    for field in STATE_LOG_REQUIRED_FIELDS:
        if field not in record:
            raise ValueError(f"Missing required field: {field!r}")
    fbv = record.get("final_behavioral_vector")
    if not isinstance(fbv, dict):
        raise ValueError("final_behavioral_vector must be an object")
    for key in ("warmth", "strictness", "verbosity", "correction_rate",
                "humor_level", "challenge_intensity", "pacing"):
        if key not in fbv:
            raise ValueError(f"final_behavioral_vector missing dimension: {key!r}")
