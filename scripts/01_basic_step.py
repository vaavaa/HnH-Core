#!/usr/bin/env python3
"""
Example: one simulation step for a given date.
Analog of CLI: create Identity, call run_step, print vector and modifiers.

Run from project root (after pip install -e .):
  python scripts/01_basic_step.py
  python scripts/01_basic_step.py 2024-09-01
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from hnh.core.identity import IdentityCore
from hnh.core.parameters import BehavioralVector
from hnh.state.replay import run_step


def main() -> None:
    date_str = sys.argv[1] if len(sys.argv) > 1 else "2024-06-15"
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(
        tzinfo=timezone.utc, hour=12, minute=0, second=0, microsecond=0
    )

    base = BehavioralVector(
        warmth=0.5,
        strictness=0.4,
        verbosity=0.6,
        correction_rate=0.3,
        humor_level=0.5,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    identity = IdentityCore(
        identity_id="script-01-basic",
        base_traits=base,
        symbolic_input=None,
    )
    state = run_step(identity, dt, seed=0)

    print(f"Date: {date_str}")
    print("Final behavioral vector:", state.final_behavior_vector.to_dict())
    print("Active modifiers:", state.active_modifiers)


if __name__ == "__main__":
    main()
