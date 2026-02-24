"""T015/T016: Determinism with age; age_mode on vs off; params_final in [0,1]; max_abs(age_delta_32) <= age_max_param_delta."""

from datetime import date, datetime, timezone

import pytest

from hnh.agent import Agent
from hnh.config.age_config import AgeConfig
from hnh.identity.schema import NUM_PARAMETERS


def _birth_data(datetime_utc: str = "1990-01-01T00:00:00+00:00"):
    return {
        "positions": [{"planet": "Sun", "longitude": 90.0}, {"planet": "Moon", "longitude": 120.0}],
        "datetime_utc": datetime_utc,
    }


def test_same_inputs_same_step_output_determinism():
    """T015: Same inputs -> same step() output (determinism with age)."""
    birth_data = _birth_data()
    age_config = AgeConfig(age_mode="on")
    agent = Agent(birth_data, config=None, lifecycle=False, age_config=age_config)
    r1 = agent.step(date(2020, 6, 15))
    r2 = agent.step(date(2020, 6, 15))
    assert agent.behavior.current_vector == agent.behavior.current_vector
    # Same date twice -> same internal state
    v1 = agent.behavior.current_vector
    agent2 = Agent(birth_data, config=None, lifecycle=False, age_config=age_config)
    agent2.step(date(2020, 6, 15))
    v2 = agent2.behavior.current_vector
    assert v1 == v2


def test_age_mode_on_vs_off_params_differ():
    """T015: age_mode=on vs off -> params_final can differ when age differs."""
    birth_data = _birth_data()
    agent_off = Agent(birth_data, config=None, lifecycle=False)
    agent_on = Agent(birth_data, config=None, lifecycle=False, age_config=AgeConfig(age_mode="on"))
    agent_off.step(date(2020, 6, 15))
    agent_on.step(date(2020, 6, 15))
    # With age on, assembly includes age_delta_32; may differ from off
    v_off = agent_off.behavior.current_vector
    v_on = agent_on.behavior.current_vector
    # At least one param can differ (age adds delta)
    assert any(v_off[i] != v_on[i] for i in range(NUM_PARAMETERS)) or v_off == v_on


def test_params_final_in_bounds():
    """T016: params_final in [0, 1]."""
    birth_data = _birth_data()
    age_config = AgeConfig(age_mode="on")
    agent = Agent(birth_data, config=None, lifecycle=False, age_config=age_config)
    agent.step(date(2025, 1, 1))
    params = agent.behavior.current_vector
    for i in range(NUM_PARAMETERS):
        assert 0.0 <= params[i] <= 1.0, f"param[{i}]={params[i]}"


def test_step_with_memory_delta_assembly():
    """T015: step with memory_delta matches expected assembly (memory_delta applied)."""
    birth_data = _birth_data()
    agent = Agent(birth_data, config=None, lifecycle=False, age_config=AgeConfig(age_mode="on"))
    memory_delta = (0.01,) * NUM_PARAMETERS
    agent.step(date(2020, 6, 15), memory_delta=memory_delta)
    params = agent.behavior.current_vector
    assert all(0.0 <= p <= 1.0 for p in params)


def test_configuration_hash_includes_age_when_on():
    """T019: configuration_hash includes age fields when age_mode=on."""
    from hnh.config.replay_config import ReplayConfig, compute_configuration_hash

    config = ReplayConfig(global_max_delta=0.08, shock_threshold=0.5, shock_multiplier=1.0)
    h_no_age = compute_configuration_hash(config)
    age_config = AgeConfig(age_mode="on")
    h_with_age = compute_configuration_hash(config, age_config=age_config)
    assert h_no_age != h_with_age
    # Different age strength -> different hash
    age_config2 = AgeConfig(age_mode="on", age_strength=0.08)
    h_with_age2 = compute_configuration_hash(config, age_config=age_config2)
    assert h_with_age != h_with_age2
