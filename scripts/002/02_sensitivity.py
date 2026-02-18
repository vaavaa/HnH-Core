#!/usr/bin/env python3
"""
002 demo: Natal-derived sensitivity (compute_sensitivity, sensitivity_histogram).

Shows how a natal_data dict (positions + optional aspects) yields
a 32-dim sensitivity vector in [0, 1] and debug histogram.

Run from project root:
  python scripts/002/02_sensitivity.py
"""

from __future__ import annotations

from hnh.identity import compute_sensitivity, sensitivity_histogram
from hnh.identity.schema import NUM_PARAMETERS


def main() -> None:
    print("=== Empty natal (no positions, no aspects) ===")
    natal_empty = {"positions": [], "aspects": []}
    vec_empty = compute_sensitivity(natal_empty)
    print(f"  Sensitivity length: {len(vec_empty)}")
    print(f"  All in [0,1]: {all(0 <= v <= 1 for v in vec_empty)}")
    print(f"  Sample (first 5): {vec_empty[:5]}")

    print("\n=== Natal with Moon and Saturn ===")
    natal = {
        "positions": [
            {"planet": "Moon", "longitude": 45.0},
            {"planet": "Saturn", "longitude": 120.0},
        ],
        "aspects": [],
    }
    vec = compute_sensitivity(natal)
    print(f"  Sensitivity length: {len(vec)}")
    print(f"  Min: {min(vec):.4f}, Max: {max(vec):.4f}")

    print("\n=== Debug: sensitivity_histogram ===")
    hist = sensitivity_histogram(vec)
    print(f"  histogram: {hist['histogram']}")
    print(f"  low_sensitivity_pct: {hist['low_sensitivity_pct']}%")
    print(f"  high_sensitivity_pct: {hist['high_sensitivity_pct']}%")


if __name__ == "__main__":
    main()
