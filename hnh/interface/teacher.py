"""
Planetary Teacher MVP (Future): fixed birth date, daily modulation, pilot helper.
Wraps Identity + optional natal; no LLM in core.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from hnh.core.identity import IdentityCore
from hnh.core.natal import build_natal_positions
from hnh.core.parameters import BehavioralVector
from hnh.state.replay import run_step
from hnh.state.dynamic_state import DynamicState


def _default_base_traits() -> BehavioralVector:
    return BehavioralVector(
        warmth=0.5,
        strictness=0.4,
        verbosity=0.6,
        correction_rate=0.3,
        humor_level=0.5,
        challenge_intensity=0.4,
        pacing=0.5,
    )


@dataclass
class PlanetaryTeacher:
    """First Planetary Teacher: label + Identity (with optional natal)."""

    label: str
    identity: IdentityCore

    def state_for_date(
        self,
        injected_time: datetime,
        seed: int | None = None,
        relational_snapshot: dict[str, float] | None = None,
    ) -> DynamicState:
        """Daily modulation: get Dynamic State for given date (injected time)."""
        return run_step(
            self.identity,
            injected_time,
            seed=seed,
            relational_snapshot=relational_snapshot,
        )


def create_planetary_teacher(
    label: str,
    birth_datetime: datetime,
    latitude: float,
    longitude: float,
    base_traits: BehavioralVector | None = None,
) -> PlanetaryTeacher:
    """
    Instantiate a Planetary Teacher with fixed birth date and natal.
    identity_id = teacher-{label}. Requires pyswisseph for natal; otherwise uses base_traits only.
    """
    identity_id = f"teacher-{label}"
    base = base_traits or _default_base_traits()
    symbolic_input: dict[str, Any] | None = None
    try:
        natal_positions = build_natal_positions(birth_datetime, latitude, longitude)
        symbolic_input = {"natal_positions": natal_positions}
    except Exception:
        pass  # no pyswisseph or invalid input → identity without natal
    identity = IdentityCore(
        identity_id=identity_id,
        base_traits=base,
        symbolic_input=symbolic_input,
    )
    return PlanetaryTeacher(label=label, identity=identity)


def pilot_run(
    teacher: PlanetaryTeacher,
    start_date: datetime,
    end_date: datetime,
    seed: int = 0,
    step_days: int = 1,
) -> list[tuple[datetime, DynamicState]]:
    """
    Run simulation for date range; return list of (date, state).
    Internal logs can be written by caller (e.g. state_logger.write_record).
    """
    from datetime import timedelta

    result: list[tuple[datetime, DynamicState]] = []
    current = start_date
    while current <= end_date:
        state = teacher.state_for_date(current, seed=seed)
        result.append((current, state))
        current = current + timedelta(days=step_days)
    return result
