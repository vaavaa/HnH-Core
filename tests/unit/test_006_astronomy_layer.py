"""
T004: Unit tests for 006 astronomy layer — Planet, Aspect, NatalChart.
Planet: sign from longitude; Aspect: angle, type, tension_score; NatalChart: immutability, determinism.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hnh.astrology.aspect_model import Aspect, aspect_from_dict
from hnh.astrology.natal_chart import NatalChart
from hnh.astrology.planet import Planet, ZODIAC_SIGNS, longitude_to_sign_index


# --- Planet: sign from longitude ---


def test_planet_sign_index_from_longitude():
    """Planet: sign index 0..11 from longitude (30° per sign)."""
    p0 = Planet(name="Sun", longitude=0.0)
    assert p0.sign_index == 0
    assert p0.sign == "Aries"
    p15 = Planet(name="Sun", longitude=15.0)
    assert p15.sign_index == 0
    p30 = Planet(name="Moon", longitude=30.0)
    assert p30.sign_index == 1
    assert p30.sign == "Taurus"
    p359 = Planet(name="Mars", longitude=359.0)
    assert p359.sign_index == 11
    assert p359.sign == "Pisces"


def test_planet_immutable():
    """Planet is frozen (immutable)."""
    p = Planet(name="Sun", longitude=90.0)
    with pytest.raises(Exception):
        p.longitude = 100.0  # type: ignore[misc]
    with pytest.raises(Exception):
        p.name = "Moon"  # type: ignore[misc]


def test_longitude_to_sign_index_wraps():
    """longitude_to_sign_index normalizes to [0, 360) and maps to 0..11."""
    assert longitude_to_sign_index(0) == 0
    assert longitude_to_sign_index(360) == 0
    assert longitude_to_sign_index(-30) == 11
    assert longitude_to_sign_index(180) == 6


# --- Aspect: angle, type, tension_score ---


def test_aspect_tension_score_hard():
    """Aspect: tension_score > 0 for hard aspects (Conjunction, Opposition, Square)."""
    # Exact conjunction: separation 0, angle 0
    a = Aspect(planet_a="Sun", planet_b="Moon", angle=0.0, type="Conjunction", separation=0.0)
    assert a.tension_score() > 0
    # Opposition: separation 180
    b = Aspect(planet_a="Sun", planet_b="Moon", angle=180.0, type="Opposition", separation=180.0)
    assert b.tension_score() > 0
    # Square
    c = Aspect(planet_a="Sun", planet_b="Mars", angle=90.0, type="Square", separation=90.0)
    assert c.tension_score() > 0


def test_aspect_tension_score_soft_zero():
    """Aspect: tension_score = 0 for soft aspects (Trine, Sextile)."""
    a = Aspect(planet_a="Sun", planet_b="Venus", angle=120.0, type="Trine", separation=120.0)
    assert a.tension_score() == 0.0
    b = Aspect(planet_a="Sun", planet_b="Mercury", angle=60.0, type="Sextile", separation=60.0)
    assert b.tension_score() == 0.0


def test_aspect_from_dict():
    """Aspect: build from legacy dict."""
    d = {"planet1": "Sun", "planet2": "Moon", "aspect": "Conjunction", "angle": 0, "separation": 2.5}
    a = aspect_from_dict(d)
    assert a.planet_a == "Sun"
    assert a.planet_b == "Moon"
    assert a.type == "Conjunction"
    assert a.separation == 2.5


# --- NatalChart: immutability, determinism (variant B) ---


def test_natal_chart_from_positions_immutable():
    """NatalChart: planets and aspects stored as tuples (immutable)."""
    birth_data = {
        "positions": [
            {"planet": "Sun", "longitude": 90.0},
            {"planet": "Moon", "longitude": 120.0},
        ],
    }
    chart = NatalChart.from_birth_data(birth_data)
    assert isinstance(chart.planets, tuple)
    assert isinstance(chart.aspects, tuple)
    assert len(chart.planets) == 2
    assert chart.planets[0].name == "Sun"
    assert chart.planets[0].longitude == 90.0


def test_natal_chart_determinism_same_input():
    """NatalChart: same birth_data → same chart (determinism)."""
    birth_data = {
        "positions": [
            {"planet": "Sun", "longitude": 45.0},
            {"planet": "Moon", "longitude": 90.0},
        ],
    }
    c1 = NatalChart.from_birth_data(birth_data)
    c2 = NatalChart.from_birth_data(birth_data)
    assert c1.planets == c2.planets
    assert c1.aspects == c2.aspects
    assert c1.to_natal_data()["positions"][0]["longitude"] == c2.to_natal_data()["positions"][0]["longitude"]


def test_natal_chart_to_natal_data_has_positions_and_aspects():
    """NatalChart: to_natal_data() returns positions + aspects for sensitivity/replay."""
    birth_data = {
        "positions": [
            {"planet": "Sun", "longitude": 100.0, "house": 4},
        ],
    }
    chart = NatalChart.from_birth_data(birth_data)
    data = chart.to_natal_data()
    assert "positions" in data
    assert "aspects" in data
    assert len(data["positions"]) == 1
    assert data["positions"][0]["planet"] == "Sun"
    assert data["positions"][0]["sign"] == 3  # Cancer
    assert "angular_strength" in data["positions"][0]


def test_natal_chart_variant_a_if_ephemeris_available():
    """NatalChart: variant A (datetime_utc, lat, lon) builds from ephemeris when available."""
    pytest.importorskip("swisseph")
    birth_data = {
        "datetime_utc": "1990-06-15T12:30:00Z",
        "lat": 55.75,
        "lon": 37.62,
    }
    chart = NatalChart.from_birth_data(birth_data)
    assert len(chart.planets) >= 1
    assert isinstance(chart.planets, tuple)
    data = chart.to_natal_data()
    assert "positions" in data
    assert any(p.get("planet") == "Sun" for p in data["positions"])
