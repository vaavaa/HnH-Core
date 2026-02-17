"""BehavioralVector validation: reject NaN, inf, out-of-range (T008)."""

from __future__ import annotations

import math

import pytest

from hnh.core.parameters import BehavioralVector

VALID = dict(
    warmth=0.5,
    strictness=0.3,
    verbosity=0.6,
    correction_rate=0.4,
    humor_level=0.5,
    challenge_intensity=0.3,
    pacing=0.5,
)


def test_reject_nan() -> None:
    """Reject NaN in any dimension."""
    with pytest.raises(ValueError, match="NaN|finite"):
        BehavioralVector(**{**VALID, "warmth": float("nan")})


def test_reject_inf() -> None:
    """Reject inf in any dimension."""
    with pytest.raises(ValueError, match="finite"):
        BehavioralVector(**{**VALID, "strictness": math.inf})


def test_reject_above_one() -> None:
    """Reject value > 1.0."""
    with pytest.raises(ValueError, match="0.0, 1.0"):
        BehavioralVector(**{**VALID, "verbosity": 1.5})


def test_reject_below_zero() -> None:
    """Reject value < 0.0."""
    with pytest.raises(ValueError, match="0.0, 1.0"):
        BehavioralVector(**{**VALID, "pacing": -0.1})


def test_accept_boundaries() -> None:
    """Accept 0.0 and 1.0."""
    BehavioralVector(**{**VALID, "warmth": 0.0, "strictness": 1.0})
