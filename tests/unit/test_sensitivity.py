"""
Unit tests for Spec 002: Sensitivity Engine (T2.1–T2.4).
"""

from __future__ import annotations

import pytest

from hnh.identity import compute_sensitivity, sensitivity_histogram
from hnh.identity.schema import NUM_PARAMETERS


def test_sensitivity_vector_length_and_range() -> None:
    """Sensitivity is 32 values, each in [0, 1]."""
    natal = {"positions": [], "aspects": []}
    vec = compute_sensitivity(natal)
    assert len(vec) == NUM_PARAMETERS
    for v in vec:
        assert 0.0 <= v <= 1.0


def test_sensitivity_deterministic() -> None:
    """Same natal_data → same vector."""
    natal = {
        "positions": [
            {"planet": "Moon", "longitude": 45.0},
            {"planet": "Saturn", "longitude": 120.0},
        ],
        "aspects": [],
    }
    a = compute_sensitivity(natal)
    b = compute_sensitivity(natal)
    assert a == b


def test_sensitivity_not_hardcoded() -> None:
    """Different natal data → different vector (distribution not constant)."""
    empty = {"positions": [], "aspects": []}
    with_saturn = {"positions": [{"planet": "Saturn", "longitude": 0.0}], "aspects": []}
    with_uranus = {"positions": [{"planet": "Uranus", "longitude": 300.0}], "aspects": []}
    v_empty = compute_sensitivity(empty)
    v_saturn = compute_sensitivity(with_saturn)
    v_uranus = compute_sensitivity(with_uranus)
    assert v_empty != v_saturn or v_empty != v_uranus


def test_sensitivity_histogram_debug() -> None:
    """Debug histogram export works; keys present."""
    natal = {"positions": [{"planet": "Sun", "longitude": 15.0}], "aspects": []}
    vec = compute_sensitivity(natal)
    hist = sensitivity_histogram(vec)
    assert "histogram" in hist
    assert "low_sensitivity_pct" in hist
    assert "high_sensitivity_pct" in hist
    assert "min" in hist
    assert "max" in hist
    assert "mean" in hist
    assert sum(hist["histogram"].values()) == NUM_PARAMETERS


def test_sensitivity_histogram_all_buckets() -> None:
    """Histogram covers all four buckets (0-0.25, 0.25-0.5, 0.5-0.75, 0.75-1.0)."""
    vec = (0.1,) * 8 + (0.4,) * 8 + (0.6,) * 8 + (0.9,) * 8
    hist = sensitivity_histogram(vec)
    assert hist["histogram"]["0.00-0.25"] == 8
    assert hist["histogram"]["0.25-0.50"] == 8
    assert hist["histogram"]["0.50-0.75"] == 8
    assert hist["histogram"]["0.75-1.00"] == 8


def test_sensitivity_saturn_modalities() -> None:
    """Saturn in cardinal/fixed/mutable gives different stabilization factors."""
    # Saturn at 15° = Aries = cardinal (mod_ix 0) -> 0.75
    v_card = compute_sensitivity({"positions": [{"planet": "Saturn", "longitude": 15.0}], "aspects": []})
    # Saturn at 45° = Taurus = fixed (mod_ix 1) -> 0.85
    v_fixed = compute_sensitivity({"positions": [{"planet": "Saturn", "longitude": 45.0}], "aspects": []})
    # Saturn at 75° = Gemini = mutable (mod_ix 2) -> 0.90
    v_mut = compute_sensitivity({"positions": [{"planet": "Saturn", "longitude": 75.0}], "aspects": []})
    assert v_card != v_fixed or v_fixed != v_mut


def test_sensitivity_uranus_modalities() -> None:
    """Uranus in fixed/cardinal/mutable gives different disruption factors."""
    # Uranus at 300° = Aquarius = fixed (mod_ix 1) -> 1.25
    v_fixed = compute_sensitivity({"positions": [{"planet": "Uranus", "longitude": 300.0}], "aspects": []})
    # Uranus at 15° = Aries = cardinal -> 1.15
    v_card = compute_sensitivity({"positions": [{"planet": "Uranus", "longitude": 15.0}], "aspects": []})
    # Uranus at 75° = Gemini = mutable -> 1.10
    v_mut = compute_sensitivity({"positions": [{"planet": "Uranus", "longitude": 75.0}], "aspects": []})
    assert v_fixed != v_card or v_card != v_mut


def test_sensitivity_aspect_tension_branches() -> None:
    """Aspect tension code paths: square/opposition, trine/sextile, other (name key)."""
    square = {"positions": [], "aspects": [{"aspect": "Square"}]}
    trine = {"positions": [], "aspects": [{"aspect": "Trine"}]}
    other = {"positions": [], "aspects": [{"name": "Conjunction"}]}
    v1 = compute_sensitivity(square)
    v2 = compute_sensitivity(trine)
    v3 = compute_sensitivity(other)
    assert len(v1) == NUM_PARAMETERS and len(v2) == NUM_PARAMETERS and len(v3) == NUM_PARAMETERS


def test_sensitivity_empty_positions_same_raw_normalize() -> None:
    """Empty positions + empty aspects -> baseline 0.5, min==max -> return 0.5 everywhere."""
    natal = {"positions": [], "aspects": []}
    vec = compute_sensitivity(natal)
    assert all(abs(x - 0.5) < 1e-9 for x in vec)


def test_sensitivity_skips_position_without_planet() -> None:
    """Position with no planet key or empty planet is skipped (no crash)."""
    natal = {"positions": [{"longitude": 90.0}, {"planet": "", "longitude": 0.0}], "aspects": []}
    vec = compute_sensitivity(natal)
    assert len(vec) == NUM_PARAMETERS


def test_sensitivity_skips_unknown_planet() -> None:
    """Position with planet not in _PLANET_AXIS (e.g. Pluto) is skipped."""
    natal = {"positions": [{"planet": "Pluto", "longitude": 200.0}], "aspects": []}
    vec = compute_sensitivity(natal)
    assert len(vec) == NUM_PARAMETERS
