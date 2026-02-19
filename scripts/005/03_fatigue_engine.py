#!/usr/bin/env python3
"""
005: Движок усталости — траектория F(t), q(t) за N дней.

Фиксированные S_T, R, S_g; вывод load, recovery, F, L, q по дням.
Запуск из корня:
  python scripts/005/03_fatigue_engine.py
  python scripts/005/03_fatigue_engine.py --days 60 --stress 0.6
"""

from __future__ import annotations

import argparse

from hnh.lifecycle.fatigue import (
    load,
    recovery,
    fatigue_limit,
    update_fatigue,
    normalized_fatigue,
)
from hnh.lifecycle.constants import DEFAULT_LIFECYCLE_CONSTANTS, C_T_DEFAULT


def main() -> None:
    parser = argparse.ArgumentParser(description="005: Fatigue engine trajectory F(t), q(t)")
    parser.add_argument("--days", type=int, default=30, help="Number of days")
    parser.add_argument("--stress", type=float, default=0.5, help="S_T (0..1) constant per day")
    parser.add_argument("--r", type=float, default=0.5, help="Resilience R")
    parser.add_argument("--s-g", type=float, default=0.5, help="Global sensitivity S_g")
    args = parser.parse_args()

    c = DEFAULT_LIFECYCLE_CONSTANTS
    s_t = max(0.0, min(1.0, args.stress))
    r = max(0.0, min(1.0, args.r))
    s_g = max(0.0, min(1.0, args.s_g))
    L = fatigue_limit(r, s_g, c)
    f = 0.0
    print(f"S_T={s_t:.3f}  R={r:.3f}  S_g={s_g:.3f}  L={L:.2f}")
    print(f"{'day':>4} {'F':>8} {'q':>6} {'load':>7} {'rec':>7}")
    print("-" * 38)
    for day in range(args.days):
        ld = load(s_t, r, s_g, c)
        rec = recovery(s_t, r, c)
        f = update_fatigue(f, ld, rec, c)
        q = normalized_fatigue(f, L)
        print(f"{day:4d} {f:8.4f} {q:6.3f} {ld:7.4f} {rec:7.4f}")


if __name__ == "__main__":
    main()
