"""
CLI: simulate agent for specific date; print behavioral vector and modifiers; replay mode.
No datetime.now() in core — time is always injected from CLI args.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from hnh.core.identity import IdentityCore
from hnh.core.parameters import BehavioralVector
from hnh.state.replay import run_step


def _default_identity() -> IdentityCore:
    """Default identity for CLI demo (fixed base vector)."""
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.4,
        verbosity=0.6,
        correction_rate=0.3,
        humor_level=0.5,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    return IdentityCore(
        identity_id="cli-default",
        base_traits=base,
        symbolic_input=None,
    )


def _parse_date(s: str) -> datetime:
    """Parse YYYY-MM-DD to UTC noon."""
    dt = datetime.strptime(s, "%Y-%m-%d")
    return dt.replace(tzinfo=timezone.utc, hour=12, minute=0, second=0, microsecond=0)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="HnH deterministic personality engine — simulate for a specific date.",
    )
    parser.add_argument(
        "--date",
        type=str,
        required=True,
        metavar="YYYY-MM-DD",
        help="Date for simulation (injected time, no system clock).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Deterministic seed (default: 0).",
    )
    parser.add_argument(
        "--replay",
        action="store_true",
        help="Run twice and verify identical output (replay validation).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output state as single JSON line.",
    )
    args = parser.parse_args()

    try:
        injected = _parse_date(args.date)
    except ValueError as e:
        print(f"Invalid --date: {e}. Use YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)
        return  # unreachable when sys.exit runs; helps when exit is mocked

    identity = _default_identity()
    state = run_step(identity, injected, seed=args.seed, relational_snapshot=None)

    if args.replay:
        state2 = run_step(identity, injected, seed=args.seed, relational_snapshot=None)
        if state.final_behavior_vector.to_dict() != state2.final_behavior_vector.to_dict():
            print("Replay mismatch: outputs differ.", file=sys.stderr)
            sys.exit(1)
        if not args.json:
            print("Replay OK: identical output.")

    if args.json:
        out = {
            "identity_hash": state.identity_hash,
            "injected_time": state.injected_time,
            "final_behavioral_vector": state.final_behavior_vector.to_dict(),
            "active_modifiers": state.active_modifiers,
        }
        print(json.dumps(out, sort_keys=True))
    else:
        print("final_behavioral_vector:", state.final_behavior_vector.to_dict())
        print("active_modifiers:", state.active_modifiers)


if __name__ == "__main__":
    main()
