"""T016: 009 calibration script runs and passes SC-004 thresholds (smoke test)."""

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_009_calibration_script_runs():
    """Run calibration_sex_transit.py with small N and loose thresholds; must exit 0."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/009/calibration_sex_transit.py",
            "--n", "80",
            "--days", "14",
            "--mean-threshold", "0.05",
            "--p95-threshold", "0.15",
            "--cohen-threshold", "1.0",
        ],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")
