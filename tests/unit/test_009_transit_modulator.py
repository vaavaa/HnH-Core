"""T010: SexTransitModulator — M in [1-mcap, 1+mcap], symmetry M(male)≈2-M(female), E=0→M=1."""

import pytest

from hnh.identity.schema import NUM_PARAMETERS
from hnh.sex.transit_modulator import (
    compute_multipliers,
    apply_bounded_delta_eff,
    get_wdyn_profile,
    registered_wdyn_profiles,
)


def test_E_zero_M_all_one():
    """E=0 → M[i]=1 for all i."""
    M = compute_multipliers(0.0, "v1", beta=0.05, mcap=0.10)
    assert M == (1.0,) * NUM_PARAMETERS


def test_M_in_bounds():
    """M[i] in [1-mcap, 1+mcap] for non-zero E."""
    for E in (0.5, -0.5, 1.0, -1.0):
        M = compute_multipliers(E, "v1", beta=0.05, mcap=0.10)
        for i in range(NUM_PARAMETERS):
            assert 0.90 <= M[i] <= 1.10, f"E={E} M[{i}]={M[i]}"


def test_symmetry_M_male_approx_2_minus_M_female():
    """M(male E=+0.5) ≈ 2 - M(female E=-0.5) per SC-002."""
    M_m = compute_multipliers(0.5, "v1", beta=0.05, mcap=0.10)
    M_f = compute_multipliers(-0.5, "v1", beta=0.05, mcap=0.10)
    for i in range(NUM_PARAMETERS):
        assert abs(M_m[i] + M_f[i] - 2.0) < 1e-9, f"axis {i}: M_m[i]+M_f[i] should be 2"


def test_apply_bounded_delta_eff():
    """bounded_delta_eff[i] = bounded_delta[i] * M[i]."""
    delta = (0.01,) * NUM_PARAMETERS
    M = compute_multipliers(0.5, "v1", beta=0.05, mcap=0.10)
    eff = apply_bounded_delta_eff(delta, M)
    assert len(eff) == NUM_PARAMETERS
    for i in range(NUM_PARAMETERS):
        assert abs(eff[i] - delta[i] * M[i]) < 1e-12


def test_get_wdyn_profile_v1():
    """v1 returns 32-element tuple."""
    w = get_wdyn_profile("v1")
    assert len(w) == NUM_PARAMETERS
    assert isinstance(w, tuple)


def test_registered_profiles_includes_v1():
    """Registered profiles include 'v1'."""
    assert "v1" in registered_wdyn_profiles()
