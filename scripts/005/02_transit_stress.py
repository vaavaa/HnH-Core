#!/usr/bin/env python3
"""
005: Transit stress I_T(t), S_T(t) из аспектов (контракт transit-stress).

При наличии астрологии: --date, --lat, --lon для реальных транзитов.
Без опций: демо на фиктивных аспектах (Conjunction, Square).

Запуск из корня:
  python scripts/005/02_transit_stress.py
  python scripts/005/02_transit_stress.py --date 2025-06-15 --lat 51.5 --lon -0.13
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from hnh.lifecycle.stress import compute_raw_transit_intensity, compute_transit_stress
from hnh.lifecycle.constants import C_T_DEFAULT


def _get_aspects_from_transits(date_str: str, lat: float, lon: float) -> list[dict]:
    """Реальные аспекты транзит–натал на дату. Пустой список при ошибке."""
    try:
        from hnh.core.natal import build_natal_positions
        from hnh.astrology.transits import compute_transit_signature
    except ImportError:
        return []
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
        )
        natal = build_natal_positions(dt, lat, lon)
        sig = compute_transit_signature(dt, natal)
        return sig.get("aspects_to_natal", [])
    except Exception:
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description="005: I_T, S_T from aspects (transit-stress contract)")
    parser.add_argument("--date", default="2025-06-15", help="Date YYYY-MM-DD for real transits")
    parser.add_argument("--lat", type=float, default=51.5074, help="Latitude (e.g. London)")
    parser.add_argument("--lon", type=float, default=-0.1278, help="Longitude")
    parser.add_argument("--c-t", type=float, default=C_T_DEFAULT, help="Normalization constant C_T")
    args = parser.parse_args()

    aspects = _get_aspects_from_transits(args.date, args.lat, args.lon)
    if not aspects:
        # Демо: фиктивные жёсткие аспекты
        aspects = [
            {"aspect": "Conjunction", "separation": 2.0, "angle": 0.0},
            {"aspect": "Square", "separation": 91.0, "angle": 90.0},
        ]
        print("(Real transits unavailable; using demo aspects: Conjunction, Square)\n")

    i_t = compute_raw_transit_intensity(aspects)
    _, s_t = compute_transit_stress(aspects, c_t=args.c_t)
    print(f"Date: {args.date}")
    print(f"Aspects (hard only): {len([a for a in aspects if a.get('aspect') in ('Conjunction', 'Opposition', 'Square')])}")
    print(f"I_T = {i_t:.4f}")
    print(f"S_T = {s_t:.4f}  (clip(I_T/C_T, 0, 1), C_T={args.c_t})")


if __name__ == "__main__":
    main()
