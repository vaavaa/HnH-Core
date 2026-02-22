#!/usr/bin/env python3
"""
Calibration for Spec 009 (SC-004): sex-based transit response.
Deterministic synthetic population (fixed seed, N≥10k), 50/50 natals; for each natal run
male and female with sex_transit_mode=scale_delta over a fixed date range; compute per-axis
mean(d_male - d_female), p95, and Cohen's d (same formal criterion as 008).
Exit non-zero if any threshold violated.
Thresholds (documented): |mean_diff| <= 0.01, p95 <= 0.10, Cohen's d <= 0.2.
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import date, timedelta

NUM_AXES = 8
AXIS_SIZE = 4
DEFAULT_SEED = 42
DEFAULT_N = 2000  # Use 10_000+ for full CI
DEFAULT_DAYS = 30


def _axis_mean(vec: list[float], axis: int) -> float:
    start = axis * AXIS_SIZE
    return sum(vec[start : start + AXIS_SIZE]) / AXIS_SIZE


def _synthetic_natals(n: int, seed: int) -> list[dict]:
    """Deterministic synthetic natals (positions only; sex set per run)."""
    rng = __import__("random").Random(seed)
    out = []
    for _ in range(n):
        positions = [
            {"planet": p, "longitude": rng.uniform(0, 360)}
            for p in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
        ]
        out.append({"positions": positions})
    return out


def _axis_delta_over_run(agent, start_date: date, num_days: int) -> list[float]:
    from hnh.lifecycle.engine import aggregate_axis

    axis_0 = list(aggregate_axis(agent.behavior.current_vector))
    for i in range(num_days):
        agent.step(start_date + timedelta(days=i))
    axis_N = aggregate_axis(agent.behavior.current_vector)
    return [axis_N[j] - axis_0[j] for j in range(NUM_AXES)]


def _run_calibration(natals: list[dict], start_date: date, num_days: int):
    from hnh.agent import Agent
    from hnh.config.sex_transit_config import SexTransitConfig

    config_sd = SexTransitConfig(sex_transit_mode="scale_delta")
    deltas_male: list[list[float]] = []
    deltas_female: list[list[float]] = []
    for bd in natals:
        bd_m = {**bd, "sex": "male"}
        bd_f = {**bd, "sex": "female"}
        agent_m = Agent(bd_m, lifecycle=False, sex_transit_config=config_sd)
        agent_f = Agent(bd_f, lifecycle=False, sex_transit_config=config_sd)
        deltas_male.append(_axis_delta_over_run(agent_m, start_date, num_days))
        deltas_female.append(_axis_delta_over_run(agent_f, start_date, num_days))
    return deltas_male, deltas_female


def _cohens_d(male_vals: list[float], female_vals: list[float]) -> float:
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
    parser = argparse.ArgumentParser(description="009 calibration (SC-004): sex transit response")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"RNG seed (default {DEFAULT_SEED})")
    parser.add_argument("--n", type=int, default=DEFAULT_N, help=f"Number of natals (default {DEFAULT_N})")
    parser.add_argument("--date", type=str, default="2020-06-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help=f"Date range length (default {DEFAULT_DAYS})")
    parser.add_argument("--mean-threshold", type=float, default=0.01, help="|mean_diff| <= this")
    parser.add_argument("--p95-threshold", type=float, default=0.10, help="p95 <= this")
    parser.add_argument("--cohen-threshold", type=float, default=0.2, help="|Cohen's d| <= this")
    args = parser.parse_args()

    year, month, day = map(int, args.date.split("-"))
    start_date = date(year, month, day)
    natals = _synthetic_natals(args.n, args.seed)
    deltas_male, deltas_female = _run_calibration(natals, start_date, args.days)

    if not deltas_male or not deltas_female:
        print("ERROR: no results", file=sys.stderr)
        return 2

    failed = False
    for axis in range(NUM_AXES):
        male_axis = [d[axis] for d in deltas_male]
        female_axis = [d[axis] for d in deltas_female]
        mean_m = sum(male_axis) / len(male_axis)
        mean_f = sum(female_axis) / len(female_axis)
        mean_diff = mean_m - mean_f
        diffs = [male_axis[i] - female_axis[i] for i in range(len(male_axis))]
        diffs_sorted = sorted(abs(x) for x in diffs)
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
    print("009 calibration: all SC-004 thresholds passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
