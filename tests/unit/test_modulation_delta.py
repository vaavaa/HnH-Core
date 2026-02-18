"""Unit tests for 32-param raw delta (Spec 002 T3.3)."""

from __future__ import annotations

from hnh.identity.schema import AXES, NUM_PARAMETERS, PARAMETERS, get_parameter_axis_index
from hnh.modulation.delta import (
    PHASE_WINDOW_DAYS_BY_CATEGORY,
    compute_raw_delta_32,
    compute_raw_delta_32_by_category,
)


def _axis_indices(axis_name: str) -> set[int]:
    axis_ix = AXES.index(axis_name)
    return {i for i in range(NUM_PARAMETERS) if get_parameter_axis_index(i) == axis_ix}


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


def test_mercury_aspect_produces_nonzero_cognitive_delta() -> None:
    """Mercury aspect must move cognitive_style (non-zero)."""
    aspects = [
        {
            "planet1": "Mercury",
            "planet2": "Sun",
            "aspect": "Conjunction",
            "angle": 0.0,
            "separation": 0.0,
        }
    ]
    vec = compute_raw_delta_32(aspects)
    cog_ix = _axis_indices("cognitive_style")
    assert any(vec[i] != 0.0 for i in cog_ix)


def test_saturn_aspect_produces_nonzero_structure_delta() -> None:
    """Saturn aspect must move structure_discipline (non-zero)."""
    aspects = [
        {
            "planet1": "Saturn",
            "planet2": "Moon",
            "aspect": "Trine",
            "angle": 120.0,
            "separation": 120.0,
        }
    ]
    vec = compute_raw_delta_32(aspects)
    struct_ix = _axis_indices("structure_discipline")
    assert any(vec[i] != 0.0 for i in struct_ix)


def test_sun_aspect_produces_nonzero_power_delta() -> None:
    """Sun aspect must move power_boundaries (non-zero)."""
    aspects = [
        {
            "planet1": "Sun",
            "planet2": "Venus",
            "aspect": "Sextile",
            "angle": 60.0,
            "separation": 60.0,
        }
    ]
    vec = compute_raw_delta_32(aspects)
    power_ix = _axis_indices("power_boundaries")
    assert any(vec[i] != 0.0 for i in power_ix)


def test_raw_delta_32_by_category_sum_equals_full() -> None:
    """Sum of personal+social+outer raw_delta equals compute_raw_delta_32(all aspects)."""
    aspects = [
        {"planet1": "Mercury", "planet2": "Sun", "aspect": "Square", "angle": 90.0, "separation": 90.0},
        {"planet1": "Saturn", "planet2": "Moon", "aspect": "Trine", "angle": 120.0, "separation": 120.0},
    ]
    full = compute_raw_delta_32(aspects)
    by_cat = compute_raw_delta_32_by_category(aspects)
    summed = tuple(
        by_cat["personal"][i] + by_cat["social"][i] + by_cat["outer"][i]
        for i in range(NUM_PARAMETERS)
    )
    assert len(by_cat) == 3
    assert by_cat["personal"].__class__ == tuple
    assert PHASE_WINDOW_DAYS_BY_CATEGORY["personal"] == 7
    assert PHASE_WINDOW_DAYS_BY_CATEGORY["outer"] == 365
    for i in range(NUM_PARAMETERS):
        assert abs(full[i] - summed[i]) < 1e-9


def test_planet_does_not_move_unrelated_axes_unless_mapped() -> None:
    """With planet1/planet2 present, only affected axes may receive deltas."""
    aspects = [
        {
            "planet1": "Mercury",
            "planet2": "Sun",
            "aspect": "Square",
            "angle": 90.0,
            "separation": 90.0,
        }
    ]
    vec = compute_raw_delta_32(aspects)
    allowed = _axis_indices("cognitive_style") | _axis_indices("power_boundaries")
    for i, v in enumerate(vec):
        if i not in allowed:
            assert v == 0.0
