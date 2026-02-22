#!/usr/bin/env python3
"""
Calibration sanity check for Spec 008 (SC-004).
Deterministic synthetic population (fixed seed), 50/50 sex; per-axis mean diff, p95, Cohen's d.
Exit non-zero if any threshold violated.
Thresholds (documented): |mean_diff| <= 0.01, p95 <= 0.10, Cohen's d <= 0.2.
"""

from __future__ import annotations

import argparse
import sys

# Fixed seed for reproducibility (documented)
DEFAULT_SEED = 42
DEFAULT_N = 2000  # Use 10_000 for full CI if desired
NUM_AXES = 8
AXIS_SIZE = 4


def _axis_mean(vec: list[float], axis: int) -> float:
    """Axis k = mean of params[4k : 4k+4]."""
    start = axis * AXIS_SIZE
    return sum(vec[start : start + AXIS_SIZE]) / AXIS_SIZE


def _synthetic_birth_data_list(n: int, seed: int) -> list[dict]:
    """Deterministic synthetic natals: positions with planet longitudes from seed."""
    rng = __import__("random").Random(seed)
    planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
    out = []
    for _ in range(n):
        positions = [{"planet": p, "longitude": rng.uniform(0, 360)} for p in planets]
        sex = "male" if rng.random() < 0.5 else "female"
        out.append({"positions": positions, "sex": sex})
    return out


def _run_calibration(birth_data_list: list[dict], step_date) -> tuple[list[list[float]], list[list[float]]]:
    from hnh.agent import Agent

    vectors_male: list[list[float]] = []
    vectors_female: list[list[float]] = []
    for bd in birth_data_list:
        agent = Agent(bd, lifecycle=False)
        agent.step(step_date)
        vec = list(agent.behavior.current_vector)
        if bd.get("sex") == "male":
            vectors_male.append(vec)
        else:
            vectors_female.append(vec)
    return vectors_male, vectors_female


def _cohens_d(male_vals: list[float], female_vals: list[float]) -> float:
    import math
    n1, n2 = len(male_vals), len(female_vals)
    if n1 < 2 or n2 < 2:
        return 0.0
    m1 = sum(male_vals) / n1
    m2 = sum(female_vals) / n2
    v1 = sum((x - m1) ** 2 for x in male_vals) / (n1 - 1) if n1 > 1 else 0.0
    v2 = sum((x - m2) ** 2 for x in female_vals) / (n2 - 1) if n2 > 1 else 0.0
    pooled = ((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2) if (n1 + n2 > 2) else 0.0
    if pooled <= 0:
        return 0.0
    return (m1 - m2) / math.sqrt(pooled)


def main() -> int:
    from datetime import date

    parser = argparse.ArgumentParser(description="008 calibration sanity check (SC-004)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"RNG seed (default {DEFAULT_SEED})")
    parser.add_argument("--n", type=int, default=DEFAULT_N, help=f"Population size (default {DEFAULT_N})")
    parser.add_argument("--date", type=str, default="2020-06-15", help="Step date (YYYY-MM-DD)")
    parser.add_argument("--mean-threshold", type=float, default=0.01, help="|mean_diff| <= this")
    parser.add_argument("--p95-threshold", type=float, default=0.10, help="p95 <= this")
    parser.add_argument("--cohen-threshold", type=float, default=0.2, help="|Cohen's d| <= this")
    args = parser.parse_args()

    year, month, day = map(int, args.date.split("-"))
    step_date = date(year, month, day)
    birth_data_list = _synthetic_birth_data_list(args.n, args.seed)
    vectors_male, vectors_female = _run_calibration(birth_data_list, step_date)

    if not vectors_male or not vectors_female:
        print("ERROR: need both male and female agents", file=sys.stderr)
        return 2

    failed = False
    for axis in range(NUM_AXES):
        male_axis = [_axis_mean(v, axis) for v in vectors_male]
        female_axis = [_axis_mean(v, axis) for v in vectors_female]
        mean_m = sum(male_axis) / len(male_axis)
        mean_f = sum(female_axis) / len(female_axis)
        mean_diff = mean_m - mean_f
        combined = [m - mean_f for m in male_axis] + [f - mean_m for f in female_axis]
        diffs_sorted = sorted(abs(x) for x in combined) if combined else [0.0]
        p95 = diffs_sorted[int(0.95 * len(diffs_sorted))] if diffs_sorted else 0.0
        cohen = _cohens_d(male_axis, female_axis)

        if abs(mean_diff) > args.mean_threshold:
            print(f"Axis {axis}: |mean_diff|={abs(mean_diff):.4f} > {args.mean_threshold}")
            failed = True
        if p95 > args.p95_threshold:
            print(f"Axis {axis}: p95={p95:.4f} > {args.p95_threshold}")
            failed = True
        if abs(cohen) > args.cohen_threshold:
            print(f"Axis {axis}: |Cohen's d|={abs(cohen):.4f} > {args.cohen_threshold}")
            failed = True

    if failed:
        return 1
    print("Calibration sanity: all thresholds passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
