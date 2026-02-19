#!/usr/bin/env python3
"""
004 demo: Full pipeline — natal (10 planets + houses) → zodiac expression → zodiac_summary_hash.

One date, one location: build_natal_positions → compute_zodiac_output → zodiac_summary_hash.
Optional: write zodiac fields to a JSON line (orjson).

Run from project root:
  python scripts/004/06_full_zodiac_pipeline.py
  python scripts/004/06_full_zodiac_pipeline.py --date 1990-06-15 --out 004_zodiac_demo.log
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

import orjson
import xxhash

from hnh.astrology import zodiac_expression as ze
from hnh.core import natal


def zodiac_summary_hash(sign_energy_vector: list[tuple[float, float, float, float]]) -> str:
    """Deterministic hash per Spec 004 §9.1."""
    blob = orjson.dumps(sign_energy_vector, option=orjson.OPT_SORT_KEYS)
    return xxhash.xxh3_128(blob).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="004: full zodiac pipeline")
    parser.add_argument("--date", default="2000-01-01", help="Date YYYY-MM-DD")
    parser.add_argument("--lat", type=float, default=55.75, help="Latitude")
    parser.add_argument("--lon", type=float, default=37.62, help="Longitude")
    parser.add_argument("--out", default="", help="If set, write one JSON line with zodiac fields")
    args = parser.parse_args()

    dt = datetime.strptime(args.date, "%Y-%m-%d").replace(
        hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    )

    print("=== Full pipeline (Spec 004) ===")
    print("  1. build_natal_positions (10 planets + houses)")
    nat = natal.build_natal_positions(dt, args.lat, args.lon)
    print(f"     → {len(nat['positions'])} positions, {len(nat['aspects'])} aspects")

    print("  2. compute_zodiac_output")
    out = ze.compute_zodiac_output(nat["positions"], nat["aspects"])
    print(f"     → dominant_sign={out['dominant_sign']} ({out['dominant_sign_name']}), dominant_element={out['dominant_element']}")

    print("  3. zodiac_summary_hash")
    h = zodiac_summary_hash(out["sign_energy_vector"])
    print(f"     → {h[:24]}...")

    if args.out:
        record = {
            "injected_time_utc": dt.isoformat(),
            "latitude": args.lat,
            "longitude": args.lon,
            "dominant_sign": out["dominant_sign"],
            "dominant_sign_name": out["dominant_sign_name"],
            "dominant_element": out["dominant_element"],
            "zodiac_summary_hash": h,
        }
        line = orjson.dumps(record, option=orjson.OPT_SORT_KEYS).decode("utf-8")
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(line + "\n")
        print(f"\n  Written one record to {args.out}")


if __name__ == "__main__":
    main()
