#!/usr/bin/env python3
"""
005: Условие смерти F >= L, финальный снапшот, delta_W и обновление W при смерти.

Запускаем шаги до F >= L (подбираем высокий S_T или много дней), выводим снапшот и W.
  python scripts/005/05_death_and_will.py
  python scripts/005/05_death_and_will.py --stress 0.95 --days 5000
"""

from __future__ import annotations

import argparse

from hnh.identity.schema import NUM_PARAMETERS
from hnh.lifecycle.engine import (
    LifecycleState,
    LifecycleStepState,
    lifecycle_step,
)
from hnh.lifecycle.fatigue import (
    load,
    recovery,
    fatigue_limit,
    update_fatigue,
    normalized_fatigue,
)
from hnh.lifecycle.constants import DEFAULT_LIFECYCLE_CONSTANTS


def main() -> None:
    parser = argparse.ArgumentParser(description="005: Death condition, snapshot, delta_W at death")
    parser.add_argument("--stress", type=float, default=0.9, help="S_T constant (high to reach death)")
    parser.add_argument("--days", type=int, default=3000, help="Max days to run")
    parser.add_argument("--r", type=float, default=0.3, help="Resilience (lower = lower L)")
    parser.add_argument("--s-g", type=float, default=0.6, help="S_g")
    args = parser.parse_args()

    c = DEFAULT_LIFECYCLE_CONSTANTS
    s_t = max(0.0, min(1.0, args.stress))
    r = max(0.0, min(1.0, args.r))
    s_g = max(0.0, min(1.0, args.s_g))
    L = fatigue_limit(r, s_g, c)
    base = (0.5,) * NUM_PARAMETERS
    sens = (0.5,) * NUM_PARAMETERS
    daily = (0.01,) * NUM_PARAMETERS
    mem = (0.0,) * NUM_PARAMETERS
    state = LifecycleStepState(F=0.0, W=0.0, state=LifecycleState.ALIVE, sum_v=0.0, sum_burn=0.0, count_days=0)

    for day in range(args.days):
        next_state, params_final, axis_final, snap = lifecycle_step(
            base, sens, daily, mem, s_t=s_t, r=r, s_g=s_g, chrono_age_days=float(day), state=state, c=c
        )
        if snap is not None:
            print(f"Death/Transcendence at day {day}")
            print(f"  state: {snap.state}")
            print(f"  F={snap.F:.4f}  L={snap.L:.4f}  q={snap.q:.4f}")
            print(f"  W before->after: {state.W:.4f} -> {next_state.W:.4f}")
            print(f"  sum_v={snap.sum_v:.4f}  sum_burn={snap.sum_burn:.4f}  count_days={snap.count_days}")
            if snap.Age_psy is not None:
                print(f"  Age_psy (years): {snap.Age_psy:.2f}")
            return
        state = next_state
    print(f"No death in {args.days} days (F={state.F:.4f}, L={L:.4f}). Try --stress 0.95 or --days 5000.")


if __name__ == "__main__":
    main()
