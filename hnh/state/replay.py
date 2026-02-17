"""
Replay harness: inject seed, time, relational snapshot; no system clock.
Same inputs → identical state output.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from hnh.core.identity import IdentityCore
from hnh.state.dynamic_state import DynamicState, compute_dynamic_state


def run_step(
    identity: IdentityCore,
    injected_time: datetime,
    seed: int | None = None,
    relational_snapshot: dict[str, float] | None = None,
) -> DynamicState:
    """
    Run one deterministic state step. No datetime.now(); all inputs injected.
    Same identity + time + snapshot → identical DynamicState.
    """
    natal_positions: dict[str, Any] | None = None
    if identity.symbolic_input:
        natal_positions = identity.symbolic_input.get("natal_positions")
    return compute_dynamic_state(
        identity_hash=identity.identity_hash,
        base_behavior_vector=identity.base_behavior_vector,
        injected_time=injected_time,
        seed=seed,
        natal_positions=natal_positions,
        relational_modifier=relational_snapshot,
    )
