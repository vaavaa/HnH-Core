# User Guide: HnH via CLI

How to install the engine and use it from the command line.

---

## What This Is

**HnH** is a deterministic personality engine: given a date and a seed, it outputs a **behavioral vector** and **active modifiers**. On this branch (spec 002) the **hierarchical 8×4 model** is used: **32 parameters** (8 axes × 4 sub-parameters), all values in 0–1, plus per-axis aggregates (`axis_final`). Everything is reproducible: the same inputs yield the same result. The core does not use system time or unseeded randomness.

The **CLI** (001 mode) or scripts in **`scripts/002/`** run a simulation for a single date and print the result to the console or as a single JSON line.

---

## Installation

Requires **Python 3.12+**.

```bash
# Clone the repo and go to the project directory
cd /path/to/core

# Create a virtual environment and install the package
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# or:  .venv\Scripts\activate   # Windows

pip install -e .
```

The `hnh` command will be available in this environment.

**Optional (astrology layer — natal/transits):**

```bash
pip install -e ".[astrology]"
```

Without this extra, the engine uses a single fixed base vector; with it you can plug in natal chart and transits (when added to the CLI).

---

## Running the CLI

### Required argument: date

The date is in **YYYY-MM-DD** format. It is treated as “injected”: the engine does not read the system clock.

```bash
hnh --date 2024-06-15
```

**Sample output (CLI, 001 mode — 7 parameters):**

```
final_behavioral_vector: {'warmth': 0.5, 'strictness': 0.4, 'verbosity': 0.6, 'correction_rate': 0.3, 'humor_level': 0.5, 'challenge_intensity': 0.4, 'pacing': 0.5}
active_modifiers: {'transit_delta': {'warmth': 0.0, 'strictness': 0.0, ...}, ...}
```

For **32-parameter** output (params_final, axis_final) use the scripts in `scripts/002/`.

- **final_behavioral_vector** (001 mode) — seven parameters; in the 002 model the output is **params_final** (32) and **axis_final** (8), all in 0.0–1.0.
- **active_modifiers** — how the base vector was adjusted (transit_delta, relational, etc.).

---

### Single-line JSON output

Useful for scripts and logging:

```bash
hnh --date 2024-01-10 --json
```

Example:

```json
{"active_modifiers": {...}, "final_behavioral_vector": {...}, "identity_hash": "...", "injected_time": "2024-01-10T12:00:00+00:00"}
```

---

### Seed (reproducibility)

The default seed is **0**. You can set it explicitly:

```bash
hnh --date 2024-03-20 --seed 42
```

The same `--date` and `--seed` always produce the same output.

---

### Replay check

The **--replay** flag runs the computation twice with the same parameters and checks that the output matches:

```bash
hnh --date 2024-05-01 --replay
```

On success you’ll see: `Replay OK: identical output.`  
If outputs differ, the command exits with code 1.

With JSON:

```bash
hnh --date 2024-05-01 --replay --json
```

On success the same single JSON line is printed (no duplicate; it only verifies).

---

## 32 parameters (8 axes × 4) — model 002

On this branch the main model is **hierarchical 8×4**: 8 axes, each with 4 sub-parameters (32 total), values from **0.0** to **1.0**.

| Axis | Sub-parameters |
|------|----------------|
| **1 — Emotional Tone** | warmth, empathy, patience, emotional_intensity |
| **2 — Stability & Regulation** | stability, reactivity, resilience, stress_response |
| **3 — Cognitive Style** | analytical_depth, abstraction_level, detail_orientation, big_picture_focus |
| **4 — Structure & Discipline** | structure_preference, consistency, rule_adherence, planning_bias |
| **5 — Communication Style** | verbosity, directness, questioning_frequency, explanation_bias |
| **6 — Teaching Style** | correction_intensity, challenge_level, encouragement_level, pacing |
| **7 — Power & Boundaries** | authority_presence, dominance, tolerance_for_errors, conflict_tolerance |
| **8 — Motivation & Drive** | ambition, curiosity, initiative, persistence |

Output per date: **params_final** (32 values) and **axis_final** (8 aggregates — mean of 4 sub-parameters per axis). See `scripts/002/` for demos.

*(001 mode: seven parameters — warmth, strictness, verbosity, correction_rate, humor_level, challenge_intensity, pacing; used by the CLI and `scripts/01_*` … `05_*`.)*

---

## Example commands

```bash
# Simulate for 15 June 2024, console output
hnh --date 2024-06-15

# Same, single JSON line
hnh --date 2024-06-15 --json

# Different seed
hnh --date 2024-06-15 --seed 123

# Check that two runs give the same result
hnh --date 2024-06-15 --replay

# Invalid date — error and hint
hnh --date 2024-13-01
# Invalid --date: ... Use YYYY-MM-DD.
```

---

## Examples in the `scripts/` folder

The repo includes a **`scripts/`** folder with ready-made examples. Run from the **project root** with the virtual environment activated:

```bash
cd /path/to/core
source .venv/bin/activate
pip install -e .   # once
python scripts/01_basic_step.py
```

If the package is not installed in the venv, use: `PYTHONPATH=. python scripts/01_basic_step.py`.

| Script | What it does |
|--------|----------------|
| **01_basic_step.py** | One simulation step for a date: creates Identity, calls `run_step`, prints vector and modifiers. Optional date argument: `python scripts/01_basic_step.py 2024-09-01`. |
| **02_replay_and_log.py** | One step → write transition to a file (JSON Lines) → replay and verify output matches. Default output file: `state.log`; options: `--out other.log`, `--date 2024-07-01`, `--seed 42`. |
| **03_relational_memory.py** | Relational Memory: create user memory, add events (interaction, error), compute modifier; run step with `relational_snapshot=modifier`. Shows derived metrics and final vector. |
| **04_teacher_pilot.py** | Planetary Teacher: create a “teacher” with birth date and coordinates, then `pilot_run` over a date range (default 7 days). Options: `--days 14`, `--start 2024-09-01`. |
| **05_multiple_dates_jsonl.py** | Simulate over a range of dates; one JSON line per date (JSON Lines). Run: `python scripts/05_multiple_dates_jsonl.py 2024-01-01 2024-01-07`. Redirect to file: `... > january.jsonl`. |

See also [scripts/README.md](scripts/README.md) (and [scripts/README.en.md](scripts/README.en.md) in English).

---

## 002 examples — hierarchical 8×4 model (32 parameters)

In **`scripts/002/`** there are eight scripts for spec 002: 8 axes × 4 sub-parameters (32 total), natal-derived sensitivity, delta bounds, state assembly, memory v2, orjson logging, and replay with 1e-9 tolerance.

```bash
python scripts/002/01_schema_and_identity.py
python scripts/002/08_full_step_v2.py --date 2025-03-01 --log
```

| Script | What it does |
|--------|----------------|
| **01_schema_and_identity.py** | Axis and parameter registry (8 axes, 32 params), index mapping, IdentityCore v0.2 (base_vector, sensitivity_vector). |
| **02_sensitivity.py** | Sensitivity from natal data (`compute_sensitivity`), debug histogram. |
| **03_raw_delta_and_bounds.py** | raw_delta from aspects, ReplayConfig, apply_bounds (parameter > axis > global, shock). |
| **04_state_assembly.py** | State assembly: base + bounded×sensitivity + memory → params_final (32), axis_final (8). |
| **05_memory_v2.py** | Relational Memory v2: get_memory_delta_32, memory_signature. |
| **06_logging_v2.py** | V2 logging (orjson): build_record_v2, write_record_v2. Options: `--out 002_demo.log`, `--date 2025-02-18`. |
| **07_replay_v2.py** | Replay v2: N runs with same inputs, replay_match (1e-9), replay_output_hash. |
| **08_full_step_v2.py** | Full step: identity + config + time + memory → ReplayResult. Options: `--date`, `--log`. |

See [scripts/002/README.md](scripts/002/README.md) and [specs/002-hierarchical-personality-model/](specs/002-hierarchical-personality-model/).

---

## Using as a library

The CLI is a thin wrapper. From Python you can:

- create **Identity Core** (v0.2: 32 parameters — `hnh.identity.IdentityCore` with `base_vector`, `sensitivity_vector`);
- call **run_step_v2(identity, config, injected_time, memory_delta=..., memory_signature=...)** and get **ReplayResult** (params_final, axis_final, replay signature);
- write v2 logs via **state_logger_v2** (orjson);
- use **Planetary Teacher** and **LLM adapter** (see `hnh.interface`).

Minimal 002 step example (32 parameters):

```python
from datetime import datetime, timezone
from hnh.identity import IdentityCore
from hnh.config.replay_config import ReplayConfig
from hnh.state.replay_v2 import run_step_v2

identity = IdentityCore(
    identity_id="my-id",
    base_vector=(0.5,) * 32,
    sensitivity_vector=(0.5,) * 32,
)
config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)
result = run_step_v2(identity, config, datetime(2025, 2, 18, 12, 0, 0, tzinfo=timezone.utc))
print("params_final (32):", result.params_final[:8], "...")
print("axis_final (8):", result.axis_final)
```

More in `scripts/002/` and `specs/002-hierarchical-personality-model/`. For 001 (7 parameters): `hnh.core.identity`, `hnh.state.replay.run_step`.

---

## See also

- **Project overview and vision:** [README.md](README.md)
- **Engine spec and plan (001):** [specs/001-deterministic-personality-engine/](specs/001-deterministic-personality-engine/)
- **Spec 002 (8×4 model):** [specs/002-hierarchical-personality-model/](specs/002-hierarchical-personality-model/)
- **State log contract:** [specs/001-deterministic-personality-engine/contracts/state-log-spec.md](specs/001-deterministic-personality-engine/contracts/state-log-spec.md)

Russian version of this guide: [user-guide-readme.md](user-guide-readme.md).
