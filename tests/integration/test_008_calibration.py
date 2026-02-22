"""T018: Calibration script runs and exits 0 with loose thresholds (smoke test)."""

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_calibration_script_runs():
    """Run calibration_sanity.py with small N and loose thresholds; must exit 0."""
    result = subprocess.run(
        [sys.executable, "scripts/008/calibration_sanity.py", "--n", "80", "--mean-threshold", "0.05", "--p95-threshold", "0.15", "--cohen-threshold", "20.0"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (result.stdout or "") + (result.stderr or "")
