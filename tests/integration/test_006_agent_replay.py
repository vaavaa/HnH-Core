"""
T012: Integration test — Agent.step() vs replay_v2 on same inputs; params_final/axis_final match (tolerance 1e-6).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hnh.agent import Agent
from hnh.astrology.natal_chart import NatalChart
from hnh.config.replay_config import ReplayConfig
from hnh.identity.schema import IdentityCore, NUM_AXES, NUM_PARAMETERS
from hnh.identity.sensitivity import compute_sensitivity
from hnh.lifecycle.engine import aggregate_axis
from hnh.state.replay_v2 import replay_match, run_step_v2

TOLERANCE = 1e-6


def test_agent_step_matches_replay_v2_same_inputs():
    """Same birth_data, config, dates: Agent.step() outcome matches run_step_v2 (params_final, axis_final)."""
    birth_data = {
        "positions": [
            {"planet": "Sun", "longitude": 90.0},
            {"planet": "Moon", "longitude": 120.0},
            {"planet": "Mercury", "longitude": 45.0},
        ],
    }
    config = ReplayConfig(global_max_delta=0.08, shock_threshold=0.5, shock_multiplier=1.0)
    natal = NatalChart.from_birth_data(birth_data)
    natal_data = natal.to_natal_data()
    sensitivity = compute_sensitivity(natal_data)
    base_vector = (0.5,) * NUM_PARAMETERS
    identity = IdentityCore(
        identity_id="test-006-integ-1",
        base_vector=base_vector,
        sensitivity_vector=sensitivity,
    )
    dt = datetime(2020, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    # Single step: replay_v2 from base
    result_replay = run_step_v2(
        identity,
        config,
        dt,
        memory_delta=None,
        natal_positions=natal_data,
    )
    # Agent: one step from same effective base (Agent builds same identity from natal)
    agent = Agent(birth_data, config=config, lifecycle=False)
    agent.step(dt)
    agent_params = agent.behavior.current_vector
    agent_axis = aggregate_axis(agent_params)
    assert len(agent_axis) == NUM_AXES
    assert replay_match(
        agent_params,
        agent_axis,
        result_replay.params_final,
        result_replay.axis_final,
        tolerance=TOLERANCE,
    ), (
        f"Agent vs replay_v2 mismatch: "
        f"agent params[:4]={agent_params[:4]} axis={agent_axis[:2]}, "
        f"replay params[:4]={result_replay.params_final[:4]} axis={result_replay.axis_final[:2]}"
    )
