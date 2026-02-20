# User Guide: HnH via CLI

How to install the engine and use it from the command line.

---

## What This Is

**HnH** is a deterministic personality engine: given a date, it outputs a **behavioral vector** (32 parameters, 8 axes) and optionally **lifecycle** state (F, W, state). It uses a **layered architecture** (spec 006): natal chart, 32D behavior, transits, and optional lifecycle. The **canonical path** is a single step via **Agent.step(date)**. Everything is reproducible; the core does not use system time.

Use the **CLI** to run a simulation for one date: **`hnh agent step`** (006) is the main command; **`run-v2`** (002) and **`run`** (001) remain for compatibility. Scripts in **`scripts/006/`** and **`scripts/002/`** demonstrate Agent and replay usage.

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

The date is in **YYYY-MM-DD** format (UTC noon). It is “injected”: the engine does not read the system clock.

**Commands:** **`hnh agent step`** (006 — canonical path, 32 parameters), **`hnh run-v2`** (002), **`hnh run`** (001). Help: `hnh --help`, `hnh agent step --help`.

### Canonical command 006: agent step

One step via **Agent.step(date)** — layers: natal, behavior, transits (and with `--lifecycle`: lifecycle).

```bash
hnh agent step --date 2024-06-15
```

**Sample output:**

```
params_final (32): [0.58, 0.51, ...]
axis_final (8): [0.53, 0.5, ...]
```

With **research mode** (lifecycle: fatigue F, will W, state ALIVE/DISABLED/TRANSCENDED):

```bash
hnh agent step --date 2024-06-15 --lifecycle
```

Output also includes: `lifecycle F: ... W: ... state: ...`

- **params_final** (32) and **axis_final** (8) — behavioral vector and per-axis aggregates, all in 0.0–1.0.
- **run-v2** delegates to Agent on the simple path (no phase/history); **run** is the 001 model (7 parameters).

---

### Single-line JSON output

Useful for scripts and logging:

```bash
hnh agent step --date 2024-01-10 --json
```

Example (without lifecycle):

```json
{"axis_final": [...], "injected_time_utc": "2024-01-10T12:00:00+00:00", "params_final": [...]}
```

With `--lifecycle`, the JSON includes `lifecycle_F`, `lifecycle_W`, `lifecycle_state`.

---

### Seed (reproducibility)

The default seed is **0**. You can set it explicitly:

```bash
hnh run --date 2024-03-20 --seed 42
```

The same `--date` and `--seed` always produce the same output.

---

### Replay check

The **--replay** flag runs the computation twice with the same parameters and checks that the output matches:

```bash
hnh agent step --date 2024-05-01 --replay
```

On success: `Replay OK: identical output.` If outputs differ, the command exits with code 1.

---

## 006 layers and 32-parameter model

In the **006** architecture, one step is performed by **Agent**: natal (NatalChart) → behavior (BehavioralCore, 32D) → transits (TransitEngine) → optionally lifecycle (LifecycleEngine). The **`hnh agent step`** command does exactly that. The behavior model is **hierarchical 8×4**: 8 axes, 4 sub-parameters each (32 total), values **0.0–1.0**.

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
# Canonical 006 step (recommended)
hnh agent step --date 2024-06-15

# With lifecycle (research) and JSON
hnh agent step --date 2024-06-15 --lifecycle --json

# Replay check
hnh agent step --date 2024-06-15 --replay

# 002 mode (run-v2 delegates to Agent on simple path)
hnh run-v2 --date 2024-06-15

# 001 mode (7 parameters)
hnh run --date 2024-06-15

# Invalid date — error
hnh agent step --date 2024-13-01
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

### Scripts 006 — Agent and layers

In **`scripts/006/`** you’ll find demos of the layered architecture: building an Agent (product and research), calling `step()` over dates, and comparing with replay_v2.

```bash
python scripts/006/run_agent_demo.py
```

See [scripts/006/README.md](scripts/006/README.md).

---

## Using as a library

The **canonical path (006)** is **Agent.step(date)**. The CLI command `hnh agent step` calls it.

From Python you can:

- Use **Agent** as the single orchestration point for a step: natal, 32D behavior, transits, optional lifecycle (`hnh.agent.Agent`);
- **run_step_v2** delegates to Agent.step() on the simple path; the previous implementation is used for phase/history and memory_delta;
- Write v2 logs via **state_logger_v2** (orjson); use **Planetary Teacher** and **LLM adapter** (`hnh.interface`).

Minimal 006 example:

```python
from datetime import date
from hnh.agent import Agent
from hnh.config.replay_config import ReplayConfig

birth_data = {"positions": [{"planet": "Sun", "longitude": 90.0}, {"planet": "Moon", "longitude": 120.0}]}
config = ReplayConfig(global_max_delta=0.08, shock_threshold=0.5, shock_multiplier=1.0)
agent = Agent(birth_data, config=config, lifecycle=False)
agent.step(date(2025, 2, 18))
print("params_final (32):", agent.behavior.current_vector[:8], "...")
# axis_final = aggregate_axis(agent.behavior.current_vector); TransitState = agent.transits.state(d, config)
```

With lifecycle (research): `Agent(..., lifecycle=True)`; after a step use `agent.lifecycle.F`, `agent.lifecycle.W`, `agent.lifecycle.state`. More in **`scripts/006/`** and **`specs/006-layered-agent-architecture/`**.

---

## See also

- **Russian version of this guide:** [user-guide-readme.md](user-guide-readme.md)
- **Project overview:** [README.md](README.md)
- **Spec 006 (layered architecture, Agent):** [specs/006-layered-agent-architecture/](specs/006-layered-agent-architecture/)
- **Spec 002 (8×4 model):** [specs/002-hierarchical-personality-model/](specs/002-hierarchical-personality-model/)
- **Scripts 006:** [scripts/006/README.md](scripts/006/README.md)
- **State log contract:** [specs/001-deterministic-personality-engine/contracts/state-log-spec.md](specs/001-deterministic-personality-engine/contracts/state-log-spec.md)
