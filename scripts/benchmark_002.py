#!/usr/bin/env python3
"""
Phase 9 benchmarks: orjson vs json (T9.1), daily state computation (T9.2).
Run from repo root with venv active: python scripts/benchmark_002.py
"""

from __future__ import annotations

import json
import timeit
from datetime import datetime, timezone

# T9.1: orjson vs json
try:
    import orjson
except ImportError:
    orjson = None  # type: ignore[assignment]


def bench_serialization(record: dict, n: int = 50_000) -> None:
    """T9.1: Compare orjson vs stdlib json for log-record serialization."""
    blob_json = json.dumps(record, sort_keys=True)
    t_json = timeit.timeit(lambda: json.dumps(record, sort_keys=True), number=n)
    print(f"  json.dumps:  {t_json:.3f}s for {n} calls ({n/t_json:.0f} calls/s)")
    if orjson is not None:
        t_orjson = timeit.timeit(lambda: orjson.dumps(record, option=orjson.OPT_SORT_KEYS), number=n)
        print(f"  orjson.dumps: {t_orjson:.3f}s for {n} calls ({n/t_orjson:.0f} calls/s)")
        print(f"  orjson vs json: {t_json/t_orjson:.1f}x faster")
    else:
        print("  orjson not installed, skip orjson.dumps")


def bench_daily_state(n: int = 5_000) -> None:
    """T9.2: Time run_step_v2 (one daily state computation)."""
    from hnh.config.replay_config import ReplayConfig
    from hnh.identity.schema import IdentityCore, NUM_PARAMETERS, _registry
    from hnh.state.replay_v2 import run_step_v2

    _registry.discard("bench-id")
    identity = IdentityCore(
        identity_id="bench-id",
        base_vector=(0.5,) * NUM_PARAMETERS,
        sensitivity_vector=(0.5,) * NUM_PARAMETERS,
    )
    config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)
    t = datetime(2025, 2, 18, 12, 0, 0, tzinfo=timezone.utc)
    mem = (0.0,) * NUM_PARAMETERS

    def one_step() -> None:
        run_step_v2(identity, config, t, memory_delta=mem, memory_signature="m")

    elapsed = timeit.timeit(one_step, number=n)
    print(f"  run_step_v2: {elapsed:.3f}s for {n} steps ({n/elapsed:.0f} steps/s)")
    _registry.discard("bench-id")


def main() -> None:
    print("=== T9.1 Serialization (orjson vs json) ===")
    # Record similar to state_logger_v2 build_record_v2 output
    record = {
        "identity_hash": "a" * 64,
        "configuration_hash": "b" * 64,
        "injected_time_utc": "2025-02-18T12:00:00+00:00",
        "transit_signature": "c" * 64,
        "shock_flag": False,
        "effective_max_delta_summary": [0.15] * 8,
        "axis_final": [0.5] * 8,
        "params_final": [0.5] * 32,
        "memory_signature": "d" * 64,
    }
    bench_serialization(record)

    print("\n=== T9.2 Daily state computation ===")
    bench_daily_state()

    print("\nDone.")


if __name__ == "__main__":
    main()
