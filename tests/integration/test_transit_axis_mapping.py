"""Integration tests: transit aspects -> raw_delta axis filtering (Spec 002).

These tests use the astrology layer (pyswisseph). They validate:
- Mercury aspects produce non-zero cognitive_style delta
- Saturn aspects produce non-zero structure_discipline delta
- Sun aspects produce non-zero power_boundaries delta
- No planet moves unrelated axes unless explicitly mapped (axis-filter correctness)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from hnh.core.natal import build_natal_positions
from hnh.identity.schema import AXES, NUM_PARAMETERS, get_parameter_axis_index
from hnh.modulation.delta import PLANET_AXIS_MAP, compute_raw_delta_32


def _axes_for_planet(planet: str | None) -> set[str]:
    if not planet:
        return set()
    ax = PLANET_AXIS_MAP.get(planet)
    if ax is None:
        return set()
    if isinstance(ax, str):
        return {ax}
    return set(ax)


def _allowed_axes_for_aspects(aspects: list[dict]) -> set[str]:
    allowed: set[str] = set()
    for a in aspects:
        allowed |= _axes_for_planet(a.get("planet1"))
        allowed |= _axes_for_planet(a.get("planet2"))
    return allowed


def _axis_name_for_param_index(p_ix: int) -> str:
    return AXES[get_parameter_axis_index(p_ix)]


def _find_nonzero_delta_for_planet(
    planet: str,
    natal_positions: dict,
    start: datetime,
    days: int,
) -> tuple[list[dict], tuple[float, ...]]:
    """Search forward until we find planet aspects that produce a non-zero delta."""
    from hnh.astrology import ephemeris as eph
    from hnh.astrology import transits as tr

    if eph.swe is None:  # pragma: no cover
        pytest.skip("pyswisseph not installed (install with hnh[astrology])")

    for d in range(days):
        injected = start + timedelta(days=d)
        sig = tr.compute_transit_signature(injected, natal_positions)
        aspects = sig.get("aspects_to_natal", [])
        subset = [a for a in aspects if a.get("planet1") == planet or a.get("planet2") == planet]
        if not subset:
            continue
        vec = compute_raw_delta_32(subset)
        if any(v != 0.0 for v in vec):
            return (subset, vec)
    pytest.fail(f"Did not find any non-zero delta for {planet!r} within {days} days")


@pytest.mark.integration
def test_mercury_aspects_produce_cognitive_and_only_related_axes() -> None:
    natal = build_natal_positions(datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc), 51.5074, -0.1278)
    subset, vec = _find_nonzero_delta_for_planet(
        "Mercury",
        natal,
        start=datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc),
        days=366,
    )

    allowed_axes = _allowed_axes_for_aspects(subset)
    assert "cognitive_style" in allowed_axes  # sanity (Mercury is mapped to cognitive_style)

    # Must move cognitive axis
    cognitive_ix = {i for i in range(NUM_PARAMETERS) if _axis_name_for_param_index(i) == "cognitive_style"}
    assert any(vec[i] != 0.0 for i in cognitive_ix)

    # Must not move unrelated axes
    for i, v in enumerate(vec):
        if _axis_name_for_param_index(i) not in allowed_axes:
            assert v == 0.0


@pytest.mark.integration
def test_saturn_aspects_produce_structure_and_only_related_axes() -> None:
    natal = build_natal_positions(datetime(1999, 6, 1, 12, 0, tzinfo=timezone.utc), 51.5074, -0.1278)
    subset, vec = _find_nonzero_delta_for_planet(
        "Saturn",
        natal,
        start=datetime(1999, 6, 1, 12, 0, tzinfo=timezone.utc),
        days=366 * 2,
    )

    allowed_axes = _allowed_axes_for_aspects(subset)
    assert "structure_discipline" in allowed_axes  # Saturn maps to structure_discipline (and stability)

    structure_ix = {i for i in range(NUM_PARAMETERS) if _axis_name_for_param_index(i) == "structure_discipline"}
    assert any(vec[i] != 0.0 for i in structure_ix)

    for i, v in enumerate(vec):
        if _axis_name_for_param_index(i) not in allowed_axes:
            assert v == 0.0


@pytest.mark.integration
def test_sun_aspects_produce_power_and_only_related_axes() -> None:
    natal = build_natal_positions(datetime(2001, 9, 1, 12, 0, tzinfo=timezone.utc), 51.5074, -0.1278)
    subset, vec = _find_nonzero_delta_for_planet(
        "Sun",
        natal,
        start=datetime(2001, 9, 1, 12, 0, tzinfo=timezone.utc),
        days=366,
    )

    allowed_axes = _allowed_axes_for_aspects(subset)
    assert "power_boundaries" in allowed_axes  # Sun maps to power_boundaries

    power_ix = {i for i in range(NUM_PARAMETERS) if _axis_name_for_param_index(i) == "power_boundaries"}
    assert any(vec[i] != 0.0 for i in power_ix)

    for i, v in enumerate(vec):
        if _axis_name_for_param_index(i) not in allowed_axes:
            assert v == 0.0

