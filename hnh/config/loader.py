"""
Config loader: YAML or TOML (Spec 002 T4.1).
Extracts ReplayConfig subset for replay signature.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hnh.config.replay_config import (
    ENGINE_SHOCK_MULTIPLIER_HARD_CAP,
    ReplayConfig,
)
from hnh.identity.schema import AXES, PARAMETERS


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        raise RuntimeError("PyYAML not installed; pip install pyyaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config(config_path: str | Path) -> dict[str, Any]:
    """
    Load config from YAML or TOML file.
    Returns full dict; use extract_replay_config() for ReplayConfig.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    suf = path.suffix.lower()
    if suf in (".yaml", ".yml"):
        return _load_yaml(path)
    if suf == ".toml":
        return _load_toml(path)
    raise ValueError(f"Unsupported config format: {suf}. Use .yaml or .toml")


def extract_replay_config(data: dict[str, Any]) -> ReplayConfig:
    """
    Build ReplayConfig from loaded dict.
    global_max_delta required; axis/parameter overrides optional.
    shock_multiplier validated against ENGINE_SHOCK_MULTIPLIER_HARD_CAP.
    """
    global_max_delta = float(data.get("global_max_delta", 0.15))
    shock_threshold = float(data.get("shock_threshold", 0.8))
    shock_multiplier = float(data.get("shock_multiplier", 1.5))
    if shock_multiplier > ENGINE_SHOCK_MULTIPLIER_HARD_CAP:
        raise ValueError(
            f"shock_multiplier must be ≤ {ENGINE_SHOCK_MULTIPLIER_HARD_CAP}, got {shock_multiplier}"
        )
    axis_max_delta: list[tuple[str, float]] = []
    if "axis_max_delta" in data and isinstance(data["axis_max_delta"], dict):
        axis_max_delta = [(k, float(v)) for k, v in data["axis_max_delta"].items() if k in AXES]
    parameter_max_delta: list[tuple[str, float]] = []
    if "parameter_max_delta" in data and isinstance(data["parameter_max_delta"], dict):
        parameter_max_delta = [(k, float(v)) for k, v in data["parameter_max_delta"].items() if k in PARAMETERS]
    return ReplayConfig(
        global_max_delta=global_max_delta,
        shock_threshold=shock_threshold,
        shock_multiplier=shock_multiplier,
        axis_max_delta=tuple(sorted(axis_max_delta)),
        parameter_max_delta=tuple(sorted(parameter_max_delta)),
    )
