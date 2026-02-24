"""T002b: Invalid AgeConfig (unknown age_mode, out-of-range numeric) raises documented ValueError."""

import pytest

from hnh.config.age_config import AGE_MAX_PARAM_DELTA_MAX, AGE_STRENGTH_MAX, AgeConfig


def test_age_mode_invalid_raises():
    """Unknown age_mode must raise ValueError with clear message."""
    with pytest.raises(ValueError, match="age_mode must be 'off' or 'on'"):
        AgeConfig(age_mode="enabled")
    with pytest.raises(ValueError, match="age_mode"):
        AgeConfig(age_mode="")


def test_age_strength_invalid_raises():
    """age_strength <= 0 or > 0.2 must raise ValueError."""
    with pytest.raises(ValueError, match="age_strength"):
        AgeConfig(age_mode="on", age_strength=0.0)
    with pytest.raises(ValueError, match="age_strength"):
        AgeConfig(age_mode="on", age_strength=-0.01)
    with pytest.raises(ValueError, match="age_strength"):
        AgeConfig(age_mode="on", age_strength=AGE_STRENGTH_MAX + 0.01)


def test_age_strength_valid():
    """Valid age_strength in (0, 0.2] does not raise."""
    c = AgeConfig(age_mode="on", age_strength=0.04)
    assert c.age_strength == 0.04
    c2 = AgeConfig(age_mode="on", age_strength=AGE_STRENGTH_MAX)
    assert c2.age_strength == AGE_STRENGTH_MAX


def test_age_max_param_delta_invalid_raises():
    """age_max_param_delta <= 0 or > 0.2 must raise ValueError."""
    with pytest.raises(ValueError, match="age_max_param_delta"):
        AgeConfig(age_mode="on", age_max_param_delta=0.0)
    with pytest.raises(ValueError, match="age_max_param_delta"):
        AgeConfig(age_mode="on", age_max_param_delta=AGE_MAX_PARAM_DELTA_MAX + 0.01)


def test_age_daily_lipschitz_negative_raises():
    """age_daily_lipschitz < 0 must raise ValueError."""
    with pytest.raises(ValueError, match="age_daily_lipschitz"):
        AgeConfig(age_mode="on", age_daily_lipschitz=-0.001)


def test_age_daily_lipschitz_zero_valid():
    """age_daily_lipschitz >= 0 is valid."""
    c = AgeConfig(age_mode="on", age_daily_lipschitz=0.0)
    assert c.age_daily_lipschitz == 0.0


def test_age_max_years_invalid_raises():
    """age_max_years <= 0 must raise ValueError."""
    with pytest.raises(ValueError, match="age_max_years"):
        AgeConfig(age_mode="on", age_max_years=0.0)
    with pytest.raises(ValueError, match="age_max_years"):
        AgeConfig(age_mode="on", age_max_years=-1.0)


def test_defaults_valid():
    """Default AgeConfig (age_mode=off) is valid."""
    c = AgeConfig()
    assert c.age_mode == "off"
    assert c.age_strength == 0.04
    assert c.age_max_param_delta == 0.06
    assert c.age_daily_lipschitz == 0.001
    assert c.age_max_years == 120.0
