#!/usr/bin/env python3
"""
004 demo: Ephemeris — 10 planets (Sun..Pluto), compute_positions.

Shows PLANETS_NATAL (10 planets), datetime_to_julian_utc, compute_positions.
Deterministic: same JD → same longitudes.

Run from project root:
  python scripts/004/01_ephemeris_10_planets.py
"""

from __future__ import annotations

from datetime import datetime, timezone

from hnh.astrology import ephemeris as eph


def main() -> None:
    print("=== 10 planets (Spec 004) ===")
    for i, (name, pid) in enumerate(eph.PLANETS_NATAL):
        print(f"  {i}: {name} (Swiss Ephemeris ID {pid})")

    print("\n=== compute_positions(jd_ut) ===")
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    jd = eph.datetime_to_julian_utc(dt)
    positions = eph.compute_positions(jd)
    print(f"  JD(UT): {jd:.4f}")
    print(f"  Count: {len(positions)}")
    for p in positions[:4]:
        print(f"    {p['planet']}: longitude {p['longitude']:.2f}°")
    print("    ...")
    for p in positions[-2:]:
        print(f"    {p['planet']}: longitude {p['longitude']:.2f}°")

    print("\n=== Determinism ===")
    positions2 = eph.compute_positions(jd)
    same = all(
        positions[i]["planet"] == positions2[i]["planet"]
        and abs(positions[i]["longitude"] - positions2[i]["longitude"]) < 1e-9
        for i in range(len(positions))
    )
    print(f"  Same JD → same positions: {same}")


if __name__ == "__main__":
    main()
