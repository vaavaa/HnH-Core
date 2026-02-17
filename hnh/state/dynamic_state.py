"""
Dynamic State: identity_hash, injected timestamp, transit_signature,
relational_modifier, final_behavior_vector, active_modifiers.
No Identity mutation; rejects relational values outside [0, 1].
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from hnh.core.parameters import BehavioralVector
from hnh.state.modulation import (
    DIMENSION_NAMES,
    aggregate_aspect_modifiers,
    merge_vectors,
)

# Optional astrology: avoid import if not used
try:
    from hnh.astrology import aspects as asp
    from hnh.astrology import transits as tr
except ImportError:
    asp = None  # type: ignore[assignment]
    tr = None  # type: ignore[assignment]


class DynamicState(BaseModel):
    """
    One state snapshot: deterministic output for given identity + time + modifiers.
    Spec: identity_hash, timestamp (injected), transit_signature, relational_modifier,
    final_behavior_vector, active_modifiers.
    """

    identity_hash: str
    injected_time: str  # ISO UTC
    seed: int | None = None
    transit_signature: dict[str, Any] | None = None
    relational_modifier: dict[str, float] | None = None
    final_behavior_vector: BehavioralVector
    active_modifiers: dict[str, Any]  # e.g. {"transit_delta": {...}, "relational": ...}

    model_config = {"frozen": True}


def compute_dynamic_state(
    identity_hash: str,
    base_behavior_vector: BehavioralVector,
    injected_time: datetime,
    seed: int | None = None,
    natal_positions: dict[str, Any] | None = None,
    relational_modifier: dict[str, float] | None = None,
) -> DynamicState:
    """
    Build DynamicState from identity snapshot and injected time.
    No system clock; no Identity mutation. Rejects relational_modifier outside [0, 1].
    """
    injected_time_iso = injected_time.isoformat()
    transit_signature: dict[str, Any] | None = None
    transit_delta: dict[str, float] = {d: 0.0 for d in DIMENSION_NAMES}

    if tr is not None and natal_positions is not None:
        transit_signature = tr.compute_transit_signature(injected_time, natal_positions)
        aspects = transit_signature.get("aspects_to_natal", [])
        transit_delta = aggregate_aspect_modifiers(aspects)

    final_vector = merge_vectors(base_behavior_vector, transit_delta, relational_modifier)
    active_modifiers: dict[str, Any] = {"transit_delta": transit_delta}
    if relational_modifier is not None:
        active_modifiers["relational"] = relational_modifier

    return DynamicState(
        identity_hash=identity_hash,
        injected_time=injected_time_iso,
        seed=seed,
        transit_signature=transit_signature,
        relational_modifier=relational_modifier,
        final_behavior_vector=final_vector,
        active_modifiers=active_modifiers,
    )
