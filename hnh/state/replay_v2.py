"""
Replay harness for Spec 002 (32-param model).
Inputs: identity snapshot, config snapshot, time, memory snapshot.
Same inputs → identical params_final and axis_final (tolerance 1e-9). No system clock.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import orjson

from hnh.config.replay_config import ReplayConfig, compute_configuration_hash
from hnh.identity.schema import IdentityCore, NUM_AXES, NUM_PARAMETERS
from hnh.modulation.boundaries import apply_bounds
from hnh.modulation.delta import compute_raw_delta_32
from hnh.state.assembler import assemble_state

REPLAY_TOLERANCE: float = 1e-9

try:
    from hnh.astrology import aspects as asp
    from hnh.astrology import transits as tr
except ImportError:
    asp = None  # type: ignore[assignment]
    tr = None  # type: ignore[assignment]


@dataclass(frozen=True)
class ReplayResult:
    """Result of one replay step: params_final, axis_final, and replay signature fields."""

    params_final: tuple[float, ...]
    axis_final: tuple[float, ...]
    identity_hash: str
    configuration_hash: str
    injected_time_utc: str
    transit_signature: str
    shock_flag: bool
    effective_max_delta: tuple[float, ...]
    memory_signature: str


def _transit_signature_hash(transit_data: dict[str, Any] | None) -> str:
    """Deterministic hash of transit signature for replay."""
    if not transit_data:
        return hashlib.sha256(b"no_transit").hexdigest()
    blob = orjson.dumps(transit_data, option=orjson.OPT_SORT_KEYS)
    return hashlib.sha256(blob).hexdigest()


def run_step_v2(
    identity: IdentityCore,
    config: ReplayConfig,
    injected_time_utc: datetime,
    memory_delta: tuple[float, ...] | None = None,
    memory_signature: str = "",
    natal_positions: dict[str, Any] | None = None,
) -> ReplayResult:
    """
    Run one deterministic state step (v0.2 pipeline).
    Inputs: identity, config, time, memory_delta (+ memory_signature for log), optional natal_positions.
    No system clock. Same inputs → identical result.
    """
    if injected_time_utc.tzinfo is None:
        injected_time_utc = injected_time_utc.replace(tzinfo=timezone.utc)
    elif injected_time_utc.tzinfo != timezone.utc:
        injected_time_utc = injected_time_utc.astimezone(timezone.utc)
    injected_iso = injected_time_utc.isoformat()

    config_hash = compute_configuration_hash(config)
    memory_delta = memory_delta if memory_delta is not None else (0.0,) * NUM_PARAMETERS
    if len(memory_delta) != NUM_PARAMETERS:
        raise ValueError(f"memory_delta must have length {NUM_PARAMETERS}, got {len(memory_delta)}")

    transit_data: dict[str, Any] | None = None
    raw_delta_list = [0.0] * NUM_PARAMETERS

    if tr is not None and natal_positions is not None:
        transit_data = tr.compute_transit_signature(injected_time_utc, natal_positions)
        aspects = transit_data.get("aspects_to_natal", [])
        raw_delta_list = list(compute_raw_delta_32(aspects))
    raw_delta = tuple(raw_delta_list)

    # Shock: max |raw_delta| > threshold
    max_raw = max(abs(r) for r in raw_delta)
    shock_active = max_raw > config.shock_threshold

    bounded_delta, effective_max_delta = apply_bounds(raw_delta, config, shock_active)

    params_final, axis_final = assemble_state(
        identity.base_vector,
        identity.sensitivity_vector,
        bounded_delta,
        memory_delta,
    )

    transit_sig_hash = _transit_signature_hash(transit_data)

    return ReplayResult(
        params_final=params_final,
        axis_final=axis_final,
        identity_hash=identity.identity_hash,
        configuration_hash=config_hash,
        injected_time_utc=injected_iso,
        transit_signature=transit_sig_hash,
        shock_flag=shock_active,
        effective_max_delta=effective_max_delta,
        memory_signature=memory_signature,
    )


def replay_match(
    a_params: tuple[float, ...],
    a_axis: tuple[float, ...],
    b_params: tuple[float, ...],
    b_axis: tuple[float, ...],
    tolerance: float = REPLAY_TOLERANCE,
) -> bool:
    """
    True if (a_params, a_axis) and (b_params, b_axis) match within absolute tolerance.
    Spec: 1e-9.
    """
    if len(a_params) != NUM_PARAMETERS or len(b_params) != NUM_PARAMETERS:
        return False
    if len(a_axis) != NUM_AXES or len(b_axis) != NUM_AXES:
        return False
    for i in range(NUM_PARAMETERS):
        if abs(a_params[i] - b_params[i]) > tolerance:
            return False
    for i in range(NUM_AXES):
        if abs(a_axis[i] - b_axis[i]) > tolerance:
            return False
    return True


def replay_output_hash(params_final: tuple[float, ...], axis_final: tuple[float, ...]) -> str:
    """Deterministic hash of params_final + axis_final for replay identity check."""
    blob = orjson.dumps(
        [list(params_final), list(axis_final)],
        option=orjson.OPT_SORT_KEYS,
    )
    return hashlib.sha256(blob).hexdigest()
