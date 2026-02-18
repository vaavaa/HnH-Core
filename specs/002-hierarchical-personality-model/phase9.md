# Phase 9 — Performance & Coverage

## T9.1 Benchmark Serialization

Run from repo root with venv active:

```bash
python scripts/benchmark_002.py
```

The script compares **orjson** vs stdlib **json** for serializing a log-record-sized dict (50k iterations). orjson is typically several times faster.

## T9.2 Benchmark Daily State Computation

Same script: section "T9.2 Daily state computation" times `run_step_v2` (e.g. 5000 steps). No natal/transit in this run (memory_delta only).

## T9.3 Coverage Gate (99%+ core modules)

Core modules for 002: `hnh.identity`, `hnh.config`, `hnh.modulation`, `hnh.memory`, `hnh.state` (assembler, replay_v2), `hnh.logging.state_logger_v2`.

To run coverage restricted to 002 core and enforce 99%:

```bash
pytest tests/unit --cov=hnh --cov-report=term-missing \
  --cov-omit="hnh/cli.py,hnh/interface/*,hnh/logging/state_logger.py,hnh/logging/contracts.py,hnh/astrology/*,hnh/core/*,hnh/state/dynamic_state.py,hnh/state/modulation.py,hnh/state/replay.py" \
  --cov-fail-under=99
```

Current gate in pyproject.toml: **fail_under = 99** for 002 core (omit list). Achieved with tests for sensitivity (Saturn/Uranus modalities, aspect tension, histogram buckets), delta (orb_scale=0, unknown aspect), replay (mocked transit path), and schema (hash, validators).
