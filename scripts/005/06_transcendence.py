#!/usr/bin/env python3
"""
005: Порог W >= 0.995, state TRANSCENDED, заморозка профиля.

Демо: задаём W(0) >= 0.995 и показываем, что первый же шаг даёт TRANSCENDED и снапшот.
  python scripts/005/06_transcendence.py
"""

from __future__ import annotations

from hnh.identity.schema import NUM_PARAMETERS
from hnh.lifecycle.engine import (
    LifecycleState,
    LifecycleStepState,
    lifecycle_step,
    check_init_death_or_transcendence,
)
from hnh.lifecycle.fatigue import fatigue_limit
from hnh.lifecycle.constants import DEFAULT_LIFECYCLE_CONSTANTS, W_TRANSCEND


def main() -> None:
    base = (0.5,) * NUM_PARAMETERS
    sens = (0.5,) * NUM_PARAMETERS
    daily = (0.01,) * NUM_PARAMETERS
    mem = (0.0,) * NUM_PARAMETERS
    r, s_g = 0.5, 0.5
    c = DEFAULT_LIFECYCLE_CONSTANTS
    L = fatigue_limit(r, s_g, c)

    # Edge case: W(0) >= 0.995 -> transcendence before first step
    state = LifecycleStepState(
        F=0.0, W=0.996, state=LifecycleState.ALIVE,
        sum_v=0.0, sum_burn=0.0, count_days=0,
    )
    next_state, params_final, axis_final, snap = lifecycle_step(
        base, sens, daily, mem, s_t=0.2, r=r, s_g=s_g, chrono_age_days=0.0, state=state, c=c
    )
    print("W(0) = 0.996 (>= 0.995) -> Transcendence")
    print(f"  state: {next_state.state.value}")
    if snap:
        print(f"  snapshot state: {snap.state}")
        print(f"  params_final (first 4): {params_final[:4]}")
    print("\ncheck_init_death_or_transcendence(F=0, W=0.996, L, 0.995):", check_init_death_or_transcendence(0.0, 0.996, L, W_TRANSCEND))


if __name__ == "__main__":
    main()
