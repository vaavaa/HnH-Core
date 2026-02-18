#!/usr/bin/env python3
"""
002 demo: Structured logging v2 (orjson) — build_record_v2, write_record_v2.

Shows required fields (identity_hash, configuration_hash, injected_time_utc,
transit_signature, shock_flag, effective_max_delta_summary, axis_final,
params_final, memory_signature) and optional debug fields.

Run from project root:
  python scripts/002/06_logging_v2.py
  python scripts/002/06_logging_v2.py --out 002_demo.log
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from hnh.config.replay_config import ReplayConfig, compute_configuration_hash
from hnh.identity import IdentityCore
from hnh.identity.schema import NUM_AXES, NUM_PARAMETERS, _registry
from hnh.logging.state_logger_v2 import (
    build_record_v2,
    effective_max_delta_summary,
    validate_record_v2,
    write_record_v2,
)
from hnh.state.replay_v2 import run_step_v2


def main() -> None:
    parser = argparse.ArgumentParser(description="002: one step + v2 log (orjson)")
    parser.add_argument("--date", default="2025-02-18", help="Date YYYY-MM-DD")
    parser.add_argument("--out", default="002_state.log", help="Log file (JSON Lines)")
    args = parser.parse_args()

    dt = datetime.strptime(args.date, "%Y-%m-%d").replace(
        tzinfo=timezone.utc, hour=12, minute=0, second=0, microsecond=0
    )
    config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)
    _registry.discard("script-002-06")
    identity = IdentityCore(
        identity_id="script-002-06",
        base_vector=(0.5,) * NUM_PARAMETERS,
        sensitivity_vector=(0.5,) * NUM_PARAMETERS,
    )
    result = run_step_v2(identity, config, dt, memory_signature="demo-mem")

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
    validate_record_v2(record)

    with open(args.out, "w", encoding="utf-8") as f:
        write_record_v2(record, f)
    print(f"Written one v2 record to {args.out}")
    print("Required fields:", list(record.keys())[:9])


if __name__ == "__main__":
    main()
