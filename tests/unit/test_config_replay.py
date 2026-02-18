"""Unit tests for ReplayConfig, configuration_hash, hierarchy (Spec 002 T4)."""

from __future__ import annotations

import pytest

from hnh.config.replay_config import (
    ENGINE_SHOCK_MULTIPLIER_HARD_CAP,
    ReplayConfig,
    compute_configuration_hash,
    resolve_max_delta,
)
from hnh.identity.schema import AXES, get_parameter_index


def test_shock_cap_enforced() -> None:
    """shock_multiplier > 2.0 raises."""
    with pytest.raises(ValueError, match="must be ≤"):
        ReplayConfig(
            global_max_delta=0.15,
            shock_threshold=0.8,
            shock_multiplier=2.5,
        )


def test_configuration_hash_stable() -> None:
    """Same config → same hash."""
    c = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)
    h1 = compute_configuration_hash(c)
    h2 = compute_configuration_hash(c)
    assert h1 == h2


def test_hierarchy_parameter_over_axis_over_global() -> None:
    """resolve_max_delta: parameter > axis > global."""
    c = ReplayConfig(
        global_max_delta=0.2,
        shock_threshold=0.8,
        shock_multiplier=1.0,
        axis_max_delta=(("emotional_tone", 0.15),),
        parameter_max_delta=(("warmth", 0.1),),
    )
    # warmth is in emotional_tone; param override
    warmth_ix = get_parameter_index("warmth")
    assert resolve_max_delta(warmth_ix, c, "emotional_tone") == 0.1
    # empathy: axis override
    empathy_ix = get_parameter_index("empathy")
    assert resolve_max_delta(empathy_ix, c, "emotional_tone") == 0.15
    # param in another axis: global
    stability_ix = get_parameter_index("stability")
    assert resolve_max_delta(stability_ix, c, "stability_regulation") == 0.2


def test_apply_bounds_clamps_and_shock() -> None:
    """apply_bounds clamps raw_delta; shock multiplies effective max."""
    from hnh.identity.schema import NUM_PARAMETERS
    from hnh.modulation.boundaries import apply_bounds

    config = ReplayConfig(global_max_delta=0.1, shock_threshold=0.8, shock_multiplier=1.5)
    raw = [0.2] * NUM_PARAMETERS  # over 0.1
    bounded_no_shock, eff_no = apply_bounds(tuple(raw), config, shock_active=False)
    bounded_shock, eff_shock = apply_bounds(tuple(raw), config, shock_active=True)
    assert all(abs(b) <= 0.1 for b in bounded_no_shock)
    assert all(e == 0.1 for e in eff_no)
    assert all(abs(e - 0.15) < 1e-9 for e in eff_shock)
    assert all(abs(b) <= 0.15 + 1e-9 for b in bounded_shock)


def test_apply_bounds_rejects_wrong_length() -> None:
    """apply_bounds raises if raw_delta length != 32."""
    from hnh.modulation.boundaries import apply_bounds

    config = ReplayConfig(global_max_delta=0.1, shock_threshold=0.8, shock_multiplier=1.5)
    with pytest.raises(ValueError, match="raw_delta length must be 32"):
        apply_bounds((0.1,) * 31, config)
