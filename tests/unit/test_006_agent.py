"""
T011: Unit tests for Agent (Spec 006). Creation with/without lifecycle; step(date) deterministic.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from hnh.agent import Agent
from hnh.config.replay_config import ReplayConfig
from hnh.identity.schema import NUM_PARAMETERS


def test_agent_creation_lifecycle_false():
    """Agent with lifecycle=False: lifecycle is None (product mode)."""
    birth_data = {"positions": [{"planet": "Sun", "longitude": 90.0}]}
    agent = Agent(birth_data, lifecycle=False)
    assert agent.lifecycle is None
    assert agent.natal is not None
    assert agent.behavior is not None
    assert agent.transits is not None


def test_agent_creation_lifecycle_true():
    """Agent with lifecycle=True: lifecycle is LifecycleEngine."""
    birth_data = {"positions": [{"planet": "Sun", "longitude": 90.0}]}
    agent = Agent(birth_data, lifecycle=True)
    assert agent.lifecycle is not None
    assert hasattr(agent.lifecycle, "F")
    assert hasattr(agent.lifecycle, "W")
    assert hasattr(agent.lifecycle, "state")


def test_agent_step_does_not_raise():
    """Agent.step(date) does not raise; params_final / axis_final available via behavior.current_vector."""
    birth_data = {"positions": [{"planet": "Sun", "longitude": 90.0}, {"planet": "Moon", "longitude": 120.0}]}
    agent = Agent(birth_data, lifecycle=False)
    agent.step(date(2020, 6, 15))
    assert len(agent.behavior.current_vector) == NUM_PARAMETERS
    for v in agent.behavior.current_vector:
        assert 0.0 <= v <= 1.0


def test_agent_step_deterministic_same_inputs():
    """Same birth_data, config, dates → same current_vector after step."""
    birth_data = {"positions": [{"planet": "Sun", "longitude": 45.0}, {"planet": "Moon", "longitude": 90.0}]}
    config = ReplayConfig(global_max_delta=0.08, shock_threshold=0.5, shock_multiplier=1.0)
    agent1 = Agent(birth_data, config=config, lifecycle=False)
    agent2 = Agent(birth_data, config=config, lifecycle=False)
    for _ in range(3):
        agent1.step(date(2021, 1, 1))
        agent2.step(date(2021, 1, 1))
    assert agent1.behavior.current_vector == agent2.behavior.current_vector


def test_agent_zodiac_expression_lazy():
    """ZodiacExpression created on demand (lazy); not in constructor."""
    birth_data = {"positions": [{"planet": "Sun", "longitude": 90.0}]}
    agent = Agent(birth_data, lifecycle=False)
    zod = agent.zodiac_expression()
    assert zod is not None
    assert hasattr(zod, "dominant_sign")
    assert hasattr(zod, "dominant_element")
    assert agent.zodiac_expression() is zod  # same instance
