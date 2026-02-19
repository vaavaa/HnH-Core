#!/usr/bin/env python3
"""
004 demo: Natal — 10 planets + houses (sign, house, angular_strength).

Shows build_natal_positions with birth datetime and location:
positions with planet, longitude, sign (0–11), house (1–12), angular_strength,
plus houses (cusps, ascendant, mc). Deterministic.

Run from project root:
  python scripts/004/03_natal_10_planets_houses.py
  python scripts/004/03_natal_10_planets_houses.py --date 1990-06-15 --lat 52.52 --lon 13.40
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from hnh.core import natal


def main() -> None:
    parser = argparse.ArgumentParser(description="004: natal with 10 planets and houses")
    parser.add_argument("--date", default="2000-01-01", help="Birth date YYYY-MM-DD")
    parser.add_argument("--lat", type=float, default=55.75, help="Latitude")
    parser.add_argument("--lon", type=float, default=37.62, help="Longitude")
    args = parser.parse_args()

    dt = datetime.strptime(args.date, "%Y-%m-%d").replace(
        hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    )

    print("=== build_natal_positions (Spec 004) ===")
    print(f"  Birth: {dt.isoformat()}, lat={args.lat}, lon={args.lon}")
    out = natal.build_natal_positions(dt, args.lat, args.lon)

    print(f"\n  positions: {len(out['positions'])} planets")
    for p in out["positions"][:4]:
        print(f"    {p['planet']}: long={p['longitude']:.2f} sign={p['sign']} house={p['house']} angular_strength={p['angular_strength']}")
    print("    ...")

    print(f"\n  aspects: {len(out['aspects'])} aspects")
    if out["aspects"]:
        for a in out["aspects"][:3]:
            print(f"    {a['planet1']}–{a['planet2']} {a['aspect']}")

    print("\n  houses:")
    print(f"    cusps: 12 values")
    print(f"    ascendant: {out['houses']['ascendant']:.2f}°")
    print(f"    mc: {out['houses']['mc']:.2f}°")


if __name__ == "__main__":
    main()
