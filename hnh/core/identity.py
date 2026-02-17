"""
Identity Core: immutable, serializable, hashable.
At most one Core per identity_id; duplicate creation raises.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, model_validator

from hnh.core.parameters import BehavioralVector

# Registry for duplicate identity_id check (in-memory, process scope)
_registry: set[str] = set()


class IdentityCore(BaseModel):
    """
    Identity Core: immutable after creation.
    identity_id: unique; second creation with same id → ValueError.
    base_traits: produces base_behavior_vector (seven dimensions [0, 1]).
    optional symbolic_input: e.g. natal metadata; must map to measurable params.
    """

    identity_id: str
    base_traits: BehavioralVector
    symbolic_input: dict[str, Any] | None = None

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _register_and_reject_duplicate(self) -> IdentityCore:
        if self.identity_id in _registry:
            msg = f"Identity Core with identity_id={self.identity_id!r} already exists"
            raise ValueError(msg)
        _registry.add(self.identity_id)
        return self

    @property
    def base_behavior_vector(self) -> BehavioralVector:
        """Base behavioral vector (spec: seven dimensions, 0–1)."""
        return self.base_traits

    @property
    def identity_hash(self) -> str:
        """Stable, deterministic hash of identity."""
        payload = {
            "identity_id": self.identity_id,
            "base_behavior_vector": self.base_traits.to_dict(),
            "symbolic_input": self.symbolic_input,
        }
        blob = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    def __hash__(self) -> int:
        return hash((self.identity_id, self.identity_hash))
