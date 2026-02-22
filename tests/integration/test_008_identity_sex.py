"""T014: Integration — identity includes sex_delta_32; male/female/None; symmetry."""

from datetime import date

import pytest

from hnh.agent import Agent
from hnh.identity.schema import NUM_PARAMETERS


def _bd(sex=None):
    return {"positions": [{"planet": "Sun", "longitude": 90.0}, {"planet": "Moon", "longitude": 120.0}], **({"sex": sex} if sex is not None else {})}


def test_identity_with_sex_differs_from_baseline():
    """With sex=male, base_vector differs from neutral (0.5,*32)."""
    agent_none = Agent(_bd(), lifecycle=False)
    agent_male = Agent(_bd("male"), lifecycle=False)
    base_none = agent_none.behavior.base_vector
    base_male = agent_male.behavior.base_vector
    assert base_none != base_male
    assert all(0.0 <= v <= 1.0 for v in base_male)


def test_symmetry_male_female_delta_bounds():
    """SC-002: |sex_delta_f[i] + sex_delta_m[i]| <= 2*0.08 for same natal."""
    from hnh.sex.delta_32 import compute_sex_delta_32
    # E=±0.5 -> delta_m ≈ -delta_f; bound 2*sex_max_param_delta = 0.08
    delta_m = compute_sex_delta_32(0.5)
    delta_f = compute_sex_delta_32(-0.5)
    for i in range(NUM_PARAMETERS):
        assert abs(delta_f[i] + delta_m[i]) <= 0.08 + 1e-9  # 2 * 0.04
