# User Guide: HnH via CLI

How to install the engine and use it from the command line.

---

## What This Is

**HnH** is a deterministic personality engine: given a date and a seed, it outputs a **behavioral vector** (7 parameters in the 0–1 range) and **active modifiers**. Everything is reproducible: the same date and seed always yield the same result. The core does not use system time or unseeded randomness.

The **CLI** runs a simulation for a single date and prints the result to the console or as a single JSON line.

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

**Sample output (default mode):**

```
final_behavioral_vector: {'warmth': 0.5, 'strictness': 0.4, 'verbosity': 0.6, 'correction_rate': 0.3, 'humor_level': 0.5, 'challenge_intensity': 0.4, 'pacing': 0.5}
active_modifiers: {'transit_delta': {'warmth': 0.0, 'strictness': 0.0, ...}, ...}
```

- **final_behavioral_vector** — the seven personality parameters for that date (all in 0.0–1.0).
- **active_modifiers** — how the base vector was adjusted (in the demo: mainly `transit_delta`; with Relational Memory you also get `relational`).

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

## The seven parameters

| Parameter              | Brief meaning                    |
|------------------------|----------------------------------|
| **warmth**             | Warmth, empathy                  |
| **strictness**         | Strictness, demandingness        |
| **verbosity**          | Response length                  |
| **correction_rate**    | Frequency of explicit corrections|
| **humor_level**        | Level of humor                   |
| **challenge_intensity**| Intensity of challenge/difficulty|
| **pacing**             | Pace, delivery speed             |

Values from **0.0** to **1.0**. The current CLI uses one fixed base vector; modifiers (e.g. `transit_delta`) shift it within that range.

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

## Using as a library

The CLI is a thin wrapper. From Python you can:

- create **Identity Core** (your own `identity_id` and base vector);
- call **run_step(identity, injected_time, seed=..., relational_snapshot=...)** and get **DynamicState**;
- write transition logs via **state_logger**;
- use **Planetary Teacher** and **LLM adapter** (see `hnh.interface`).

Minimal step example (same as inside the CLI):

```python
from datetime import datetime, timezone
from hnh.core.identity import IdentityCore
from hnh.core.parameters import BehavioralVector
from hnh.state.replay import run_step

base = BehavioralVector(
    warmth=0.5, strictness=0.4, verbosity=0.6,
    correction_rate=0.3, humor_level=0.5,
    challenge_intensity=0.4, pacing=0.5,
)
identity = IdentityCore(identity_id="my-id", base_traits=base, symbolic_input=None)
state = run_step(identity, datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc), seed=0)
print(state.final_behavior_vector.to_dict())
```

More details in the code and in `specs/001-deterministic-personality-engine/`.

---

## See also

- **Project overview and vision:** [README.md](README.md)
- **Engine spec and plan:** [specs/001-deterministic-personality-engine/](specs/001-deterministic-personality-engine/)
- **State log contract:** [specs/001-deterministic-personality-engine/contracts/state-log-spec.md](specs/001-deterministic-personality-engine/contracts/state-log-spec.md)

Russian version of this guide: [user-guide-readme.md](user-guide-readme.md).
