"""
Structured state transition logger for Spec 002 (32-param model).
Uses orjson only in core path; no stdlib json. Replay signature and effective_max_delta_summary.
"""

from __future__ import annotations

from typing import Any, TextIO

import orjson

from hnh.identity.schema import NUM_AXES, NUM_PARAMETERS, _PARAMETER_LIST

# Required fields per spec §13 / FR-010
STATE_LOG_V2_REQUIRED_FIELDS = (
    "identity_hash",
    "configuration_hash",
    "injected_time_utc",
    "transit_signature",
    "shock_flag",
    "effective_max_delta_summary",
    "axis_final",
    "params_final",
    "memory_signature",
)


def effective_max_delta_summary(effective_max_delta_32: tuple[float, ...]) -> tuple[float, ...]:
    """
    T7.2: Aggregate effective_max_delta per axis (8 values).
    One value per axis = max of the 4 sub-parameter effective_max_delta for that axis.
    """
    if len(effective_max_delta_32) != NUM_PARAMETERS:
        raise ValueError(f"effective_max_delta must have length {NUM_PARAMETERS}, got {len(effective_max_delta_32)}")
    axis_max: list[float] = [0.0] * NUM_AXES
    for p_ix in range(NUM_PARAMETERS):
        axis_ix = _PARAMETER_LIST[p_ix][0]
        axis_max[axis_ix] = max(axis_max[axis_ix], effective_max_delta_32[p_ix])
    return tuple(axis_max)


def build_record_v2(
    identity_hash: str,
    configuration_hash: str,
    injected_time_utc: str,
    transit_signature: str,
    shock_flag: bool,
    effective_max_delta_summary_8: tuple[float, ...],
    axis_final: tuple[float, ...],
    params_final: tuple[float, ...],
    memory_signature: str,
    *,
    params_base: tuple[float, ...] | None = None,
    sensitivities: tuple[float, ...] | None = None,
    raw_delta: tuple[float, ...] | None = None,
    bounded_delta: tuple[float, ...] | None = None,
) -> dict[str, Any]:
    """
    Build one log record for v0.2 state transition.
    Required fields per spec; optional debug fields when provided.
    """
    record: dict[str, Any] = {
        "identity_hash": identity_hash,
        "configuration_hash": configuration_hash,
        "injected_time_utc": injected_time_utc,
        "transit_signature": transit_signature,
        "shock_flag": shock_flag,
        "effective_max_delta_summary": list(effective_max_delta_summary_8),
        "axis_final": list(axis_final),
        "params_final": list(params_final),
        "memory_signature": memory_signature,
    }
    if params_base is not None:
        record["params_base"] = list(params_base)
    if sensitivities is not None:
        record["sensitivities"] = list(sensitivities)
    if raw_delta is not None:
        record["raw_delta"] = list(raw_delta)
    if bounded_delta is not None:
        record["bounded_delta"] = list(bounded_delta)
    return record


def emit_line_v2(record: dict[str, Any]) -> bytes:
    """
    T7.1: Serialize record to one JSON line using orjson (no stdlib json in core path).
    Returns bytes (orjson default).
    """
    return orjson.dumps(record, option=orjson.OPT_SORT_KEYS)


def write_record_v2(record: dict[str, Any], stream: TextIO) -> None:
    """Append one state transition record to stream (one line, orjson)."""
    line_bytes = emit_line_v2(record)
    stream.write(line_bytes.decode("utf-8") + "\n")


def parse_line_v2(line: str | bytes) -> dict[str, Any]:
    """Parse one JSON Lines record. Uses orjson."""
    if isinstance(line, str):
        line = line.strip().encode("utf-8")
    else:
        line = line.strip()
    if not line:
        raise ValueError("Empty log line")
    return orjson.loads(line)


def validate_record_v2(record: dict[str, Any]) -> None:
    """Ensure record has all required fields per spec. Raises ValueError if missing."""
    for field in STATE_LOG_V2_REQUIRED_FIELDS:
        if field not in record:
            raise ValueError(f"Missing required field: {field!r}")
    if len(record.get("effective_max_delta_summary", [])) != NUM_AXES:
        raise ValueError(f"effective_max_delta_summary must have {NUM_AXES} values")
    if len(record.get("axis_final", [])) != NUM_AXES:
        raise ValueError(f"axis_final must have {NUM_AXES} values")
    if len(record.get("params_final", [])) != NUM_PARAMETERS:
        raise ValueError(f"params_final must have {NUM_PARAMETERS} values")
