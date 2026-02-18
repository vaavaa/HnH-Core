"""Unit tests for 32-param raw delta (Spec 002 T3.3)."""

from __future__ import annotations

from hnh.identity.schema import NUM_PARAMETERS
from hnh.modulation.delta import compute_raw_delta_32


def test_raw_delta_32_length() -> None:
    """Output is 32 floats."""
    vec = compute_raw_delta_32([])
    assert len(vec) == NUM_PARAMETERS


def test_raw_delta_deterministic() -> None:
    """Same aspects → same raw_delta."""
    aspects = [
        {"aspect": "Trine", "angle": 120.0, "separation": 119.5},
        {"aspect": "Square", "angle": 90.0, "separation": 91.0},
    ]
    a = compute_raw_delta_32(aspects)
    b = compute_raw_delta_32(aspects)
    assert a == b


def test_raw_delta_bounded_magnitude() -> None:
    """Many aspects don't explode (bounded by weights)."""
    aspects = [
        {"aspect": "Square", "angle": 90.0, "separation": 90.0},
        {"aspect": "Square", "angle": 90.0, "separation": 90.0},
        {"aspect": "Opposition", "angle": 180.0, "separation": 180.0},
    ]
    vec = compute_raw_delta_32(aspects)
    for v in vec:
        assert abs(v) < 1.0  # single-aspect weights are small
    assert any(v != 0.0 for v in vec)


def test_raw_delta_intensity_conjunction_and_missing_separation() -> None:
    """Conjunction (angle 0) and aspect without separation use intensity factor correctly."""
    # No separation -> intensity 1.0
    aspects_no_sep = [{"aspect": "Trine", "angle": 120.0}]
    vec = compute_raw_delta_32(aspects_no_sep)
    assert len(vec) == NUM_PARAMETERS
    # Conjunction with separation
    aspects_conj = [{"aspect": "Conjunction", "angle": 0.0, "separation": 2.0}]
    vec2 = compute_raw_delta_32(aspects_conj)
    assert any(v != 0.0 for v in vec2)


def test_raw_delta_custom_weights_and_orb_scale() -> None:
    """Custom aspect_weights and orb_scale are applied."""
    aspects = [{"aspect": "Square", "angle": 90.0, "separation": 90.0}]
    custom = {"Square": {"reactivity": 0.1}}
    vec = compute_raw_delta_32(aspects, aspect_weights=custom, orb_scale=0.5)
    assert len(vec) == NUM_PARAMETERS
    vec_default = compute_raw_delta_32(aspects)
    vec_scale = compute_raw_delta_32(aspects, orb_scale=2.0)
    assert vec != vec_default or vec != vec_scale


def test_raw_delta_aspect_not_in_weights_skipped() -> None:
    """Aspect name not in weights is skipped (no key error)."""
    aspects = [{"aspect": "Unknown", "angle": 90.0, "separation": 90.0}]
    vec = compute_raw_delta_32(aspects)
    assert all(v == 0.0 for v in vec)


def test_raw_delta_orb_scale_zero_intensity_one() -> None:
    """orb_scale=0 -> orb<=0 -> intensity 1.0 (branch coverage)."""
    aspects = [{"aspect": "Square", "angle": 90.0, "separation": 95.0}]
    vec = compute_raw_delta_32(aspects, orb_scale=0.0)
    assert len(vec) == NUM_PARAMETERS
    assert any(v != 0.0 for v in vec)
