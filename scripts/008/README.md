# 008 — Calibration & scripts

## Calibration sanity check (SC-004)

**Script**: `calibration_sanity.py`  
**Purpose**: Check that sex-based 32D shifts stay within calibration thresholds (mean axis diff, p95, Cohen's d). Uses a **deterministic synthetic population** (fixed RNG seed).

### Data source

- **Synthetic population**: generated in-process with `random.Random(seed)` (default seed: **42**). Each natal has positions for Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn with random longitudes; sex is assigned 50/50.
- **Reproducibility**: Same seed and `--n` yield identical results. No external dataset required.

### Thresholds (documented in script and spec)

| Metric | Default | Spec (SC-004) |
|--------|---------|----------------|
| \|mean(axis_male − axis_female)\| | ≤ 0.01 | ≤ 0.01 |
| p95 of axis difference | ≤ 0.10 | ≤ 0.10 |
| \|Cohen's d\| per axis | ≤ 0.2 | overlap criterion |

With default **sex_strength=0.03** and **sex_max_param_delta=0.04**, the default thresholds from spec may be strict; the script exits non-zero if any axis violates. Use script options to adjust thresholds for your calibration policy.

### Run locally

From repo root (so `hnh` is importable):

```bash
uv run python scripts/008/calibration_sanity.py [options]
# or
python -m scripts.008.calibration_sanity  # if scripts is on PYTHONPATH
```

Options:

- `--seed N` — RNG seed (default: 42)
- `--n N` — population size (default: 2000; use 10000 for full CI)
- `--date YYYY-MM-DD` — step date (default: 2020-06-15)
- `--mean-threshold`, `--p95-threshold`, `--cohen-threshold` — override thresholds

Exit code: **0** if all pass, **1** if any threshold violated, **2** if setup error.

### CI

When **sex_strength** or **W32** is changed, run this script in CI and fail the job if it exits non-zero.

Example (GitHub Actions or similar):

```yaml
- name: 008 calibration sanity
  run: uv run python scripts/008/calibration_sanity.py --seed 42 --n 2000
```

Document the seed and `--n` in your CI config so runs are reproducible. Optionally add a dedicated job that runs only when files under `hnh/sex/` or calibration script change.
