"""T011: SexPolarityEngine (FR-008, FR-009)."""

import pytest

from hnh.sex.polarity import sex_score, compute_E


def test_sex_score():
    """FR-008: male +1, female -1, None 0."""
    assert sex_score("male") == 1.0
    assert sex_score("female") == -1.0
    assert sex_score(None) == 0.0


def test_compute_E_clamp():
    """FR-009: E in [-1, 1]."""
    E = compute_E("male", 1.0, 1)
    assert -1.0 <= E <= 1.0
    E = compute_E("female", -1.0, -1)
    assert -1.0 <= E <= 1.0


def test_compute_E_none_zero():
    """sex=None -> E from astro terms only (b, c)."""
    E = compute_E(None, 0.0, 0)
    assert E == 0.0
