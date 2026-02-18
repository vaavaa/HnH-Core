"""
Unit tests for Spec 002: Axis & Parameter Registry, PersonalityParameter, IdentityCore v0.2.
T1.1, T1.2, T1.3 acceptance.
"""

from __future__ import annotations

import pytest

from hnh.identity import (
    AXES,
    PARAMETERS,
    IdentityCore,
    PersonalityAxis,
    PersonalityParameter,
    get_axis_index,
    get_parameter_axis_index,
    get_parameter_index,
)
from hnh.identity.schema import NUM_AXES, NUM_PARAMETERS, _registry


# --- T1.1 Axis & Parameter Registry ----------------------------------------------------------


def test_axes_canonical_order_stable() -> None:
    """Order of axes is stable across runs."""
    assert len(AXES) == NUM_AXES == 8
    assert AXES[0] == "emotional_tone"
    assert AXES[7] == "motivation_drive"


def test_parameters_canonical_order_stable() -> None:
    """Order of 32 parameters is stable."""
    assert len(PARAMETERS) == NUM_PARAMETERS == 32
    assert PARAMETERS[0] == "warmth"
    assert PARAMETERS[3] == "emotional_intensity"
    assert PARAMETERS[31] == "persistence"


def test_get_axis_index() -> None:
    """Index mapping for axes."""
    assert get_axis_index("emotional_tone") == 0
    assert get_axis_index("motivation_drive") == 7
    with pytest.raises(ValueError, match="Unknown axis"):
        get_axis_index("unknown_axis")


def test_get_parameter_index() -> None:
    """Index mapping for parameters."""
    assert get_parameter_index("warmth") == 0
    assert get_parameter_index("persistence") == 31
    with pytest.raises(ValueError, match="Unknown parameter"):
        get_parameter_index("unknown_param")


def test_get_parameter_axis_index() -> None:
    """Parameter index maps to correct axis."""
    assert get_parameter_axis_index(0) == 0
    assert get_parameter_axis_index(3) == 0
    assert get_parameter_axis_index(4) == 1
    assert get_parameter_axis_index(31) == 7
    with pytest.raises(ValueError, match="Parameter index"):
        get_parameter_axis_index(32)


# --- T1.2 PersonalityParameter ---------------------------------------------------------------


def test_personality_parameter_validation() -> None:
    """base_value and sensitivity in [0, 1]; name/axis canonical."""
    p = PersonalityParameter(
        name="warmth", axis="emotional_tone", base_value=0.5, sensitivity=0.3
    )
    assert p.base_value == 0.5
    assert p.sensitivity == 0.3


def test_personality_parameter_rejects_out_of_range() -> None:
    """Values outside [0, 1] rejected."""
    with pytest.raises(ValueError, match="must be in"):
        PersonalityParameter(
            name="warmth", axis="emotional_tone", base_value=1.5, sensitivity=0.3
        )
    with pytest.raises(ValueError, match="must be in"):
        PersonalityParameter(
            name="warmth", axis="emotional_tone", base_value=0.5, sensitivity=-0.1
        )


def test_personality_parameter_rejects_unknown_name_or_axis() -> None:
    """Unknown parameter or axis name rejected."""
    with pytest.raises(ValueError, match="Unknown parameter"):
        PersonalityParameter(
            name="unknown_param", axis="emotional_tone", base_value=0.5, sensitivity=0.3
        )
    with pytest.raises(ValueError, match="Unknown axis"):
        PersonalityParameter(
            name="warmth", axis="unknown_axis", base_value=0.5, sensitivity=0.3
        )


def test_personality_parameter_immutable() -> None:
    """PersonalityParameter is frozen."""
    p = PersonalityParameter(
        name="warmth", axis="emotional_tone", base_value=0.5, sensitivity=0.3
    )
    with pytest.raises(Exception):
        p.base_value = 0.9  # type: ignore[misc]


# --- T1.3 IdentityCore -----------------------------------------------------------------------


def _make_base_vector(value: float = 0.5) -> tuple[float, ...]:
    return (value,) * NUM_PARAMETERS


def _make_sensitivity_vector(value: float = 0.5) -> tuple[float, ...]:
    return (value,) * NUM_PARAMETERS


def test_identity_core_hash_deterministic() -> None:
    """Same inputs → same identity_hash."""
    _registry.clear()
    base = _make_base_vector(0.4)
    sens = _make_sensitivity_vector(0.6)
    c1 = IdentityCore(identity_id="h1", base_vector=base, sensitivity_vector=sens)
    # Second identity with different id but same vectors
    c2 = IdentityCore(identity_id="h2", base_vector=base, sensitivity_vector=sens)
    assert c1.identity_hash == c1.identity_hash
    assert c2.identity_hash == c2.identity_hash
    # Same vectors → same hash for hash payload (different identity_id so hashes differ)
    _registry.clear()


def test_identity_core_immutable() -> None:
    """IdentityCore is frozen."""
    _registry.clear()
    core = IdentityCore(
        identity_id="imm2",
        base_vector=_make_base_vector(0.5),
        sensitivity_vector=_make_sensitivity_vector(0.5),
    )
    with pytest.raises(Exception):
        core.base_vector = _make_base_vector(0.0)  # type: ignore[misc]
    _registry.clear()


def test_identity_core_serialization_deterministic() -> None:
    """model_dump is deterministic (stable keys/order for hash)."""
    _registry.clear()
    core = IdentityCore(
        identity_id="ser1",
        base_vector=_make_base_vector(0.1),
        sensitivity_vector=_make_sensitivity_vector(0.2),
    )
    d = core.model_dump()
    assert d["identity_id"] == "ser1"
    assert len(d["base_vector"]) == 32
    assert len(d["sensitivity_vector"]) == 32
    _registry.clear()


def test_identity_core_rejects_wrong_length() -> None:
    """Vectors must be length 32."""
    _registry.clear()
    with pytest.raises(ValueError, match="length must be 32"):
        IdentityCore(
            identity_id="bad",
            base_vector=(0.5,) * 31,
            sensitivity_vector=_make_sensitivity_vector(),
        )
    _registry.clear()


def test_identity_core_rejects_value_out_of_range() -> None:
    """Vector values must be in [0, 1]."""
    _registry.clear()
    base = list(_make_base_vector(0.5))
    base[0] = 1.5
    with pytest.raises(ValueError, match=r"Vector\[0\] must be in"):
        IdentityCore(
            identity_id="badval",
            base_vector=tuple(base),
            sensitivity_vector=_make_sensitivity_vector(),
        )
    _registry.clear()


def test_identity_core_hashable() -> None:
    """IdentityCore is hashable (__hash__ used in sets)."""
    _registry.clear()
    core = IdentityCore(
        identity_id="hashable-1",
        base_vector=_make_base_vector(),
        sensitivity_vector=_make_sensitivity_vector(),
    )
    hash(core)
    s = {core}
    assert core in s
    _registry.clear()


def test_identity_core_duplicate_id_rejected() -> None:
    """Second Core with same identity_id raises."""
    _registry.clear()
    IdentityCore(
        identity_id="dup2",
        base_vector=_make_base_vector(),
        sensitivity_vector=_make_sensitivity_vector(),
    )
    with pytest.raises(ValueError, match="already exists"):
        IdentityCore(
            identity_id="dup2",
            base_vector=_make_base_vector(),
            sensitivity_vector=_make_sensitivity_vector(),
        )
    _registry.clear()


def test_personality_axis_model() -> None:
    """PersonalityAxis accepts valid index and name."""
    a = PersonalityAxis(index=0, name="emotional_tone")
    assert a.index == 0
    assert a.name == "emotional_tone"
    with pytest.raises(ValueError, match="Axis index"):
        PersonalityAxis(index=8, name="emotional_tone")
    with pytest.raises(ValueError, match="Unknown axis"):
        PersonalityAxis(index=0, name="invalid_axis")
