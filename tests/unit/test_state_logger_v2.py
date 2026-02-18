"""
Unit tests for Spec 002 Phase 7: orjson logging, effective_max_delta_summary, replay signature.
"""

from __future__ import annotations

import io

import pytest

from hnh.identity.schema import NUM_AXES, NUM_PARAMETERS
from hnh.logging.state_logger_v2 import (
    STATE_LOG_V2_REQUIRED_FIELDS,
    build_record_v2,
    effective_max_delta_summary,
    emit_line_v2,
    parse_line_v2,
    validate_record_v2,
    write_record_v2,
)


def test_effective_max_delta_summary_shape() -> None:
    """T7.2: Returns 8 values, one per axis."""
    eff32 = (0.1,) * NUM_PARAMETERS
    summary = effective_max_delta_summary(eff32)
    assert len(summary) == NUM_AXES
    assert summary == (0.1,) * NUM_AXES


def test_effective_max_delta_summary_wrong_length_raises() -> None:
    """Wrong input length raises."""
    with pytest.raises(ValueError, match="effective_max_delta must have length"):
        effective_max_delta_summary((0.1,) * 31)


def test_effective_max_delta_summary_aggregate() -> None:
    """Per-axis aggregate is max of 4 sub-parameters."""
    eff32 = [0.0] * NUM_PARAMETERS
    eff32[0] = 0.2   # axis 0, param 0
    eff32[1] = 0.15  # axis 0, param 1
    eff32[2] = 0.25  # axis 0, param 2
    eff32[3] = 0.1   # axis 0, param 3
    summary = effective_max_delta_summary(tuple(eff32))
    assert summary[0] == 0.25
    assert summary[1] == 0.0


def test_build_record_v2_has_required_fields() -> None:
    """Record contains all required fields."""
    record = build_record_v2(
        identity_hash="ih",
        configuration_hash="ch",
        injected_time_utc="2025-02-18T12:00:00+00:00",
        transit_signature="tsig",
        shock_flag=False,
        effective_max_delta_summary_8=(0.1,) * NUM_AXES,
        axis_final=(0.5,) * NUM_AXES,
        params_final=(0.5,) * NUM_PARAMETERS,
        memory_signature="msig",
    )
    for field in STATE_LOG_V2_REQUIRED_FIELDS:
        assert field in record
    assert record["params_final"] == [0.5] * NUM_PARAMETERS
    assert record["axis_final"] == [0.5] * NUM_AXES


def test_build_record_v2_debug_fields() -> None:
    """Optional debug params_base, sensitivities, raw_delta, bounded_delta included when provided."""
    record = build_record_v2(
        identity_hash="x",
        configuration_hash="y",
        injected_time_utc="2025-01-01T00:00:00+00:00",
        transit_signature="z",
        shock_flag=False,
        effective_max_delta_summary_8=(0.1,) * NUM_AXES,
        axis_final=(0.5,) * NUM_AXES,
        params_final=(0.5,) * NUM_PARAMETERS,
        memory_signature="m",
        params_base=(0.4,) * NUM_PARAMETERS,
        sensitivities=(0.6,) * NUM_PARAMETERS,
        raw_delta=(0.01,) * NUM_PARAMETERS,
        bounded_delta=(0.01,) * NUM_PARAMETERS,
    )
    assert record["params_base"] == [0.4] * NUM_PARAMETERS
    assert record["sensitivities"] == [0.6] * NUM_PARAMETERS
    assert record["raw_delta"] == [0.01] * NUM_PARAMETERS
    assert record["bounded_delta"] == [0.01] * NUM_PARAMETERS


def test_emit_line_v2_orjson_no_stdlib_json() -> None:
    """T7.1: Serialization uses orjson (bytes, sort_keys)."""
    record = build_record_v2(
        identity_hash="a",
        configuration_hash="b",
        injected_time_utc="2025-01-01T00:00:00+00:00",
        transit_signature="c",
        shock_flag=False,
        effective_max_delta_summary_8=(0.1,) * NUM_AXES,
        axis_final=(0.5,) * NUM_AXES,
        params_final=(0.5,) * NUM_PARAMETERS,
        memory_signature="d",
    )
    line = emit_line_v2(record)
    assert isinstance(line, bytes)
    parsed = parse_line_v2(line)
    assert parsed["identity_hash"] == "a"
    assert parsed["memory_signature"] == "d"


def test_validate_record_v2_accepts_valid() -> None:
    """Valid record passes validation."""
    record = build_record_v2(
        identity_hash="x",
        configuration_hash="y",
        injected_time_utc="2025-01-01T00:00:00+00:00",
        transit_signature="z",
        shock_flag=True,
        effective_max_delta_summary_8=(0.15,) * NUM_AXES,
        axis_final=(0.5,) * NUM_AXES,
        params_final=(0.5,) * NUM_PARAMETERS,
        memory_signature="m",
    )
    validate_record_v2(record)


def test_validate_record_v2_rejects_missing_field() -> None:
    """Missing required field raises."""
    record = build_record_v2(
        identity_hash="x",
        configuration_hash="y",
        injected_time_utc="2025-01-01T00:00:00+00:00",
        transit_signature="z",
        shock_flag=False,
        effective_max_delta_summary_8=(0.1,) * NUM_AXES,
        axis_final=(0.5,) * NUM_AXES,
        params_final=(0.5,) * NUM_PARAMETERS,
        memory_signature="m",
    )
    del record["memory_signature"]
    with pytest.raises(ValueError, match="Missing required field"):
        validate_record_v2(record)


def test_validate_record_v2_rejects_wrong_lengths() -> None:
    """Wrong length for effective_max_delta_summary, axis_final, params_final raises."""
    record = build_record_v2(
        identity_hash="x",
        configuration_hash="y",
        injected_time_utc="2025-01-01T00:00:00+00:00",
        transit_signature="z",
        shock_flag=False,
        effective_max_delta_summary_8=(0.1,) * NUM_AXES,
        axis_final=(0.5,) * NUM_AXES,
        params_final=(0.5,) * NUM_PARAMETERS,
        memory_signature="m",
    )
    record["effective_max_delta_summary"] = [0.1]
    with pytest.raises(ValueError, match="effective_max_delta_summary must have"):
        validate_record_v2(record)
    record["effective_max_delta_summary"] = list((0.1,) * NUM_AXES)
    record["axis_final"] = [0.5]
    with pytest.raises(ValueError, match="axis_final must have"):
        validate_record_v2(record)
    record["axis_final"] = list((0.5,) * NUM_AXES)
    record["params_final"] = [0.5]
    with pytest.raises(ValueError, match="params_final must have"):
        validate_record_v2(record)


def test_parse_line_v2_empty_raises() -> None:
    """Empty line raises ValueError."""
    with pytest.raises(ValueError, match="Empty log line"):
        parse_line_v2("")
    with pytest.raises(ValueError, match="Empty log line"):
        parse_line_v2(b"")


def test_write_record_v2_roundtrip() -> None:
    """Write then read back validates."""
    record = build_record_v2(
        identity_hash="id1",
        configuration_hash="cfg1",
        injected_time_utc="2025-02-18T12:00:00+00:00",
        transit_signature="ts1",
        shock_flag=False,
        effective_max_delta_summary_8=(0.1,) * NUM_AXES,
        axis_final=(0.5,) * NUM_AXES,
        params_final=(0.5,) * NUM_PARAMETERS,
        memory_signature="mem1",
    )
    buf = io.StringIO()
    write_record_v2(record, buf)
    line = buf.getvalue().strip()
    parsed = parse_line_v2(line)
    validate_record_v2(parsed)
    assert parsed["identity_hash"] == "id1"
    assert parsed["configuration_hash"] == "cfg1"
    assert parsed["memory_signature"] == "mem1"
