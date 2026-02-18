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
from hnh.modulation.delta import (
    PHASE_WINDOW_DAYS_BY_CATEGORY,
    compute_raw_delta_32,
    compute_raw_delta_32_by_category,
)
from hnh.state.assembler import assemble_state

REPLAY_TOLERANCE: float = 1e-9

# Phase smoothing: final = base + (PHASE_DAILY_WEIGHT * daily + PHASE_SMOOTH_WEIGHT * phase) + memory
# Dynamic window by planet category: personal 7d (погода), social 30d (сезон), outer 365d (эпоха).
PHASE_DAILY_WEIGHT: float = 0.7
PHASE_SMOOTH_WEIGHT: float = 0.3
# Backward compat: single-window default (e.g. for tests)
PHASE_WINDOW_DAYS: int = PHASE_WINDOW_DAYS_BY_CATEGORY["social"]

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
    daily_transit_effect: tuple[float, ...]  # bounded_delta × sensitivity; for caller's rolling buffer
    daily_transit_effect_by_category: dict[str, tuple[float, ...]] | None = None  # personal/social/outer when using dynamic window


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
    transit_effect_history: list[tuple[float, ...]] | None = None,
    transit_effect_history_by_category: dict[str, list[tuple[float, ...]]] | None = None,
) -> ReplayResult:
    """
    Run one deterministic state step (v0.2 pipeline).
    Optional transit_effect_history: single buffer, window PHASE_WINDOW_DAYS (backward compat).
    Optional transit_effect_history_by_category: {"personal": [...], "social": [...], "outer": [...]}
    with dynamic windows 7 / 30 / 365 days (погода / сезон / эпоха). Blended as
    final = base + (0.7*daily + 0.3*(phase_personal + phase_social + phase_outer)) + memory.
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
    raw_by_cat: dict[str, tuple[float, ...]] | None = None

    if tr is not None and natal_positions is not None:
        transit_data = tr.compute_transit_signature(injected_time_utc, natal_positions)
        aspects = transit_data.get("aspects_to_natal", [])
        if transit_effect_history_by_category is not None:
            raw_by_cat = compute_raw_delta_32_by_category(aspects)
            raw_delta_list = [
                raw_by_cat["personal"][i] + raw_by_cat["social"][i] + raw_by_cat["outer"][i]
                for i in range(NUM_PARAMETERS)
            ]
        else:
            raw_delta_list = list(compute_raw_delta_32(aspects))
    raw_delta = tuple(raw_delta_list)

    max_raw = max(abs(r) for r in raw_delta)
    shock_active = max_raw > config.shock_threshold

    if raw_by_cat is not None and transit_effect_history_by_category is not None:
        bounded_p, _ = apply_bounds(raw_by_cat["personal"], config, shock_active)
        bounded_s, _ = apply_bounds(raw_by_cat["social"], config, shock_active)
        bounded_o, effective_max_delta = apply_bounds(raw_by_cat["outer"], config, shock_active)
        daily_p = tuple(bounded_p[p] * identity.sensitivity_vector[p] for p in range(NUM_PARAMETERS))
        daily_s = tuple(bounded_s[p] * identity.sensitivity_vector[p] for p in range(NUM_PARAMETERS))
        daily_o = tuple(bounded_o[p] * identity.sensitivity_vector[p] for p in range(NUM_PARAMETERS))
        daily_transit_effect = tuple(daily_p[i] + daily_s[i] + daily_o[i] for i in range(NUM_PARAMETERS))
        daily_by_cat = {"personal": daily_p, "social": daily_s, "outer": daily_o}

        phase_parts: list[tuple[float, ...]] = []
        for cat in ("personal", "social", "outer"):
            hist = transit_effect_history_by_category.get(cat) or []
            wdays = PHASE_WINDOW_DAYS_BY_CATEGORY[cat]
            window = hist[-wdays:] if len(hist) > wdays else hist
            if not window:
                phase_parts.append((0.0,) * NUM_PARAMETERS)
            else:
                n = len(window)
                phase_parts.append(tuple(sum(v[i] for v in window) / n for i in range(NUM_PARAMETERS)))
        phase_combined = tuple(
            phase_parts[0][i] + phase_parts[1][i] + phase_parts[2][i] for i in range(NUM_PARAMETERS)
        )
        effective_transit = tuple(
            PHASE_DAILY_WEIGHT * daily_transit_effect[p] + PHASE_SMOOTH_WEIGHT * phase_combined[p]
            for p in range(NUM_PARAMETERS)
        )
        params_final, axis_final = assemble_state(
            identity.base_vector,
            identity.sensitivity_vector,
            (0.0,) * NUM_PARAMETERS,
            memory_delta,
            precomputed_transit_effect=effective_transit,
        )
        return ReplayResult(
            params_final=params_final,
            axis_final=axis_final,
            identity_hash=identity.identity_hash,
            configuration_hash=config_hash,
            injected_time_utc=injected_iso,
            transit_signature=_transit_signature_hash(transit_data),
            shock_flag=shock_active,
            effective_max_delta=effective_max_delta,
            memory_signature=memory_signature,
            daily_transit_effect=daily_transit_effect,
            daily_transit_effect_by_category=daily_by_cat,
        )

    bounded_delta, effective_max_delta = apply_bounds(raw_delta, config, shock_active)
    daily_transit_effect = tuple(
        bounded_delta[p] * identity.sensitivity_vector[p] for p in range(NUM_PARAMETERS)
    )

    if transit_effect_history and len(transit_effect_history) > 0:
        window = transit_effect_history[-PHASE_WINDOW_DAYS:]
        n = len(window)
        phase = tuple(sum(w[p] for w in window) / n for p in range(NUM_PARAMETERS))
        effective_transit = tuple(
            PHASE_DAILY_WEIGHT * daily_transit_effect[p] + PHASE_SMOOTH_WEIGHT * phase[p]
            for p in range(NUM_PARAMETERS)
        )
        params_final, axis_final = assemble_state(
            identity.base_vector,
            identity.sensitivity_vector,
            bounded_delta,
            memory_delta,
            precomputed_transit_effect=effective_transit,
        )
    else:
        params_final, axis_final = assemble_state(
            identity.base_vector,
            identity.sensitivity_vector,
            bounded_delta,
            memory_delta,
        )

    return ReplayResult(
        params_final=params_final,
        axis_final=axis_final,
        identity_hash=identity.identity_hash,
        configuration_hash=config_hash,
        injected_time_utc=injected_iso,
        transit_signature=_transit_signature_hash(transit_data),
        shock_flag=shock_active,
        effective_max_delta=effective_max_delta,
        memory_signature=memory_signature,
        daily_transit_effect=daily_transit_effect,
        daily_transit_effect_by_category=None,
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
