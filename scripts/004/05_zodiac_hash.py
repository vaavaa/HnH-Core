#!/usr/bin/env python3
"""
004 demo: zodiac_summary_hash — xxhash of sign_energy_vector (orjson OPT_SORT_KEYS).

Replay consistency: same sign_energy_vector → same hash. Spec §9.1.

Run from project root:
  python scripts/004/05_zodiac_hash.py
"""

from __future__ import annotations

import orjson
import xxhash

from hnh.astrology import zodiac_expression as ze
from hnh.core import natal
from datetime import datetime, timezone


def zodiac_summary_hash(sign_energy_vector: list[tuple[float, float, float, float]]) -> str:
    """Deterministic hash per Spec 004 §9.1: orjson OPT_SORT_KEYS + xxhash."""
    blob = orjson.dumps(sign_energy_vector, option=orjson.OPT_SORT_KEYS)
    return xxhash.xxh3_128(blob).hexdigest()


def main() -> None:
    print("=== zodiac_summary_hash (Spec 004 §9.1) ===")
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    nat = natal.build_natal_positions(dt, 55.75, 37.62)
    out = ze.compute_zodiac_output(nat["positions"], nat["aspects"])
    vec = out["sign_energy_vector"]

    h1 = zodiac_summary_hash(vec)
    h2 = zodiac_summary_hash(vec)
    print(f"  Hash (xxh3_128): {h1}")
    print(f"  Same vector → same hash: {h1 == h2}")

    print("\n  Hash input: orjson.dumps(sign_energy_vector, option=orjson.OPT_SORT_KEYS)")
    blob = orjson.dumps(vec, option=orjson.OPT_SORT_KEYS)
    print(f"  Bytes length: {len(blob)}")


if __name__ == "__main__":
    main()
