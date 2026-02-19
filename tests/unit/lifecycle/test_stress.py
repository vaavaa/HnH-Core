"""Tests for transit stress I_T, S_T (Spec 005 §4, contract transit-stress)."""

import pytest

from hnh.lifecycle.stress import (
    compute_raw_transit_intensity,
    compute_transit_stress,
)
from hnh.lifecycle.constants import HARD_ASPECTS, C_T_DEFAULT


def test_hard_aspects_only() -> None:
    # Trine and Sextile must not contribute
    aspects = [
        {"aspect": "Trine", "separation": 120.0, "angle": 120.0},
        {"aspect": "Sextile", "separation": 60.0, "angle": 60.0},
    ]
    i_t = compute_raw_transit_intensity(aspects)
    assert i_t == 0.0
    _, s_t = compute_transit_stress(aspects)
    assert s_t == 0.0


def test_conjunction_contributes() -> None:
    aspects = [{"aspect": "Conjunction", "separation": 2.0, "angle": 0.0}]
    i_t = compute_raw_transit_intensity(aspects)
    assert i_t > 0
    orb = 8.0
    decay = max(0, 1 - 2.0 / orb)  # 0.75
    assert abs(i_t - 1.0 * decay) < 1e-6


def test_s_t_clipped() -> None:
    # Many aspects -> I_T large -> S_T clipped to 1
    aspects = [
        {"aspect": "Square", "separation": 90.0, "angle": 90.0},
        {"aspect": "Opposition", "separation": 180.0, "angle": 180.0},
        {"aspect": "Conjunction", "separation": 0.0, "angle": 0.0},
    ]
    _, s_t = compute_transit_stress(aspects, c_t=0.5)
    assert 0 <= s_t <= 1.0


def test_determinism() -> None:
    aspects = [
        {"aspect": "Square", "separation": 91.0, "angle": 90.0},
        {"aspect": "Conjunction", "separation": 1.0, "angle": 0.0},
    ]
    i1, s1 = compute_transit_stress(aspects, c_t=C_T_DEFAULT)
    i2, s2 = compute_transit_stress(aspects, c_t=C_T_DEFAULT)
    assert i1 == i2 and s1 == s2


def test_s_t_scale() -> None:
    # I_T = 1.5, C_T = 3.0 -> S_T = 0.5
    aspects = [{"aspect": "Conjunction", "separation": 4.0, "angle": 0.0}]  # decay 0.5, weight 1 -> 0.5
    i_t = compute_raw_transit_intensity(aspects)
    # dev=4, orb=8 -> decay=0.5 -> I_T=0.5. So S_T = 0.5/3 = 0.166...
    _, s_t = compute_transit_stress(aspects, c_t=3.0)
    assert abs(s_t - (0.5 / 3.0)) < 1e-6
