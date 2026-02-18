#!/usr/bin/env python3
"""
Example: one step → write to log (JSON Lines) → replay run → check match.

Shows how to write structured transition log and how to verify
that replay produces the same result.

Run from project root:
  python scripts/02_replay_and_log.py
  python scripts/02_replay_and_log.py --out state.log
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from hnh.core.identity import IdentityCore
from hnh.core.parameters import BehavioralVector
from hnh.logging.state_logger import build_record, write_record
from hnh.state.replay import run_step


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulation step + log + replay check")
    parser.add_argument("--date", default="2024-07-01", help="Date YYYY-MM-DD")
    parser.add_argument("--out", default="state.log", help="Output file for log (JSON Lines)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dt = datetime.strptime(args.date, "%Y-%m-%d").replace(
        tzinfo=timezone.utc, hour=12, minute=0, second=0, microsecond=0
    )

    base = BehavioralVector(
        warmth=0.5, strictness=0.4, verbosity=0.6, correction_rate=0.3,
        humor_level=0.5, challenge_intensity=0.4, pacing=0.5,
    )
    identity = IdentityCore(
        identity_id="script-02-replay",
        base_traits=base,
        symbolic_input=None,
    )

    # First run and write to log
    state1 = run_step(identity, dt, seed=args.seed)
    with open(args.out, "w", encoding="utf-8") as f:
        write_record(state1, f)
    print(f"Written one transition to {args.out}")

    # Replay: second run with same inputs
    state2 = run_step(identity, dt, seed=args.seed)
    if state1.final_behavior_vector.to_dict() != state2.final_behavior_vector.to_dict():
        print("Error: replay produced a different result.", file=sys.stderr)
        sys.exit(1)
    print("Replay OK: result matches first run.")

    record = build_record(state1)
    print("Log record fields:", list(record.keys()))


if __name__ == "__main__":
    main()
