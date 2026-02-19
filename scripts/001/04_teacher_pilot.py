#!/usr/bin/env python3
"""
Example: Planetary Teacher — create a "teacher" with fixed birth date and pilot run over a date range.

create_planetary_teacher creates Identity (optionally with natal chart if pyswisseph is installed).
pilot_run returns a list of (date, state) for the given period.

Run from project root:
  python scripts/04_teacher_pilot.py
  python scripts/04_teacher_pilot.py --days 14
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta

from hnh.core.parameters import BehavioralVector
from hnh.interface.teacher import create_planetary_teacher, pilot_run


def main() -> None:
    parser = argparse.ArgumentParser(description="Planetary Teacher: pilot run over dates")
    parser.add_argument("--days", type=int, default=7, help="Number of simulation days")
    parser.add_argument("--start", default="2024-09-01", help="Start date YYYY-MM-DD")
    args = parser.parse_args()

    birth = datetime(1985, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    base = BehavioralVector(
        warmth=0.55,
        strictness=0.35,
        verbosity=0.6,
        correction_rate=0.35,
        humor_level=0.55,
        challenge_intensity=0.4,
        pacing=0.5,
    )

    teacher = create_planetary_teacher(
        label="DemoTeacher",
        birth_datetime=birth,
        latitude=55.75,
        longitude=37.62,
        base_traits=base,
    )
    print(f"Teacher: {teacher.label}, identity_id: {teacher.identity.identity_id}")

    start = datetime.strptime(args.start, "%Y-%m-%d").replace(
        tzinfo=timezone.utc, hour=12, minute=0, second=0, microsecond=0
    )
    end = start + timedelta(days=args.days - 1)

    results = pilot_run(teacher, start, end, seed=0, step_days=1)
    print(f"\nPilot: {len(results)} days from {args.start}")
    for dt, state in results[:5]:  # first 5 days
        vec = state.final_behavior_vector.to_dict()
        print(f"  {dt.date()}: warmth={vec['warmth']:.2f} strictness={vec['strictness']:.2f} ...")
    if len(results) > 5:
        print(f"  ... and {len(results) - 5} more days.")


if __name__ == "__main__":
    main()
