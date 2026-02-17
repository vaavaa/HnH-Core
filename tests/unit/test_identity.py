"""Unit tests for Identity Core (US1): creation, base vector, immutability, duplicate rejection."""

from __future__ import annotations

import pytest

from hnh.core.identity import IdentityCore
from hnh.core.parameters import BehavioralVector


def test_identity_core_same_inputs_same_vector() -> None:
    """Same inputs → identical base_behavior_vector (T010)."""
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.2,
        verbosity=0.8,
        correction_rate=0.3,
        humor_level=0.6,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    core1 = IdentityCore(identity_id="id-1", base_traits=base)
    core2 = IdentityCore(identity_id="id-2", base_traits=base)
    assert core1.base_behavior_vector == core2.base_behavior_vector
    assert core1.base_behavior_vector.to_dict() == base.to_dict()


def test_identity_core_immutable_and_serializable_hashable() -> None:
    """Identity Core is immutable, serializable, hashable (T011)."""
    base = BehavioralVector(
        warmth=0.1,
        strictness=0.9,
        verbosity=0.2,
        correction_rate=0.3,
        humor_level=0.4,
        challenge_intensity=0.5,
        pacing=0.6,
    )
    core = IdentityCore(identity_id="imm-1", base_traits=base)
    with pytest.raises(Exception):  # pydantic ValidationError or AttributeError
        core.base_behavior_vector = base  # type: ignore[misc]
    hash(core)
    d = core.model_dump()
    assert d["identity_id"] == "imm-1"
    assert "base_traits" in d
    assert core.base_behavior_vector.to_dict() == d["base_traits"]


def test_identity_core_duplicate_id_rejected() -> None:
    """Creating a second Core with same identity_id must fail (T011)."""
    from hnh.core.identity import _registry

    _registry.clear()
    base = BehavioralVector(
        warmth=0.0,
        strictness=0.0,
        verbosity=0.0,
        correction_rate=0.0,
        humor_level=0.0,
        challenge_intensity=0.0,
        pacing=0.0,
    )
    IdentityCore(identity_id="dup-1", base_traits=base)
    with pytest.raises(ValueError, match="already exists"):
        IdentityCore(identity_id="dup-1", base_traits=base)
    _registry.clear()
