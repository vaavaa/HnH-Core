"""
T040: CLI — simulate for date, print vector/modifiers, replay flag.
"""

from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

import pytest

from hnh.cli import main
from hnh.core.identity import IdentityCore
from hnh.core.parameters import BehavioralVector


@pytest.fixture(autouse=True)
def _clear_registry():
    from hnh.core.identity import _registry
    _registry.clear()
    yield
    _registry.clear()


def _make_identity():
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.4,
        verbosity=0.6,
        correction_rate=0.3,
        humor_level=0.5,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    return IdentityCore(
        identity_id="cli-test-id",
        base_traits=base,
        symbolic_input=None,
    )


def test_cli_date_and_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    """T040: CLI with --date and --json prints valid state JSON."""
    with patch("hnh.cli._default_identity", side_effect=_make_identity):
        with patch("sys.argv", ["hnh", "--date", "2024-06-15", "--json"]):
            main()
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert "final_behavioral_vector" in data
    assert "active_modifiers" in data
    assert "identity_hash" in data
    assert set(data["final_behavioral_vector"].keys()) == {
        "warmth", "strictness", "verbosity", "correction_rate",
        "humor_level", "challenge_intensity", "pacing",
    }


def test_cli_replay_mode_identical_output(capsys: pytest.CaptureFixture[str]) -> None:
    """T040: --replay runs twice and verifies identical output."""
    with patch("hnh.cli._default_identity", side_effect=_make_identity):
        with patch("sys.argv", ["hnh", "--date", "2024-01-01", "--replay"]):
            main()
    out = capsys.readouterr().out
    assert "Replay OK" in out or "identical" in out.lower()


def test_cli_invalid_date_exits_nonzero() -> None:
    """CLI rejects invalid --date."""
    with patch("sys.argv", ["hnh", "--date", "not-a-date"]):
        with patch("sys.exit") as mock_exit:
            with patch("sys.stderr", StringIO()):
                main()
            mock_exit.assert_called_once_with(1)
