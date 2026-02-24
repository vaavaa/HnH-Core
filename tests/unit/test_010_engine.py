"""T011: AgeEngine.compute determinism and output shape; missing birth_datetime_utc documented error."""

from datetime import datetime, timezone

import pytest

from hnh.age.engine import (
    AgeEngine,
    AgeOutput,
    MISSING_BIRTH_DATETIME_UTC_MESSAGE,
    get_birth_datetime_utc_from_birth_data,
)
from hnh.config.age_config import AgeConfig
from hnh.identity.schema import NUM_PARAMETERS


def _config() -> AgeConfig:
    return AgeConfig(age_mode="on", age_strength=0.04, age_max_param_delta=0.06)


def test_engine_compute_output_shape():
    """AgeEngine.compute returns AgeOutput with age_years, age_stage_features (5), age_delta_32 (32)."""
    birth = datetime(1990, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    injected = datetime(2015, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    engine = AgeEngine(_config())
    out = engine.compute(birth, injected)
    assert isinstance(out, AgeOutput)
    assert isinstance(out.age_years, float)
    assert out.age_years >= 0
    assert len(out.age_stage_features) == 5
    assert all(0.0 <= x <= 1.0 for x in out.age_stage_features)
    assert len(out.age_delta_32) == NUM_PARAMETERS
    assert out.age_delta_32_stats is None  # default include_stats=False


def test_engine_compute_determinism():
    """Same (birth_dt, injected_dt) -> same AgeOutput."""
    birth = datetime(1985, 5, 10, 0, 0, 0, tzinfo=timezone.utc)
    injected = datetime(2020, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    engine = AgeEngine(_config())
    out1 = engine.compute(birth, injected)
    # New engine to reset Lipschitz state
    engine2 = AgeEngine(_config())
    out2 = engine2.compute(birth, injected)
    assert out1.age_years == out2.age_years
    assert out1.age_stage_features == out2.age_stage_features
    assert out1.age_delta_32 == out2.age_delta_32


def test_engine_compute_include_stats():
    """include_stats=True adds age_delta_32_stats with max_abs, mean_abs, nonzero_count."""
    birth = datetime(1990, 1, 1, tzinfo=timezone.utc)
    injected = datetime(2000, 1, 1, tzinfo=timezone.utc)
    engine = AgeEngine(_config())
    out = engine.compute(birth, injected, include_stats=True)
    assert out.age_delta_32_stats is not None
    assert "max_abs" in out.age_delta_32_stats
    assert "mean_abs" in out.age_delta_32_stats
    assert "nonzero_count" in out.age_delta_32_stats


def test_engine_requires_age_mode_on():
    """AgeEngine(config) requires config.age_mode == 'on'."""
    with pytest.raises(ValueError, match="age_mode == 'on'"):
        AgeEngine(AgeConfig(age_mode="off"))


def test_get_birth_datetime_utc_missing_returns_none():
    """get_birth_datetime_utc_from_birth_data returns None when datetime_utc not in birth_data."""
    birth_data = {"positions": [], "aspects": []}
    assert get_birth_datetime_utc_from_birth_data(birth_data) is None


def test_get_birth_datetime_utc_present():
    """get_birth_datetime_utc_from_birth_data returns datetime when datetime_utc in birth_data."""
    birth_data = {"positions": [], "datetime_utc": "1990-01-01T00:00:00+00:00"}
    dt = get_birth_datetime_utc_from_birth_data(birth_data)
    assert dt is not None
    assert dt.year == 1990 and dt.month == 1 and dt.day == 1


def test_missing_birth_datetime_message_documented():
    """MISSING_BIRTH_DATETIME_UTC_MESSAGE is the documented error message for Agent/engine fail-fast."""
    assert "birth_datetime_utc" in MISSING_BIRTH_DATETIME_UTC_MESSAGE
    assert "age_mode=on" in MISSING_BIRTH_DATETIME_UTC_MESSAGE
