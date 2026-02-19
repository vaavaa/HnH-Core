"""
Replay-relevant config subset and configuration_hash (Spec 002).
xxhash of canonical serialization (orjson); replay-relevant fields only. Spec 003.
"""

from __future__ import annotations

from dataclasses import dataclass

import orjson
import xxhash

from hnh.identity.schema import AXES, PARAMETERS

# Hard cap from spec: shock_multiplier ≤ 2.0
ENGINE_SHOCK_MULTIPLIER_HARD_CAP: float = 2.0


@dataclass(frozen=True)
class ReplayConfig:
    """
    Subset of config used for replay signature.
    Delta limits (global, axis, parameter), shock threshold, shock_multiplier, orb/weights.
    shock_multiplier must be ≤ ENGINE_SHOCK_MULTIPLIER_HARD_CAP (2.0).
    """

    global_max_delta: float
    shock_threshold: float
    shock_multiplier: float
    axis_max_delta: tuple[tuple[str, float], ...] = ()
    parameter_max_delta: tuple[tuple[str, float], ...] = ()

    def __post_init__(self) -> None:
        if self.shock_multiplier > ENGINE_SHOCK_MULTIPLIER_HARD_CAP:
            raise ValueError(
                f"shock_multiplier must be ≤ {ENGINE_SHOCK_MULTIPLIER_HARD_CAP}, got {self.shock_multiplier}"
            )

    @property
    def axis_max_delta_dict(self) -> dict[str, float]:
        return dict(self.axis_max_delta)

    @property
    def parameter_max_delta_dict(self) -> dict[str, float]:
        return dict(self.parameter_max_delta)


def compute_configuration_hash(config: ReplayConfig) -> str:
    """
    xxhash of replay-relevant fields only (canonical orjson). Spec 003.
    Deterministic; same config → same hash.
    """
    payload = {
        "global_max_delta": config.global_max_delta,
        "shock_threshold": config.shock_threshold,
        "shock_multiplier": config.shock_multiplier,
        "axis_max_delta": dict(sorted(config.axis_max_delta_dict.items())),
        "parameter_max_delta": dict(sorted(config.parameter_max_delta_dict.items())),
    }
    blob = orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
    return xxhash.xxh3_128(blob, seed=0).hexdigest()


def resolve_max_delta(
    param_index: int,
    config: ReplayConfig,
    axis_name_from_index: str,
) -> float:
    """
    Hierarchy: parameter > axis > global.
    Returns effective max_delta for the given parameter index.
    """
    param_name = PARAMETERS[param_index]
    if param_name in config.parameter_max_delta_dict:
        return config.parameter_max_delta_dict[param_name]
    if axis_name_from_index in config.axis_max_delta_dict:
        return config.axis_max_delta_dict[axis_name_from_index]
    return config.global_max_delta
