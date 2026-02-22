"""T011: SexDelta32Engine, W32 v1, BOUND-32-1, BOUND-32-3."""

import pytest

from hnh.sex.delta_32 import W32_V1, compute_sex_delta_32, DEFAULT_SEX_STRENGTH, DEFAULT_SEX_MAX_PARAM_DELTA


def test_w32_v1_length():
    """W32 v1 has 32 elements (FR-022)."""
    assert len(W32_V1) == 32


def test_bound_32_1():
    """BOUND-32-1: |sex_delta[i]| <= sex_max_param_delta."""
    delta = compute_sex_delta_32(1.0)
    for x in delta:
        assert abs(x) <= DEFAULT_SEX_MAX_PARAM_DELTA


def test_bound_32_3():
    """BOUND-32-3: L_infinity <= sex_max_param_delta."""
    delta = compute_sex_delta_32(-1.0)
    assert max(abs(x) for x in delta) <= DEFAULT_SEX_MAX_PARAM_DELTA


def test_zero_E_zero_delta():
    """E=0 -> all zeros."""
    delta = compute_sex_delta_32(0.0)
    assert delta == (0.0,) * 32
