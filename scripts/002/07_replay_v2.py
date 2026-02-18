#!/usr/bin/env python3
"""
002 demo: Replay v2 — run_step_v2 N times, replay_match (tolerance 1e-9), replay_output_hash.

Shows deterministic replay: same identity, config, time, memory → identical
params_final and axis_final; replay_match and replay_output_hash for validation.

Run from project root:
  python scripts/002/07_replay_v2.py
"""

from __future__ import annotations

from datetime import datetime, timezone

from hnh.config.replay_config import ReplayConfig
from hnh.identity import IdentityCore
from hnh.identity.schema import NUM_PARAMETERS, _registry
from hnh.state.replay_v2 import replay_match, replay_output_hash, run_step_v2


def main() -> None:
    _registry.discard("script-002-07")
    identity = IdentityCore(
        identity_id="script-002-07",
        base_vector=(0.5,) * NUM_PARAMETERS,
        sensitivity_vector=(0.5,) * NUM_PARAMETERS,
    )
    config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)
    dt = datetime(2025, 2, 18, 12, 0, 0, tzinfo=timezone.utc)
    mem = (0.0,) * NUM_PARAMETERS

    print("=== Run run_step_v2 five times (same inputs) ===")
    results = []
    for i in range(5):
        r = run_step_v2(identity, config, dt, memory_delta=mem, memory_signature="m7")
        results.append(r)
        h = replay_output_hash(r.params_final, r.axis_final)
        print(f"  Run {i+1}: output hash = {h[:16]}...")

    hashes = [replay_output_hash(r.params_final, r.axis_final) for r in results]
    print(f"\n  All hashes identical: {len(set(hashes)) == 1}")

    print("\n=== replay_match (tolerance 1e-9) ===")
    ok = replay_match(
        results[0].params_final,
        results[0].axis_final,
        results[1].params_final,
        results[1].axis_final,
    )
    print(f"  Run 1 vs Run 2 match: {ok}")


if __name__ == "__main__":
    main()
