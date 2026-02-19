"""Tests for lifecycle config hash and run integration (T003, T019)."""

import pytest

from hnh.config.replay_config import ReplayConfig, compute_configuration_hash
from hnh.lifecycle.run import is_lifecycle_active


def test_lifecycle_inactive_default() -> None:
    config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)
    assert is_lifecycle_active(config) is False
    assert getattr(config, "mode", "product") == "product"
    assert getattr(config, "lifecycle_enabled", False) is False


def test_lifecycle_active_when_enabled() -> None:
    config = ReplayConfig(
        global_max_delta=0.15,
        shock_threshold=0.8,
        shock_multiplier=1.5,
        mode="research",
        lifecycle_enabled=True,
    )
    assert is_lifecycle_active(config) is True


def test_config_hash_includes_lifecycle_when_enabled() -> None:
    c1 = ReplayConfig(
        global_max_delta=0.15,
        shock_threshold=0.8,
        shock_multiplier=1.5,
        mode="research",
        lifecycle_enabled=True,
        initial_f=0.0,
        initial_w=0.0,
    )
    c2 = ReplayConfig(
        global_max_delta=0.15,
        shock_threshold=0.8,
        shock_multiplier=1.5,
        mode="research",
        lifecycle_enabled=True,
        initial_f=0.1,
        initial_w=0.0,
    )
    h1 = compute_configuration_hash(c1)
    h2 = compute_configuration_hash(c2)
    assert h1 != h2  # different initial_f must change hash
