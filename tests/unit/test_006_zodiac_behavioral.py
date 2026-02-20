"""
T007: Unit tests for 006 ZodiacExpression and BehavioralCore.
ZodiacExpression: dominant_sign/element from natal; BehavioralCore: base/sensitivity from identity_config, apply_transits updates current_vector.
"""

from __future__ import annotations

import pytest

from hnh.astrology.natal_chart import NatalChart
from hnh.astrology.transit_state import TransitState
from hnh.astrology.zodiac_expression import ZodiacExpression
from hnh.identity.schema import NUM_PARAMETERS
from hnh.state.behavioral_core import BehavioralCore


# --- ZodiacExpression ---


def test_zodiac_expression_from_natal_chart():
    """ZodiacExpression: build from NatalChart; dominant_sign and dominant_element present."""
    birth_data = {
        "positions": [
            {"planet": "Sun", "longitude": 90.0},   # Cancer
            {"planet": "Moon", "longitude": 120.0}, # Leo
        ],
    }
    natal = NatalChart.from_birth_data(birth_data)
    zod = ZodiacExpression(natal)
    assert hasattr(zod, "dominant_sign")
    assert hasattr(zod, "dominant_element")
    assert 0 <= zod.dominant_sign <= 11
    assert zod.dominant_element in ("Fire", "Earth", "Air", "Water")
    assert len(zod.sign_vectors) == 12
    assert len(zod.sign_vectors[0]) == 4


def test_zodiac_expression_read_only():
    """ZodiacExpression: does not mutate natal (read-only view)."""
    birth_data = {"positions": [{"planet": "Sun", "longitude": 45.0}]}
    natal = NatalChart.from_birth_data(birth_data)
    zod = ZodiacExpression(natal)
    assert natal.planets[0].longitude == 45.0


# --- BehavioralCore ---


def _make_identity_config(base: tuple[float, ...] | None = None, sensitivity: tuple[float, ...] | None = None) -> object:
    n = NUM_PARAMETERS
    base = base or (0.5,) * n
    sensitivity = sensitivity or (0.3,) * n
    return type("Identity", (), {"base_vector": base, "sensitivity_vector": sensitivity})()


def test_behavioral_core_base_and_sensitivity_from_identity_config():
    """BehavioralCore: base_vector and sensitivity from identity_config; current_vector starts equal to base."""
    birth_data = {"positions": [{"planet": "Sun", "longitude": 0.0}]}
    natal = NatalChart.from_birth_data(birth_data)
    base = (0.4,) * NUM_PARAMETERS
    sens = (0.2,) * NUM_PARAMETERS
    identity = _make_identity_config(base=base, sensitivity=sens)
    core = BehavioralCore(natal, identity)
    assert core.base_vector == base
    assert core.current_vector == base


def test_behavioral_core_apply_transits_updates_current_vector():
    """BehavioralCore: apply_transits(transit_state) updates current_vector deterministically."""
    birth_data = {"positions": [{"planet": "Sun", "longitude": 0.0}]}
    natal = NatalChart.from_birth_data(birth_data)
    identity = _make_identity_config()
    core = BehavioralCore(natal, identity)
    base_before = core.base_vector
    current_before = core.current_vector
    # Small bounded_delta
    delta = (0.01,) * NUM_PARAMETERS
    state = TransitState(stress=0.1, raw_delta=delta, bounded_delta=delta)
    core.apply_transits(state)
    assert core.base_vector == base_before  # unchanged
    assert core.current_vector != current_before  # updated
    # Values should be clamped in [0, 1]
    for v in core.current_vector:
        assert 0.0 <= v <= 1.0


def test_behavioral_core_deterministic_same_inputs():
    """BehavioralCore: same identity_config and transit_state → same current_vector after apply_transits."""
    birth_data = {"positions": [{"planet": "Sun", "longitude": 0.0}]}
    natal = NatalChart.from_birth_data(birth_data)
    identity = _make_identity_config()
    core1 = BehavioralCore(natal, identity)
    core2 = BehavioralCore(natal, identity)
    state = TransitState(stress=0.0, raw_delta=(0.02,) * NUM_PARAMETERS, bounded_delta=(0.02,) * NUM_PARAMETERS)
    core1.apply_transits(state)
    core2.apply_transits(state)
    assert core1.current_vector == core2.current_vector
