"""
Unit tests for Zodiac Expression Layer (Spec 004).
Determinism, ruler influence, normalization [0,1], sign with no planets, dominant_sign/dominant_element.
"""

from __future__ import annotations

import pytest

from hnh.astrology import zodiac_expression as ze


def test_sign_ruler_modern_12_elements():
    """SIGN_RULER_MODERN has 12 entries (sign 0..11)."""
    assert len(ze.SIGN_RULER_MODERN) == 12
    for i in range(12):
        assert isinstance(ze.SIGN_RULER_MODERN[i], str)
        assert ze.SIGN_RULER_MODERN[i] in (
            "Sun", "Moon", "Mercury", "Venus", "Mars",
            "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
        )


def test_compute_zodiac_output_deterministic():
    """Same positions + aspects → same sign_energy_vector, dominant_sign, dominant_element."""
    positions = [
        {"planet": "Sun", "longitude": 280.0, "sign": 9, "house": 10, "angular_strength": 1.0},
        {"planet": "Moon", "longitude": 45.0, "sign": 1, "house": 2, "angular_strength": 0.6},
    ]
    aspects = [
        {"planet1": "Sun", "planet2": "Moon", "aspect": "Square", "angle": 90.0},
    ]
    out1 = ze.compute_zodiac_output(positions, aspects)
    out2 = ze.compute_zodiac_output(positions, aspects)
    assert out1["sign_energy_vector"] == out2["sign_energy_vector"]
    assert out1["dominant_sign"] == out2["dominant_sign"]
    assert out1["dominant_element"] == out2["dominant_element"]


def test_compute_zodiac_output_normalization_bounds():
    """All 12×4 values in [0, 1]."""
    positions = [
        {"planet": "Sun", "longitude": 0.0, "sign": 0, "house": 1, "angular_strength": 1.0},
        {"planet": "Mars", "longitude": 30.0, "sign": 0, "house": 1, "angular_strength": 1.0},
    ]
    aspects = []
    out = ze.compute_zodiac_output(positions, aspects)
    for row in out["sign_energy_vector"]:
        assert len(row) == 4
        for x in row:
            assert 0 <= x <= 1, f"value {x} out of [0,1]"


def test_sign_with_no_planets_ruler_only():
    """Sign with no planets: only ruler and aspects to ruler contribute; else (0,0,0,0)."""
    # All planets in sign 0 (Aries); sign 7 (Scorpio) has none. Ruler of Scorpio = Pluto.
    positions = [
        {"planet": "Sun", "longitude": 10.0, "sign": 0, "house": 1, "angular_strength": 1.0},
        {"planet": "Pluto", "longitude": 235.0, "sign": 7, "house": 4, "angular_strength": 1.0},
    ]
    aspects = []
    out = ze.compute_zodiac_output(positions, aspects)
    # Scorpio (7): no planets in sign, but Pluto (ruler) is in Scorpio with angular 1.0 → stability etc. can be > 0
    z7 = out["sign_energy_vector"][7]
    assert all(0 <= x <= 1 for x in z7)


def test_dominant_sign_max_intensity():
    """dominant_sign is the sign with maximum intensity (first dimension)."""
    # Put one planet in sign 4 (Leo) with high angular → that sign gets higher intensity
    positions = [
        {"planet": "Sun", "longitude": 120.0, "sign": 4, "house": 1, "angular_strength": 1.0},
    ]
    aspects = []
    out = ze.compute_zodiac_output(positions, aspects)
    # Sign 4 should have non-zero intensity; dominant_sign could be 4
    intensities = [row[0] for row in out["sign_energy_vector"]]
    dominant = out["dominant_sign"]
    assert intensities[dominant] == max(intensities)


def test_dominant_element_sum_of_intensity():
    """dominant_element is element with max sum of intensity over its 3 signs."""
    out = ze.compute_zodiac_output([], [])
    assert out["dominant_element"] in ("Fire", "Earth", "Air", "Water")


def test_compute_zodiac_output_shape():
    """Output has sign_energy_vector (12 tuples of 4), dominant_sign, dominant_sign_element, dominant_element."""
    out = ze.compute_zodiac_output([], [])
    assert "sign_energy_vector" in out
    assert len(out["sign_energy_vector"]) == 12
    for row in out["sign_energy_vector"]:
        assert isinstance(row, (tuple, list)) and len(row) == 4
    assert "dominant_sign" in out
    assert "dominant_sign_element" in out
    assert "dominant_element" in out
    assert 0 <= out["dominant_sign"] <= 11
    assert out["dominant_sign_element"] in ("Fire", "Earth", "Air", "Water")


def test_dominant_sign_element_is_element_of_dominant_sign():
    """dominant_sign_element is the element of the dominant sign (e.g. Scorpio → Water)."""
    # Force dominant sign = 7 (Scorpio) by putting planets there with high intensity
    positions = [
        {"planet": "Mars", "longitude": 235.0, "sign": 7, "house": 1, "angular_strength": 1.0},
        {"planet": "Pluto", "longitude": 240.0, "sign": 7, "house": 1, "angular_strength": 1.0},
    ]
    aspects = [{"planet1": "Mars", "planet2": "Pluto", "aspect": "Conjunction", "angle": 0.0}]
    out = ze.compute_zodiac_output(positions, aspects)
    assert out["dominant_sign"] == 7
    assert out["dominant_sign_name"] == "Scorpio"
    assert out["dominant_sign_element"] == "Water"
