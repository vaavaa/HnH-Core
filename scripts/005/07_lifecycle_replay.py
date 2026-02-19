#!/usr/bin/env python3
"""
005: Полный шаг с lifecycle (research + lifecycle_enabled): подпись реплея, проверка детерминизма.

Два прогона с одинаковыми входами -> одинаковые F, W, state. Использует run_step_v2 + run_step_with_lifecycle.
  python scripts/005/07_lifecycle_replay.py
  python scripts/005/07_lifecycle_replay.py --steps 100
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta

from hnh.config.replay_config import ReplayConfig, compute_configuration_hash
from hnh.identity import IdentityCore
from hnh.identity.schema import NUM_PARAMETERS, _registry
from hnh.state.replay_v2 import run_step_v2
from hnh.lifecycle.run import is_lifecycle_active, run_step_with_lifecycle
from hnh.lifecycle.engine import LifecycleStepState, LifecycleState


def main() -> None:
    parser = argparse.ArgumentParser(description="005: Lifecycle replay — determinism check")
    parser.add_argument("--steps", type=int, default=10, help="Number of days to run (2 runs each)")
    args = parser.parse_args()

    config = ReplayConfig(
        global_max_delta=0.15,
        shock_threshold=0.8,
        shock_multiplier=1.5,
        mode="research",
        lifecycle_enabled=True,
        initial_f=0.0,
        initial_w=0.0,
    )
    if not is_lifecycle_active(config):
        print("Config must have mode=research and lifecycle_enabled=True")
        return
    _registry.discard("life-replay-005")
    identity = IdentityCore(
        identity_id="life-replay-005",
        base_vector=(0.5,) * NUM_PARAMETERS,
        sensitivity_vector=(0.5,) * NUM_PARAMETERS,
    )
    memory_delta = (0.0,) * NUM_PARAMETERS
    birth = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    natal = None
    try:
        from hnh.core.natal import build_natal_positions
        natal = build_natal_positions(birth, 51.5, -0.13)
    except Exception:
        pass

    def run_trajectory() -> list[tuple[float, float, str]]:
        trajectory = []
        state = LifecycleStepState(
            F=config.initial_f, W=config.initial_w, state=LifecycleState.ALIVE,
            sum_v=0.0, sum_burn=0.0, count_days=0,
        )
        for day in range(args.steps):
            dt = birth + timedelta(days=day)
            result = run_step_v2(
                identity, config, dt,
                memory_delta=memory_delta, memory_signature="",
                natal_positions=natal,
            )
            aspects = []
            if natal:
                try:
                    from hnh.astrology.transits import compute_transit_signature
                    sig = compute_transit_signature(dt, natal)
                    aspects = sig.get("aspects_to_natal", [])
                except Exception:
                    pass
            chrono_days = float(day)
            next_state, _, _, _ = run_step_with_lifecycle(
                identity, config,
                result.daily_transit_effect,
                memory_delta,
                aspects,
                chrono_days,
                state,
            )
            trajectory.append((next_state.F, next_state.W, next_state.state.value))
            if next_state.state != LifecycleState.ALIVE:
                break
            state = next_state
        return trajectory

    traj1 = run_trajectory()
    traj2 = run_trajectory()
    match = len(traj1) == len(traj2) and all(
        abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9 and a[2] == b[2]
        for a, b in zip(traj1, traj2)
    )
    print(f"configuration_hash: {compute_configuration_hash(config)[:24]}...")
    print(f"Run 1 length: {len(traj1)}, Run 2 length: {len(traj2)}")
    print(f"Determinism: {'PASS' if match else 'FAIL'}")
    if traj1:
        print(f"Last step (F, W, state): {traj1[-1]}")


if __name__ == "__main__":
    main()
