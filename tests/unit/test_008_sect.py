"""T011: SectEngine (FR-007, FR-013)."""

import pytest

from hnh.sex.sect import sect_score_from_altitude, sect_score_from_house, sect_score


def test_sect_from_altitude():
    """Preferred: altitude > 0 -> +1, < 0 -> -1, == 0 -> 0."""
    assert sect_score_from_altitude(1.0) == 1
    assert sect_score_from_altitude(-1.0) == -1
    assert sect_score_from_altitude(0.0) == 0
    assert sect_score_from_altitude(None) == 0


def test_sect_from_house():
    """Fallback: houses 7-12 day (+1), 1-6 night (-1)."""
    assert sect_score_from_house(7) == 1
    assert sect_score_from_house(12) == 1
    assert sect_score_from_house(1) == -1
    assert sect_score_from_house(6) == -1
    assert sect_score_from_house(None) == 0


def test_sect_score_prefers_altitude():
    """Altitude takes precedence over house."""
    assert sect_score(sun_altitude_deg=1.0, sun_house=1) == 1
    assert sect_score(sun_altitude_deg=-1.0, sun_house=12) == -1
