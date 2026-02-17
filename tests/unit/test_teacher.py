"""Planetary Teacher MVP (Future): create, daily modulation, pilot run."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from hnh.core.parameters import BehavioralVector
from hnh.interface.teacher import (
    create_planetary_teacher,
    pilot_run,
    PlanetaryTeacher,
)


@pytest.fixture(autouse=True)
def _clear_registry():
    from hnh.core.identity import _registry
    _registry.clear()
    yield
    _registry.clear()


def test_create_planetary_teacher_without_natal() -> None:
    """Create teacher (no pyswisseph → no natal); identity has base_traits only."""
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.4,
        verbosity=0.6,
        correction_rate=0.3,
        humor_level=0.5,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    # Pass birth date that would need natal; if swisseph missing, we get teacher without natal
    birth = datetime(1990, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    teacher = create_planetary_teacher("Alpha", birth, 55.75, 37.62, base_traits=base)
    assert teacher.label == "Alpha"
    assert teacher.identity.identity_id == "teacher-Alpha"
    assert teacher.identity.base_behavior_vector.to_dict() == base.to_dict()


def test_teacher_state_for_date() -> None:
    """Daily modulation: state_for_date returns DynamicState for injected time."""
    base = BehavioralVector(
        warmth=0.4,
        strictness=0.5,
        verbosity=0.5,
        correction_rate=0.3,
        humor_level=0.6,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    birth = datetime(1985, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    teacher = create_planetary_teacher("Beta", birth, 0.0, 0.0, base_traits=base)
    injected = datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
    state = teacher.state_for_date(injected, seed=42)
    assert state.identity_hash == teacher.identity.identity_hash
    assert state.final_behavior_vector is not None


def test_pilot_run_returns_list_of_states() -> None:
    """Pilot run for date range returns (date, state) list."""
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.5,
        verbosity=0.5,
        correction_rate=0.5,
        humor_level=0.5,
        challenge_intensity=0.5,
        pacing=0.5,
    )
    birth = datetime(1990, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    teacher = create_planetary_teacher("Pilot", birth, 0.0, 0.0, base_traits=base)
    start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    end = datetime(2024, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    results = pilot_run(teacher, start, end, seed=0, step_days=1)
    assert len(results) == 5
    for (dt, state) in results:
        assert state.identity_hash == teacher.identity.identity_hash
    dates = [dt for dt, _ in results]
    assert dates[0] == start
    assert dates[-1] == end
