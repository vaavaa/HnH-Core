"""
Hierarchical personality schema: 8 axes × 4 sub-parameters (32 total).
Canonical ordering, deterministic index mapping. Spec 002.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, field_validator, model_validator

# --- T1.1 Axis & Parameter Registry ----------------------------------------------------------
# Spec §7: 8 axes, 32 sub-parameters. Order is canonical and stable.

AXES: tuple[str, ...] = (
    "emotional_tone",           # 0
    "stability_regulation",     # 1
    "cognitive_style",         # 2
    "structure_discipline",     # 3
    "communication_style",     # 4
    "teaching_style",           # 5
    "power_boundaries",        # 6
    "motivation_drive",        # 7
)

# 32 parameters: (axis_index, param_name). Global index = axis * 4 + sub.
_PARAMETER_LIST: list[tuple[int, str]] = [
    (0, "warmth"),
    (0, "empathy"),
    (0, "patience"),
    (0, "emotional_intensity"),
    (1, "stability"),
    (1, "reactivity"),
    (1, "resilience"),
    (1, "stress_response"),
    (2, "analytical_depth"),
    (2, "abstraction_level"),
    (2, "detail_orientation"),
    (2, "big_picture_focus"),
    (3, "structure_preference"),
    (3, "consistency"),
    (3, "rule_adherence"),
    (3, "planning_bias"),
    (4, "verbosity"),
    (4, "directness"),
    (4, "questioning_frequency"),
    (4, "explanation_bias"),
    (5, "correction_intensity"),
    (5, "challenge_level"),
    (5, "encouragement_level"),
    (5, "pacing"),
    (6, "authority_presence"),
    (6, "dominance"),
    (6, "tolerance_for_errors"),
    (6, "conflict_tolerance"),
    (7, "ambition"),
    (7, "curiosity"),
    (7, "initiative"),
    (7, "persistence"),
]

PARAMETERS: tuple[str, ...] = tuple(p[1] for p in _PARAMETER_LIST)
NUM_AXES: int = 8
NUM_PARAMETERS: int = 32


def get_axis_index(axis_name: str) -> int:
    """Return canonical axis index 0..7. Raises ValueError if unknown."""
    try:
        return AXES.index(axis_name)
    except ValueError:
        raise ValueError(f"Unknown axis: {axis_name!r}") from None


def get_parameter_index(param_name: str) -> int:
    """Return canonical parameter index 0..31. Raises ValueError if unknown."""
    try:
        return PARAMETERS.index(param_name)
    except ValueError:
        raise ValueError(f"Unknown parameter: {param_name!r}") from None


def get_parameter_axis_index(param_index: int) -> int:
    """Return axis index (0..7) for the given parameter index (0..31)."""
    if not 0 <= param_index < NUM_PARAMETERS:
        raise ValueError(f"Parameter index must be 0..{NUM_PARAMETERS - 1}, got {param_index}")
    return _PARAMETER_LIST[param_index][0]


class PersonalityAxis(BaseModel):
    """Top-level dimension: index 0..7 and canonical name. Immutable."""

    index: int
    name: str

    model_config = {"frozen": True}

    @field_validator("index")
    @classmethod
    def _index_range(cls, v: int) -> int:
        if not 0 <= v < NUM_AXES:
            raise ValueError(f"Axis index must be 0..{NUM_AXES - 1}, got {v}")
        return v

    @field_validator("name")
    @classmethod
    def _name_canonical(cls, v: str) -> str:
        if v not in AXES:
            raise ValueError(f"Unknown axis: {v!r}")
        return v


# --- T1.2 PersonalityParameter ---------------------------------------------------------------


def _clamp_0_1(v: float) -> float:
    if not (0.0 <= v <= 1.0):
        raise ValueError(f"Value must be in [0.0, 1.0], got {v}")
    return v


class PersonalityParameter(BaseModel):
    """
    Single sub-parameter: name, axis, base_value and sensitivity in [0, 1].
    Immutable.
    """

    name: str
    axis: str
    base_value: float
    sensitivity: float

    model_config = {"frozen": True}

    @field_validator("base_value", "sensitivity")
    @classmethod
    def _in_0_1(cls, v: float) -> float:
        return _clamp_0_1(v)

    @field_validator("name")
    @classmethod
    def _name_canonical(cls, v: str) -> str:
        if v not in PARAMETERS:
            raise ValueError(f"Unknown parameter name: {v!r}")
        return v

    @field_validator("axis")
    @classmethod
    def _axis_canonical(cls, v: str) -> str:
        if v not in AXES:
            raise ValueError(f"Unknown axis: {v!r}")
        return v


# --- T1.3 IdentityCore (v0.2) ---------------------------------------------------------------
# identity_id, natal_data (optional), base_vector[32], sensitivity_vector[32], identity_hash


_registry: set[str] = set()


class IdentityCore(BaseModel):
    """
    Identity Core v0.2: immutable.
    base_vector and sensitivity_vector: 32 floats each, [0, 1].
    When natal_data is absent, caller MUST supply base_vector and sensitivity_vector;
    no default values. One Core per identity_id (duplicate raises).
    """

    identity_id: str
    natal_data: dict[str, Any] | None = None
    base_vector: tuple[float, ...]
    sensitivity_vector: tuple[float, ...]

    model_config = {"frozen": True}

    @field_validator("base_vector", "sensitivity_vector")
    @classmethod
    def _length_32(cls, v: tuple[float, ...]) -> tuple[float, ...]:
        if len(v) != NUM_PARAMETERS:
            raise ValueError(f"Vector length must be {NUM_PARAMETERS}, got {len(v)}")
        return v

    @field_validator("base_vector", "sensitivity_vector")
    @classmethod
    def _values_0_1(cls, v: tuple[float, ...]) -> tuple[float, ...]:
        for i, x in enumerate(v):
            if not (0.0 <= x <= 1.0):
                raise ValueError(f"Vector[{i}] must be in [0, 1], got {x}")
        return v

    @model_validator(mode="after")
    def _register_and_reject_duplicate(self) -> IdentityCore:
        if self.identity_id in _registry:
            raise ValueError(
                f"Identity Core with identity_id={self.identity_id!r} already exists"
            )
        _registry.add(self.identity_id)
        return self

    @property
    def identity_hash(self) -> str:
        """Deterministic hash: identity_id + base_vector + sensitivity_vector."""
        payload = {
            "identity_id": self.identity_id,
            "base_vector": list(self.base_vector),
            "sensitivity_vector": list(self.sensitivity_vector),
        }
        blob = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    def __hash__(self) -> int:
        return hash((self.identity_id, self.identity_hash))
