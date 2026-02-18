"""Unit tests for state assembler (Spec 002 Phase 5)."""

from __future__ import annotations

import pytest

from hnh.identity.schema import NUM_PARAMETERS, NUM_AXES
from hnh.state.assembler import assemble_state


def test_assemble_state_output_shape() -> None:
    """params_final length 32, axis_final length 8."""
    base = (0.5,) * NUM_PARAMETERS
    sens = (0.5,) * NUM_PARAMETERS
    bounded = (0.0,) * NUM_PARAMETERS
    params_final, axis_final = assemble_state(base, sens, bounded)
    assert len(params_final) == NUM_PARAMETERS
    assert len(axis_final) == NUM_AXES


def test_assemble_state_clamp01() -> None:
    """Final values in [0, 1]."""
    base = (0.1,) * NUM_PARAMETERS
    sens = (1.0,) * NUM_PARAMETERS
    bounded = (0.5,) * NUM_PARAMETERS  # 0.1 + 0.5 = 0.6 ok
    params_final, _ = assemble_state(base, sens, bounded)
    assert all(0.0 <= v <= 1.0 for v in params_final)


def test_assemble_state_deterministic() -> None:
    """Same inputs → same outputs."""
    base = (0.4,) * NUM_PARAMETERS
    sens = (0.6,) * NUM_PARAMETERS
    bounded = (0.02,) * NUM_PARAMETERS
    a_params, a_axis = assemble_state(base, sens, bounded)
    b_params, b_axis = assemble_state(base, sens, bounded)
    assert a_params == b_params
    assert a_axis == b_axis


def test_axis_aggregation_mean() -> None:
    """axis_final = mean of 4 sub-parameters per axis."""
    base = (0.0,) * NUM_PARAMETERS
    sens = (1.0,) * NUM_PARAMETERS
    bounded = [0.0] * NUM_PARAMETERS
    bounded[0] = 0.1
    bounded[1] = 0.2
    bounded[2] = 0.3
    bounded[3] = 0.4
    params_final, axis_final = assemble_state(base, sens, tuple(bounded))
    assert abs(axis_final[0] - (0.1 + 0.2 + 0.3 + 0.4) / 4.0) < 1e-9


def test_assemble_state_rejects_wrong_length() -> None:
    """Wrong vector lengths raise ValueError."""
    base = (0.5,) * NUM_PARAMETERS
    sens = (0.5,) * NUM_PARAMETERS
    bounded = (0.0,) * NUM_PARAMETERS
    with pytest.raises(ValueError, match="Vectors must have length"):
        assemble_state((0.5,) * 31, sens, bounded)
    with pytest.raises(ValueError, match="memory_delta length must be"):
        assemble_state(base, sens, bounded, memory_delta=(0.0,) * 31)
