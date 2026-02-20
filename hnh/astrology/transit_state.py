"""
TransitState: structured output of TransitEngine (Spec 006, contract transit-engine.md).
Single return type per date: stress, raw_delta, bounded_delta.
"""

from __future__ import annotations

from dataclasses import dataclass

from hnh.identity.schema import NUM_PARAMETERS

# Vector32 = tuple[float, ...] length 32
Vector32 = tuple[float, ...]


@dataclass(frozen=True)
class TransitState:
    """
    Single structured output of TransitEngine.state(date, config).
    stress: S_T(t) [0, 1]; raw_delta: before bounds; bounded_delta: for BehavioralCore.
    """

    stress: float
    raw_delta: Vector32
    bounded_delta: Vector32

    def __post_init__(self) -> None:
        if len(self.raw_delta) != NUM_PARAMETERS or len(self.bounded_delta) != NUM_PARAMETERS:
            raise ValueError(f"raw_delta and bounded_delta must have length {NUM_PARAMETERS}")
