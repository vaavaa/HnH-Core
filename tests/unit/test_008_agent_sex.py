"""T014: Agent step() returns sex and sex_polarity_E; determinism; bounds (US1)."""

from datetime import date

import pytest

from hnh.agent import Agent, StepResult
from hnh.identity.schema import NUM_PARAMETERS


def _minimal_birth_data(sex: str | None = None):
    return {"positions": [{"planet": "Sun", "longitude": 90.0}, {"planet": "Moon", "longitude": 120.0}], **({"sex": sex} if sex is not None else {})}


def test_step_returns_sex_and_E():
    """FR-020: step() output includes sex and sex_polarity_E."""
    agent = Agent(_minimal_birth_data("male"), lifecycle=False)
    result = agent.step(date(2020, 6, 15))
    assert isinstance(result, StepResult)
    assert result.sex == "male"
    assert hasattr(result, "sex_polarity_E")
    assert -1.0 <= result.sex_polarity_E <= 1.0


def test_step_no_sex_baseline():
    """US1 Scenario 1: no sex -> E=0, baseline preserved."""
    agent = Agent(_minimal_birth_data(), lifecycle=False)
    result = agent.step(date(2020, 6, 15))
    assert result.sex is None
    assert result.sex_polarity_E == 0.0


def test_step_deterministic():
    """Same inputs -> same step() output (determinism)."""
    bd = _minimal_birth_data("female")
    agent = Agent(bd, lifecycle=False)
    r1 = agent.step(date(2021, 1, 1))
    r2 = agent.step(date(2021, 1, 1))
    assert r1.sex == r2.sex
    assert r1.sex_polarity_E == r2.sex_polarity_E
    assert agent.behavior.current_vector == agent.behavior.current_vector


def test_invalid_sex_fail_fast():
    """FR-001: invalid sex in birth_data -> fail-fast."""
    with pytest.raises(ValueError, match="male.*female"):
        Agent(_minimal_birth_data(sex="invalid"), lifecycle=False)


def test_agent_infer_returns_male_or_female():
    """US2: sex_mode=infer, no sex -> inferred sex male or female."""
    from hnh.sex.resolver import InsufficientNatalDataError

    bd = {"positions": [{"planet": "Sun", "longitude": 90.0}, {"planet": "Moon", "longitude": 120.0}], "sex_mode": "infer"}
    agent = Agent(bd, lifecycle=False)
    result = agent.step(date(2020, 6, 15))
    assert result.sex in ("male", "female")
    assert -1.0 <= result.sex_polarity_E <= 1.0


def test_agent_infer_insufficient_data_fail_fast():
    """Infer with no Sun in natal -> fail-fast (no fallback to None)."""
    from hnh.sex.resolver import InsufficientNatalDataError

    bd = {"positions": [{"planet": "Moon", "longitude": 120.0}], "sex_mode": "infer"}
    with pytest.raises(InsufficientNatalDataError, match="Sun|insufficient"):
        Agent(bd, lifecycle=False)
