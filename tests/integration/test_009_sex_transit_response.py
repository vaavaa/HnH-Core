"""T008, T009: 009 Sex Transit Response — mode=off same d_*; scale_delta differs; determinism."""

from datetime import date, timedelta

import pytest

from hnh.agent import Agent
from hnh.config.sex_transit_config import SexTransitConfig
from hnh.lifecycle.engine import aggregate_axis


def _birth_data(sex: str | None = None):
    return {
        "positions": [
            {"planet": "Sun", "longitude": 90.0},
            {"planet": "Moon", "longitude": 120.0},
        ],
        **({"sex": sex} if sex is not None else {}),
    }


def _axis_delta_over_run(agent: Agent, start_date: date, num_steps: int) -> tuple[float, ...]:
    """Cumulative axis change over num_steps: axis_end - axis_start."""
    axis_0 = aggregate_axis(agent.behavior.current_vector)
    for i in range(num_steps):
        agent.step(start_date + timedelta(days=i))
    axis_N = aggregate_axis(agent.behavior.current_vector)
    return tuple(axis_N[j] - axis_0[j] for j in range(len(axis_0)))


def test_mode_off_male_female_same_axis_delta():
    """T008: sex_transit_mode=off → male and female d_* (axis deltas) identical."""
    start = date(2020, 6, 1)
    num_steps = 14
    config_off = SexTransitConfig(sex_transit_mode="off")
    agent_m = Agent(_birth_data("male"), lifecycle=False, sex_transit_config=config_off)
    agent_f = Agent(_birth_data("female"), lifecycle=False, sex_transit_config=config_off)
    delta_m = _axis_delta_over_run(agent_m, start, num_steps)
    delta_f = _axis_delta_over_run(agent_f, start, num_steps)
    for i in range(len(delta_m)):
        assert abs(delta_m[i] - delta_f[i]) < 1e-9, f"axis {i}: male {delta_m[i]} vs female {delta_f[i]}"


def test_scale_delta_at_least_one_axis_differs():
    """T008: scale_delta with non-zero transits → at least one axis d_* differs male vs female."""
    start = date(2020, 6, 1)
    num_steps = 30
    config_sd = SexTransitConfig(sex_transit_mode="scale_delta")
    agent_m = Agent(_birth_data("male"), lifecycle=False, sex_transit_config=config_sd)
    agent_f = Agent(_birth_data("female"), lifecycle=False, sex_transit_config=config_sd)
    delta_m = _axis_delta_over_run(agent_m, start, num_steps)
    delta_f = _axis_delta_over_run(agent_f, start, num_steps)
    diffs = [abs(delta_m[i] - delta_f[i]) for i in range(len(delta_m))]
    assert any(d > 1e-9 for d in diffs), (
        f"Expected at least one axis delta to differ (male E>0, female E<0); deltas_m={delta_m}, deltas_f={delta_f}"
    )


def test_determinism_scale_delta():
    """T009: Same natal/date/config/identity → same step() outputs with scale_delta."""
    bd = _birth_data("female")
    config_sd = SexTransitConfig(sex_transit_mode="scale_delta")
    agent1 = Agent(bd, lifecycle=False, sex_transit_config=config_sd)
    agent2 = Agent(bd, lifecycle=False, sex_transit_config=config_sd)
    d = date(2021, 1, 15)
    r1 = agent1.step(d)
    r2 = agent2.step(d)
    assert r1.sex == r2.sex
    assert r1.sex_polarity_E == r2.sex_polarity_E
    assert agent1.behavior.current_vector == agent2.behavior.current_vector


def test_debug_009_fields_when_debug_and_scale_delta():
    """T013: With 008 debug enabled and sex_transit_mode=scale_delta, step output includes 009 debug fields."""
    bd = _birth_data("male")
    config_sd = SexTransitConfig(sex_transit_mode="scale_delta")
    agent = Agent(bd, lifecycle=False, sex_transit_config=config_sd, debug=True)
    result = agent.step(date(2021, 1, 15))
    assert result.debug_009 is not None
    assert result.debug_009.get("sex_transit_mode") == "scale_delta"
    assert "sex_transit_beta" in result.debug_009
    assert "sex_transit_mcap" in result.debug_009
    assert result.debug_009.get("sex_transit_Wdyn_profile") == "v1"
    stats = result.debug_009.get("multiplier_stats")
    assert stats is not None
    assert "min_M" in stats and "max_M" in stats and "mean_abs_M_minus_1" in stats
    assert "max_abs_transit_delta" in result.debug_009
    assert "max_abs_transit_delta_eff" in result.debug_009


def test_debug_009_none_when_debug_off():
    """US3: When debug disabled, step output has no 009 debug payload."""
    bd = _birth_data("male")
    config_sd = SexTransitConfig(sex_transit_mode="scale_delta")
    agent = Agent(bd, lifecycle=False, sex_transit_config=config_sd, debug=False)
    result = agent.step(date(2021, 1, 15))
    assert result.debug_009 is None
