"""T008: age_years from two datetimes, bump/sigmoid, all 5 stage features, stage peaks (Success 4)."""

from datetime import datetime, timezone

import pytest

from hnh.age.constants import (
    JUPITER_PERIOD_YEARS,
    NODE_PERIOD_YEARS,
    SATURN_PERIOD_YEARS,
    TROPICAL_YEAR_DAYS,
    URANUS_PERIOD_YEARS,
)
from hnh.age.stage_features import (
    age_stage_features_v1,
    age_years_from_delta_days,
    bump,
    jupiter_return,
    maturity,
    nodal_return,
    saturn_event,
    sigmoid,
    uranus_opposition,
)


def test_sigmoid_bounds():
    """sigmoid(x) in (0, 1)."""
    assert 0.0 < sigmoid(-10.0) < 0.01
    assert 0.99 < sigmoid(10.0) < 1.0
    assert 0.4 < sigmoid(0) < 0.6  # ~0.5


def test_sigmoid_monotone():
    """sigmoid is increasing."""
    assert sigmoid(-1.0) < sigmoid(0.0) < sigmoid(1.0)


def test_bump_center():
    """bump(center, center, width) == 1.0 for width > 0."""
    assert bump(5.0, 5.0, 1.0) == 1.0


def test_bump_zero_outside_width():
    """bump is 0 when |age - center| >= width."""
    assert bump(0.0, 5.0, 2.0) == 0.0
    assert bump(10.0, 5.0, 2.0) == 0.0


def test_bump_width_zero_raises():
    """width <= 0 raises ValueError."""
    with pytest.raises(ValueError, match="width must be > 0"):
        bump(1.0, 1.0, 0.0)
    with pytest.raises(ValueError, match="width must be > 0"):
        bump(1.0, 1.0, -0.1)


def test_age_years_from_delta_days():
    """age_years = delta_days / TROPICAL_YEAR_DAYS, clamped to [0, age_max_years]."""
    one_year_days = TROPICAL_YEAR_DAYS
    assert abs(age_years_from_delta_days(one_year_days, 120.0) - 1.0) < 1e-6
    assert age_years_from_delta_days(0.0, 120.0) == 0.0
    assert age_years_from_delta_days(-100.0, 120.0) == 0.0
    assert age_years_from_delta_days(200 * one_year_days, 120.0) == 120.0


def test_age_years_from_two_datetimes():
    """age_years from (injected_time_utc - birth_datetime_utc).total_seconds() / 86400 / TROPICAL_YEAR_DAYS."""
    birth = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    injected = datetime(2001, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    delta_days = (injected - birth).total_seconds() / 86400.0
    age = age_years_from_delta_days(delta_days, 120.0)
    assert abs(age - 1.0) < 0.01


def test_maturity_in_bounds():
    """maturity(age) in [0, 1]."""
    for age in [0.0, 25.0, 50.0, 100.0]:
        m = maturity(age)
        assert 0.0 <= m <= 1.0


def test_maturity_monotone():
    """maturity increases with age (sigmoid shift)."""
    assert maturity(10.0) < maturity(25.0) < maturity(40.0)


def test_age_stage_features_v1_length_and_bounds():
    """age_stage_features_v1 returns 5 values, all in [0, 1]."""
    for age in [0.0, 7.0, 14.0, 22.0, 42.0, 80.0]:
        f = age_stage_features_v1(age)
        assert len(f) == 5
        assert all(0.0 <= x <= 1.0 for x in f), f"age={age} features={f}"


def test_saturn_event_peaks_near_quarter_cycles():
    """Success 4: saturn_event local max at 0, ~7.375, ~14.75, ~22.125 y (quarter Saturn cycle)."""
    T = SATURN_PERIOD_YEARS
    peaks = [0.0, 0.25 * T, 0.5 * T, 0.75 * T]  # ~0, 7.375, 14.75, 22.125
    for center in peaks:
        at_center = saturn_event(center)
        # Local max: slightly before/after should be <= or close
        before = saturn_event(center - 0.5) if center >= 0.5 else saturn_event(center + T - 0.5)
        after = saturn_event(center + 0.5) if center + 0.5 <= T else saturn_event(center - T + 0.5)
        assert at_center >= 0.3, f"saturn_event at {center} should be significant, got {at_center}"
        assert at_center >= before * 0.9 or at_center >= after * 0.9  # peak in the vicinity


def test_uranus_opposition_peak_near_42y():
    """Success 4: uranus_opposition peak near ~42 y (±2 y window)."""
    center = 0.5 * URANUS_PERIOD_YEARS  # 42.0
    at_42 = uranus_opposition(42.0)
    at_40 = uranus_opposition(40.0)
    at_44 = uranus_opposition(44.0)
    assert at_42 >= 0.3, f"uranus_opposition at 42 should be significant, got {at_42}"
    assert at_42 >= at_40 * 0.9 or at_42 >= at_44 * 0.9  # peak in window


def test_jupiter_return_at_zero():
    """jupiter_return peaks at age 0 mod cycle."""
    assert jupiter_return(0.0) >= 0.9
    assert jupiter_return(JUPITER_PERIOD_YEARS) >= 0.9


def test_nodal_return_at_zero_and_half():
    """nodal_return has peaks at 0 and half period."""
    assert nodal_return(0.0) >= 0.5
    assert nodal_return(0.5 * NODE_PERIOD_YEARS) >= 0.5
