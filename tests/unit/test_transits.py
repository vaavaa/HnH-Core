"""
T020: Transit determinism — same injected time → identical transit_signature.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hnh.astrology import transits as tr
from hnh.core import natal

pytest.importorskip("swisseph")


def test_same_injected_time_same_transit_signature():
    """T020: Same injected time + same natal → identical transit_signature."""
    dt = datetime(1990, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    natal_pos = natal.build_natal_positions(dt, 55.75, 37.62)
    injected = datetime(2020, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
    sig1 = tr.compute_transit_signature(injected, natal_pos)
    sig2 = tr.compute_transit_signature(injected, natal_pos)
    assert sig1 == sig2
    assert "timestamp_utc" in sig1
    assert "positions" in sig1
    assert "aspects_to_natal" in sig1


def test_different_time_different_signature():
    """Different injected time → different transit_signature."""
    dt = datetime(1990, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    natal_pos = natal.build_natal_positions(dt, 55.75, 37.62)
    t1 = datetime(2020, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2020, 1, 11, 18, 0, 0, tzinfo=timezone.utc)
    sig1 = tr.compute_transit_signature(t1, natal_pos)
    sig2 = tr.compute_transit_signature(t2, natal_pos)
    assert sig1 != sig2
