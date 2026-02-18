#!/usr/bin/env python3
"""
002 demo: Raw delta from aspects, ReplayConfig, apply_bounds (hierarchy + shock).

Shows compute_raw_delta_32, ReplayConfig (global_max_delta, shock_threshold,
shock_multiplier), and apply_bounds → bounded_delta, effective_max_delta.

Run from project root:
  python scripts/002/03_raw_delta_and_bounds.py
"""

from __future__ import annotations

from hnh.config.replay_config import ReplayConfig
from hnh.identity.schema import NUM_PARAMETERS
from hnh.modulation import apply_bounds, compute_raw_delta_32


def main() -> None:
    print("=== Raw delta from aspects ===")
    aspects = [
        {"aspect": "Trine", "angle": 120.0, "separation": 119.0},
        {"aspect": "Square", "angle": 90.0, "separation": 91.0},
    ]
    raw = compute_raw_delta_32(aspects)
    print(f"  raw_delta length: {len(raw)}")
    non_zero = [i for i, v in enumerate(raw) if v != 0.0]
    print(f"  Non-zero indices (sample): {non_zero[:8]}...")
    print(f"  Max |raw|: {max(abs(v) for v in raw):.4f}")

    print("\n=== ReplayConfig (hierarchy: parameter > axis > global) ===")
    config = ReplayConfig(
        global_max_delta=0.15,
        shock_threshold=0.8,
        shock_multiplier=1.5,
    )
    print(f"  global_max_delta: {config.global_max_delta}")
    print(f"  shock_threshold: {config.shock_threshold}")
    print(f"  shock_multiplier: {config.shock_multiplier}")

    print("\n=== apply_bounds (no shock) ===")
    bounded, effective = apply_bounds(raw, config, shock_active=False)
    print(f"  bounded_delta: max |bounded| = {max(abs(b) for b in bounded):.4f}")
    print(f"  effective_max_delta (per param): first 4 = {effective[:4]}")

    print("\n=== apply_bounds (shock active) ===")
    bounded_shock, effective_shock = apply_bounds(raw, config, shock_active=True)
    print(f"  effective_max_delta with shock: first 4 = {effective_shock[:4]}")


if __name__ == "__main__":
    main()
