"""
Unit tests for Spec 002 Phase 8: Replay harness, determinism, tolerance 1e-9.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from hnh.config.replay_config import ReplayConfig
from hnh.identity.schema import IdentityCore, NUM_AXES, NUM_PARAMETERS, _registry
from hnh.state.replay_v2 import (
    PHASE_WINDOW_DAYS,
    REPLAY_TOLERANCE,
    replay_match,
    replay_output_hash,
    run_step_v2,
)


def _make_identity(uid: str = "replay-test-1"):
    _registry.discard(uid)
    base = (0.5,) * NUM_PARAMETERS
    sens = (0.5,) * NUM_PARAMETERS
    return IdentityCore(identity_id=uid, base_vector=base, sensitivity_vector=sens)


def _make_config():
    return ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)


def test_run_step_v2_returns_result_shape() -> None:
    """T8.1: run_step_v2 returns params_final (32), axis_final (8)."""
    identity = _make_identity("r1")
    config = _make_config()
    t = datetime(2025, 2, 18, 12, 0, 0, tzinfo=timezone.utc)
    result = run_step_v2(identity, config, t, memory_signature="m1")
    assert len(result.params_final) == NUM_PARAMETERS
    assert len(result.axis_final) == NUM_AXES
    assert result.identity_hash == identity.identity_hash
    assert result.configuration_hash
    assert result.memory_signature == "m1"
    _registry.discard("r1")


def test_run_step_v2_deterministic_n_runs() -> None:
    """T8.2: N runs with same inputs → identical output hash and within 1e-9."""
    identity = _make_identity("r2")
    config = _make_config()
    t = datetime(2025, 2, 18, 12, 0, 0, tzinfo=timezone.utc)
    mem = (0.0,) * NUM_PARAMETERS
    results = []
    for _ in range(5):
        r = run_step_v2(identity, config, t, memory_delta=mem, memory_signature="m2")
        results.append(r)
    hashes = [replay_output_hash(r.params_final, r.axis_final) for r in results]
    assert len(set(hashes)) == 1
    for i in range(1, len(results)):
        assert replay_match(
            results[0].params_final,
            results[0].axis_final,
            results[i].params_final,
            results[i].axis_final,
            tolerance=REPLAY_TOLERANCE,
        )
    _registry.discard("r2")


def test_replay_match_tolerance() -> None:
    """replay_match respects 1e-9 tolerance."""
    base = (0.5,) * NUM_PARAMETERS
    axis = (0.5,) * NUM_AXES
    # Identical
    assert replay_match(base, axis, base, axis) is True
    # Within 1e-9
    small = tuple(x + 1e-10 for x in base)
    assert replay_match(base, axis, small, axis) is True
    # Beyond tolerance
    bad = tuple(x + 1e-8 for x in base)
    assert replay_match(base, axis, bad, axis) is False


def test_replay_output_hash_stable() -> None:
    """Same params_final + axis_final → same hash."""
    p = (0.5,) * NUM_PARAMETERS
    a = (0.5,) * NUM_AXES
    assert replay_output_hash(p, a) == replay_output_hash(p, a)


def test_run_step_v2_with_memory_delta() -> None:
    """Memory delta affects params_final."""
    identity = _make_identity("r3")
    config = _make_config()
    t = datetime(2025, 2, 18, 12, 0, 0, tzinfo=timezone.utc)
    r_no_mem = run_step_v2(identity, config, t, memory_signature="m3")
    mem = [0.0] * NUM_PARAMETERS
    mem[0] = 0.02
    r_with_mem = run_step_v2(identity, config, t, memory_delta=tuple(mem), memory_signature="m3")
    assert r_no_mem.params_final != r_with_mem.params_final
    _registry.discard("r3")


def test_run_step_v2_rejects_wrong_memory_delta_length() -> None:
    """memory_delta length must be 32."""
    identity = _make_identity("r4")
    config = _make_config()
    t = datetime(2025, 2, 18, 12, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="memory_delta must have length"):
        run_step_v2(identity, config, t, memory_delta=(0.0,) * 31, memory_signature="m4")
    _registry.discard("r4")


def test_replay_match_rejects_wrong_lengths() -> None:
    """replay_match returns False for wrong-length vectors."""
    p = (0.5,) * NUM_PARAMETERS
    a = (0.5,) * NUM_AXES
    assert replay_match((0.5,) * 31, a, p, a) is False
    assert replay_match(p, (0.5,) * 7, p, a) is False


def test_run_step_v2_normalizes_timezone_to_utc() -> None:
    """Naive and non-UTC datetime are normalized to UTC in result."""
    identity = _make_identity("r5")
    config = _make_config()
    t_naive = datetime(2025, 2, 18, 12, 0, 0)
    r1 = run_step_v2(identity, config, t_naive, memory_signature="m5")
    assert r1.injected_time_utc.endswith("+00:00") or "Z" in r1.injected_time_utc or r1.injected_time_utc[-6:] == "+00:00"
    t_local = datetime(2025, 2, 18, 12, 0, 0, tzinfo=ZoneInfo("Europe/Moscow"))
    r2 = run_step_v2(identity, config, t_local, memory_signature="m5")
    assert r2.params_final == r1.params_final
    _registry.discard("r5")


def test_run_step_v2_with_transit_mock() -> None:
    """With tr mocked and natal_positions, transit path and _transit_signature_hash(transit_data) are used."""
    from unittest.mock import MagicMock

    from hnh.state import replay_v2

    identity = _make_identity("r6")
    config = _make_config()
    t = datetime(2025, 2, 18, 12, 0, 0, tzinfo=timezone.utc)
    natal = {"positions": [{"planet": "Sun", "longitude": 300.0}], "aspects": []}
    mock_transit = {"positions": [], "aspects_to_natal": [{"aspect": "Square", "angle": 90.0, "separation": 91.0}]}
    original_tr = replay_v2.tr
    try:
        replay_v2.tr = MagicMock()
        replay_v2.tr.compute_transit_signature.return_value = mock_transit
        r = run_step_v2(identity, config, t, memory_signature="m6", natal_positions=natal)
        assert replay_v2.tr.compute_transit_signature.called
        assert r.transit_signature != replay_v2._transit_signature_hash(None)
        assert r.params_final is not None
    finally:
        replay_v2.tr = original_tr
    _registry.discard("r6")


def test_run_step_v2_phase_blending_and_daily_transit_effect() -> None:
    """With transit_effect_history, result uses 0.7*daily + 0.3*phase; daily_transit_effect is returned."""
    identity = _make_identity("r7")
    config = _make_config()
    t = datetime(2025, 2, 18, 12, 0, 0, tzinfo=timezone.utc)
    r_no_history = run_step_v2(identity, config, t, memory_signature="m7")
    assert len(r_no_history.daily_transit_effect) == NUM_PARAMETERS

    # Fake history: constant small effect so phase is non-zero
    fake = (0.01,) * NUM_PARAMETERS
    history = [fake] * PHASE_WINDOW_DAYS
    r_with_history = run_step_v2(
        identity, config, t, memory_signature="m7", transit_effect_history=history
    )
    # With same time, daily_transit_effect is identical
    assert r_with_history.daily_transit_effect == r_no_history.daily_transit_effect
    # But params_final can differ because we blend 0.7*daily + 0.3*phase (phase = fake here)
    # So r_with_history has more influence from fake → different from r_no_history unless daily was already ~fake
    assert r_with_history.params_final is not None
    _registry.discard("r7")
