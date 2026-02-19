#!/usr/bin/env python3
"""
004 demo: Houses — Placidus, cusps, house per planet, angular strength.

Shows compute_houses(jd, lat, lon), longitude_to_house_number,
angular_strength_for_house (contract: Angular 1,4,7,10=1.0; Succedent=0.6; Cadent=0.3),
assign_houses_and_strength.

Run from project root:
  python scripts/004/02_houses_placidus.py
"""

from __future__ import annotations

from datetime import datetime, timezone

from hnh.astrology import ephemeris as eph
from hnh.astrology import houses as hou


def main() -> None:
    print("=== House cusps (Placidus) ===")
    dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    jd = eph.datetime_to_julian_utc(dt)
    lat, lon = 55.75, 37.62
    cusps, ascmc = hou.compute_houses(jd, lat, lon)
    print(f"  JD: {jd:.4f}, lat={lat}, lon={lon}")
    print(f"  Cusps (1..12): {[round(c, 2) for c in cusps]}")
    print(f"  Ascendant: {ascmc[0]:.2f}°, MC: {ascmc[1]:.2f}°")

    print("\n=== longitude_to_house_number ===")
    for lon_deg, label in [(0.0, "0° Aries"), (120.0, "120° Leo"), (235.0, "235° Scorpio")]:
        h = hou.longitude_to_house_number(lon_deg, cusps)
        print(f"  {label} → house {h}")

    print("\n=== Angular strength (contract) ===")
    for house in (1, 2, 3, 4, 7, 10, 12):
        s = hou.angular_strength_for_house(house)
        print(f"  House {house}: angular_strength = {s}")

    print("\n=== assign_houses_and_strength ===")
    positions = eph.compute_positions(jd)
    with_houses = hou.assign_houses_and_strength(positions, cusps)
    for p in with_houses[:3]:
        print(f"  {p['planet']}: sign={p['sign']}, house={p['house']}, angular_strength={p['angular_strength']}")
    print("  ...")


if __name__ == "__main__":
    main()
