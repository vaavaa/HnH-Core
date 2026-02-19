#!/usr/bin/env python3
"""
005: A_g(q), effective_transit_delta, effective_memory_delta, деградация 6 параметров.

Показывает кривую A_g при разных q и применение подавления к дельтам и параметрам.
  python scripts/005/04_activity_suppression.py
  python scripts/005/04_activity_suppression.py --q 0.5
"""

from __future__ import annotations

import argparse

from hnh.identity.schema import NUM_PARAMETERS, PARAMETERS
from hnh.lifecycle.engine import (
    activity_factor,
    apply_behavioral_degradation,
    ACTIVITY_SENSITIVE_INDICES,
)
from hnh.lifecycle.constants import DEFAULT_LIFECYCLE_CONSTANTS


def main() -> None:
    parser = argparse.ArgumentParser(description="005: Activity suppression A_g, effective deltas, degradation")
    parser.add_argument("--q", type=float, default=None, help="Single q to show A_g and degradation")
    args = parser.parse_args()

    c = DEFAULT_LIFECYCLE_CONSTANTS
    if args.q is not None:
        q = max(0.0, min(1.0, args.q))
        a_g = activity_factor(q, c)
        print(f"q = {q:.3f}  ->  A_g = {a_g:.3f}")
        params = (0.5,) * NUM_PARAMETERS
        degraded = apply_behavioral_degradation(params, a_g, c)
        print("Activity-sensitive params after degradation (cap 0.1):")
        for p_ix in ACTIVITY_SENSITIVE_INDICES:
            name = PARAMETERS[p_ix]
            diff = params[p_ix] - degraded[p_ix]
            print(f"  {name}: {params[p_ix]:.3f} -> {degraded[p_ix]:.3f} (delta {diff:+.3f})")
        return

    print("A_g(q) curve: q in [0, 0.2, 0.4, 0.6, 0.8, 1.0]")
    print(f"{'q':>6} {'A_g':>6}")
    print("-" * 14)
    for q in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        a_g = activity_factor(q, c)
        print(f"{q:6.2f} {a_g:6.3f}")
    print("\neffective_transit_delta = A_g × (sensitivity × transit_delta)")
    print("effective_memory_delta  = A_g × memory_delta")
    print("Degradation: for 6 params (initiative, curiosity, persistence, pacing, challenge_level, verbosity)")
    print("  x_p -= delta_p*(1-A_g), clamp [0,1], cap 0.1 absolute reduction.")


if __name__ == "__main__":
    main()
