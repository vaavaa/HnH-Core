"""T008: compute_age_delta_32 bounds, apply_daily_lipschitz cap per call."""

import pytest

from hnh.age.delta_32 import apply_daily_lipschitz, compute_age_delta_32
from hnh.identity.schema import NUM_PARAMETERS


def test_compute_age_delta_32_length():
    """Result length is 32."""
    features = (0.0, 0.0, 0.0, 0.0, 0.0)
    out = compute_age_delta_32(features, age_strength=0.04, age_max_param_delta=0.06)
    assert len(out) == NUM_PARAMETERS


def test_compute_age_delta_32_bounds():
    """Each component in [-age_max_param_delta, +age_max_param_delta]."""
    max_delta = 0.06
    # Use non-zero features to get non-zero delta
    features = (0.5, 0.5, 0.0, 0.0, 0.0)
    out = compute_age_delta_32(features, age_strength=0.04, age_max_param_delta=max_delta)
    for i in range(NUM_PARAMETERS):
        assert -max_delta - 1e-9 <= out[i] <= max_delta + 1e-9


def test_compute_age_delta_32_zero_features():
    """Zero features -> zero delta."""
    features = (0.0, 0.0, 0.0, 0.0, 0.0)
    out = compute_age_delta_32(features, age_strength=0.04, age_max_param_delta=0.06)
    assert out == (0.0,) * NUM_PARAMETERS


def test_compute_age_delta_32_wrong_features_length_raises():
    """features length != 5 raises ValueError."""
    with pytest.raises(ValueError, match="features must have length 5"):
        compute_age_delta_32((0.0,) * 4, 0.04, 0.06)
    with pytest.raises(ValueError, match="features must have length 5"):
        compute_age_delta_32((0.0,) * 6, 0.04, 0.06)


def test_apply_daily_lipschitz_first_call_returns_raw():
    """When prev_delta_32 is None, return raw_delta_32 unchanged."""
    raw = (0.01,) * NUM_PARAMETERS
    out = apply_daily_lipschitz(None, raw, L=0.001)
    assert out == raw


def test_apply_daily_lipschitz_caps_per_component():
    """Per component: |out[i] - prev[i]| <= L."""
    L = 0.001
    prev = (0.0,) * NUM_PARAMETERS
    # raw much larger than prev -> each component can move at most L
    raw = (0.05,) * NUM_PARAMETERS
    out = apply_daily_lipschitz(prev, raw, L=L)
    for i in range(NUM_PARAMETERS):
        assert abs(out[i] - prev[i]) <= L + 1e-12


def test_apply_daily_lipschitz_small_change_unchanged():
    """When |raw - prev| <= L everywhere, out == raw."""
    prev = (0.0,) * (NUM_PARAMETERS - 1) + (0.0005,)
    raw = (0.0,) * (NUM_PARAMETERS - 1) + (0.0008,)
    out = apply_daily_lipschitz(prev, raw, L=0.001)
    assert out == raw


def test_apply_daily_lipschitz_wrong_length_raises():
    """Wrong length prev or raw raises ValueError."""
    with pytest.raises(ValueError, match=f"length {NUM_PARAMETERS}"):
        apply_daily_lipschitz((0.0,) * 31, (0.0,) * NUM_PARAMETERS, 0.001)
    with pytest.raises(ValueError, match=f"length {NUM_PARAMETERS}"):
        apply_daily_lipschitz((0.0,) * NUM_PARAMETERS, (0.0,) * 30, 0.001)
