"""
T021: Mapping determinism — identical natal + transit → identical behavioral vector.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hnh.astrology import transits as tr
from hnh.core import natal
from hnh.core.parameters import BehavioralVector
from hnh.state import modulation

pytest.importorskip("swisseph")


def test_identical_natal_and_transit_same_behavioral_vector():
    """T021: Same natal + same transit → same final behavioral vector from merge."""
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.4,
        verbosity=0.6,
        correction_rate=0.3,
        humor_level=0.5,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    dt = datetime(1990, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    natal_pos = natal.build_natal_positions(dt, 55.75, 37.62)
    injected = datetime(2020, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
    sig = tr.compute_transit_signature(injected, natal_pos)
    aspects = sig.get("aspects_to_natal", [])
    delta = modulation.aggregate_aspect_modifiers(aspects)
    out1 = modulation.merge_vectors(base, delta, None)
    out2 = modulation.merge_vectors(base, delta, None)
    assert out1.to_dict() == out2.to_dict()


def test_merge_rejects_relational_modifier_out_of_range():
    """T027/FR-006: Relational modifier outside [0, 1] is rejected."""
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.5,
        verbosity=0.5,
        correction_rate=0.5,
        humor_level=0.5,
        challenge_intensity=0.5,
        pacing=0.5,
    )
    bad = {"warmth": 1.5, "strictness": 0.5, "verbosity": 0.5, "correction_rate": 0.5,
           "humor_level": 0.5, "challenge_intensity": 0.5, "pacing": 0.5}
    with pytest.raises(ValueError, match="Relational modifier.*[0, 1]"):
        modulation.merge_vectors(base, {}, bad)
