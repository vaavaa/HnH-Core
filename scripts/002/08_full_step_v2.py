#!/usr/bin/env python3
"""
002 demo: Full step v2 — IdentityCore + ReplayConfig + time + optional memory → ReplayResult.

One-shot pipeline: run_step_v2 returns params_final (32), axis_final (8),
identity_hash, configuration_hash, transit_signature, shock_flag, memory_signature.
Optionally write v2 log record.

Run from project root:
  python scripts/002/08_full_step_v2.py
  python scripts/002/08_full_step_v2.py --date 2025-03-01
  python scripts/002/08_full_step_v2.py --date 2025-03-01 --log
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from hnh.config.replay_config import ReplayConfig
from hnh.identity import IdentityCore
from hnh.identity.schema import AXES, NUM_PARAMETERS, _registry
from hnh.memory.relational import RelationalMemory
from hnh.state.replay_v2 import run_step_v2


def main() -> None:
    parser = argparse.ArgumentParser(description="002: full step v2 (identity + config + time + memory)")
    parser.add_argument("--date", default="2025-02-18", help="Date YYYY-MM-DD")
    parser.add_argument("--log", action="store_true", help="Write one v2 log record to 002_full.log")
    args = parser.parse_args()

    dt = datetime.strptime(args.date, "%Y-%m-%d").replace(
        tzinfo=timezone.utc, hour=12, minute=0, second=0, microsecond=0
    )
    config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)

    _registry.discard("script-002-08")
    identity = IdentityCore(
        identity_id="script-002-08",
        base_vector=(0.5,) * NUM_PARAMETERS,
        sensitivity_vector=(0.5,) * NUM_PARAMETERS,
    )

    memory = RelationalMemory("user-full")
    memory.add_event(1, "interaction")
    memory_delta = memory.get_memory_delta_32(config.global_max_delta)
    mem_sig = memory.memory_signature()

    result = run_step_v2(
        identity,
        config,
        dt,
        memory_delta=memory_delta,
        memory_signature=mem_sig,
    )

    print("=== Full step v2 result ===")
    print(f"  Date: {args.date}")
    print(f"  identity_hash: {result.identity_hash[:20]}...")
    print(f"  configuration_hash: {result.configuration_hash[:20]}...")
    print(f"  shock_flag: {result.shock_flag}")
    print(f"  params_final (32): first 8 = {result.params_final[:8]}")
    print(f"  axis_final (8):")
    for i, (ax, val) in enumerate(zip(AXES, result.axis_final)):
        print(f"    {ax}: {val:.4f}")

    if args.log:
        from hnh.logging.state_logger_v2 import (
            build_record_v2,
            effective_max_delta_summary,
            write_record_v2,
        )
        summary_8 = effective_max_delta_summary(result.effective_max_delta)
        record = build_record_v2(
            identity_hash=result.identity_hash,
            configuration_hash=result.configuration_hash,
            injected_time_utc=result.injected_time_utc,
            transit_signature=result.transit_signature,
            shock_flag=result.shock_flag,
            effective_max_delta_summary_8=summary_8,
            axis_final=result.axis_final,
            params_final=result.params_final,
            memory_signature=result.memory_signature,
        )
        with open("002_full.log", "w", encoding="utf-8") as f:
            write_record_v2(record, f)
        print("\n  Written 002_full.log")


if __name__ == "__main__":
    main()
