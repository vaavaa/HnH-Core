"""T018: debug=True and age_mode=on -> step() includes age_years, age_stage_features, age_delta_32_stats; debug=False backward compatible."""

from datetime import date

import pytest

from hnh.agent import Agent, StepResult
from hnh.age.engine import MISSING_BIRTH_DATETIME_UTC_MESSAGE
from hnh.config.age_config import AgeConfig


def _minimal_birth_data(datetime_utc: str | None = None):
    data = {
        "positions": [{"planet": "Sun", "longitude": 90.0}, {"planet": "Moon", "longitude": 120.0}],
    }
    if datetime_utc is not None:
        data["datetime_utc"] = datetime_utc
    return data


def test_age_mode_on_missing_birth_datetime_utc_raises():
    """T010/T011: When age_mode=on and birth_data has no datetime_utc, step() raises documented ValueError."""
    birth_data = _minimal_birth_data(datetime_utc=None)
    age_config = AgeConfig(age_mode="on")
    agent = Agent(birth_data, config=None, lifecycle=False, age_config=age_config)
    with pytest.raises(ValueError, match=MISSING_BIRTH_DATETIME_UTC_MESSAGE):
        agent.step(date(2020, 6, 15))


def test_debug_true_age_mode_on_step_includes_age_fields():
    """T017/T018: debug=True and age_mode=on -> step() return object includes age_years, age_stage_features, age_delta_32_stats."""
    birth_data = _minimal_birth_data(datetime_utc="1990-01-01T00:00:00+00:00")
    age_config = AgeConfig(age_mode="on")
    agent = Agent(birth_data, config=None, lifecycle=False, age_config=age_config, debug=True)
    result = agent.step(date(2020, 6, 15))
    assert isinstance(result, StepResult)
    assert result.age_years is not None
    assert result.age_stage_features is not None
    assert len(result.age_stage_features) == 5
    assert result.age_delta_32_stats is not None
    assert "max_abs" in result.age_delta_32_stats
    assert "mean_abs" in result.age_delta_32_stats
    assert "nonzero_count" in result.age_delta_32_stats


def test_debug_false_age_mode_on_age_fields_none():
    """Without debug, step() return has age_* as None (backward compatible)."""
    birth_data = _minimal_birth_data(datetime_utc="1990-01-01T00:00:00+00:00")
    age_config = AgeConfig(age_mode="on")
    agent = Agent(birth_data, config=None, lifecycle=False, age_config=age_config, debug=False)
    result = agent.step(date(2020, 6, 15))
    assert result.age_years is None
    assert result.age_stage_features is None
    assert result.age_delta_32_stats is None


def test_age_mode_off_no_age_engine():
    """age_config=None or age_mode=off -> no age engine, step() works without datetime_utc."""
    birth_data = _minimal_birth_data(datetime_utc=None)
    agent = Agent(birth_data, config=None, lifecycle=False)
    result = agent.step(date(2020, 6, 15))
    assert result.sex is None or result.sex in ("male", "female")
