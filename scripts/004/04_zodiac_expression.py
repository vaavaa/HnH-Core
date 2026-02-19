#!/usr/bin/env python3
"""
004 demo: Zodiac Expression Layer — sign_energy_vector (12×4), dominant_sign, dominant_element.

Shows compute_zodiac_output(positions, aspects): 12 signs × 4 dimensions
(intensity, stability, expressiveness, adaptability), all in [0, 1].
Read-only; no impact on 32 behavioral parameters.

Run from project root:
  python scripts/004/04_zodiac_expression.py
  python scripts/004/04_zodiac_expression.py --date 2000-01-01
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from hnh.astrology import zodiac_expression as ze
from hnh.core import natal


def main() -> None:
    parser = argparse.ArgumentParser(description="004: zodiac expression 12×4")
    parser.add_argument("--date", default="2000-01-01", help="Date YYYY-MM-DD")
    parser.add_argument("--lat", type=float, default=55.75, help="Latitude")
    parser.add_argument("--lon", type=float, default=37.62, help="Longitude")
    args = parser.parse_args()

    dt = datetime.strptime(args.date, "%Y-%m-%d").replace(
        hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    )
    nat = natal.build_natal_positions(dt, args.lat, args.lon)
    positions = nat["positions"]
    aspects = nat["aspects"]

    print("=== Zodiac Expression (Spec 004) ===")
    print(f"  Input: {len(positions)} planets, {len(aspects)} aspects")
    out = ze.compute_zodiac_output(positions, aspects)

    print("\n  dominant_sign:", out["dominant_sign"], out["dominant_sign_name"])
    print("  dominant_sign_element (элемент знака):", out["dominant_sign_element"])
    print("  dominant_element (по сумме intensity 3 знаков):", out["dominant_element"])

    print("\n  sign_energy_vector (12×4) sample [intensity, stability, expressiveness, adaptability]:")
    for i in (0, 4, 8, 11):
        row = out["sign_energy_vector"][i]
        print(f"    sign {i}: {[round(x, 3) for x in row]}")
    print("  All in [0,1]:", all(0 <= x <= 1 for row in out["sign_energy_vector"] for x in row))


if __name__ == "__main__":
    main()
