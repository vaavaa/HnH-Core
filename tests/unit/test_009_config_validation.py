"""T011: Invalid sex_transit_mode and unknown sex_transit_Wdyn_profile → fail-fast (ValueError)."""

import pytest

from hnh.agent import Agent
from hnh.config.sex_transit_config import SexTransitConfig, validate_sex_transit_mode, SEX_TRANSIT_MODES
from hnh.sex.transit_modulator import get_wdyn_profile


def _birth_data(sex: str = "male"):
    return {
        "positions": [{"planet": "Sun", "longitude": 90.0}, {"planet": "Moon", "longitude": 120.0}],
        "sex": sex,
    }


def test_invalid_sex_transit_mode_raises():
    """Invalid sex_transit_mode in SexTransitConfig → ValueError."""
    with pytest.raises(ValueError, match=r"sex_transit_mode must be one of .* got: 'invalid'"):
        SexTransitConfig(sex_transit_mode="invalid")


def test_validate_sex_transit_mode_rejects_invalid():
    """validate_sex_transit_mode('bad') → ValueError."""
    with pytest.raises(ValueError, match=r"sex_transit_mode must be one of .* got: 'bad'"):
        validate_sex_transit_mode("bad")


def test_validate_sex_transit_mode_accepts_valid():
    """validate_sex_transit_mode accepts off, scale_delta, scale_sensitivity."""
    for mode in SEX_TRANSIT_MODES:
        validate_sex_transit_mode(mode)


def test_unknown_wdyn_profile_raises():
    """Unknown sex_transit_Wdyn_profile → ValueError from get_wdyn_profile (Agent init)."""
    with pytest.raises(ValueError, match=r"sex_transit_Wdyn_profile must be a registered profile.*got: 'unknown'"):
        get_wdyn_profile("unknown")


def test_agent_unknown_wdyn_profile_fail_fast():
    """Agent with scale_delta and unknown Wdyn_profile → fail-fast at init."""
    cfg = SexTransitConfig(sex_transit_mode="scale_delta", sex_transit_Wdyn_profile="nonexistent")
    with pytest.raises(ValueError, match=r"sex_transit_Wdyn_profile must be a registered profile"):
        Agent(_birth_data(), lifecycle=False, sex_transit_config=cfg)
