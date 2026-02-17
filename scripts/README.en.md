# HnH usage examples

Scripts in this folder demonstrate how to use the HnH library from Python.

**Requirement:** run from the **project root** with the virtual environment activated. If the package is installed (`pip install -e .`), use:

```bash
cd /path/to/core
source .venv/bin/activate
python scripts/01_basic_step.py
```

If the package is not installed: `PYTHONPATH=. python scripts/01_basic_step.py`

| Script | Description |
|--------|-------------|
| [01_basic_step.py](01_basic_step.py) | One simulation step for a date; prints vector and modifiers |
| [02_replay_and_log.py](02_replay_and_log.py) | Step → write to log (JSON Lines) → replay and verify output matches |
| [03_relational_memory.py](03_relational_memory.py) | Relational Memory: events, modifier, step with memory |
| [04_teacher_pilot.py](04_teacher_pilot.py) | Planetary Teacher: create, pilot run over a date range |
| [05_multiple_dates_jsonl.py](05_multiple_dates_jsonl.py) | Multiple dates in a row; output as JSON Lines |

More in the user guide: [en-user-guide-readme.md](../en-user-guide-readme.md).  
Russian: [user-guide-readme.md](../user-guide-readme.md) and [README.md](README.md).
