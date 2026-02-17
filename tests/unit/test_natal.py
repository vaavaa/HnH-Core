"""
T012–T017: Natal reproducibility, datetime/location validation, positions, aspects, natal structure.
Same birth input → identical natal output and stable hash.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import pytest

from hnh.astrology import aspects as asp
from hnh.astrology import ephemeris as eph
from hnh.core import natal


def _natal_hash(natal_positions: dict) -> str:
    """Stable hash of natal_positions structure (deterministic)."""
    payload = json.dumps(natal_positions, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


# --- T012: same birth input → identical natal output and hash ---


def test_same_birth_input_produces_identical_natal_output():
    """T012: Same birth input → identical natal_positions structure."""
    pytest.importorskip("swisseph")
    dt = datetime(1990, 6, 15, 12, 30, 0, tzinfo=timezone.utc)
    lat, lon = 55.75, 37.62
    out1 = natal.build_natal_positions(dt, lat, lon)
    out2 = natal.build_natal_positions(dt, lat, lon)
    assert out1 == out2


def test_same_birth_input_produces_identical_natal_hash():
    """T012: Same birth input → identical hash of natal_positions."""
    pytest.importorskip("swisseph")
    dt = datetime(1990, 6, 15, 12, 30, 0, tzinfo=timezone.utc)
    lat, lon = 55.75, 37.62
    out1 = natal.build_natal_positions(dt, lat, lon)
    out2 = natal.build_natal_positions(dt, lat, lon)
    assert _natal_hash(out1) == _natal_hash(out2)


# --- T013: birth datetime normalization (UTC) ---


def test_normalize_birth_datetime_utc():
    """T013: Normalize birth time to UTC datetime."""
    dt = eph.normalize_birth_datetime_utc(1990, 6, 15, 12, 30, 0)
    assert dt.tzinfo == timezone.utc
    assert dt.year == 1990 and dt.month == 6 and dt.day == 15
    assert dt.hour == 12 and dt.minute == 30 and dt.second == 0


def test_build_natal_accepts_naive_utc():
    """T013: build_natal_positions accepts naive datetime (treated as UTC)."""
    pytest.importorskip("swisseph")
    dt_naive = datetime(1990, 6, 15, 12, 30, 0)  # no tz
    out = natal.build_natal_positions(dt_naive, 0.0, 0.0)
    assert "birth_datetime_utc" in out
    assert "Z" in out["birth_datetime_utc"] or "+00:00" in out["birth_datetime_utc"]


# --- T014: location validation ---


def test_validate_location_accepts_valid():
    """T014: Valid lat/lon passes."""
    eph.validate_location(0.0, 0.0)
    eph.validate_location(55.75, 37.62)
    eph.validate_location(-90.0, 180.0)


def test_validate_location_rejects_lat_out_of_range():
    """T014: Latitude outside [-90, 90] raises."""
    with pytest.raises(ValueError, match="Latitude"):
        eph.validate_location(91.0, 0.0)
    with pytest.raises(ValueError, match="Latitude"):
        eph.validate_location(-91.0, 0.0)


def test_validate_location_rejects_lon_out_of_range():
    """T014: Longitude outside [-180, 180] raises."""
    with pytest.raises(ValueError, match="Longitude"):
        eph.validate_location(0.0, 181.0)
    with pytest.raises(ValueError, match="Longitude"):
        eph.validate_location(0.0, -181.0)


def test_build_natal_rejects_invalid_location():
    """T014: build_natal_positions rejects invalid location (no swisseph needed)."""
    dt = datetime(1990, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="Latitude"):
        natal.build_natal_positions(dt, 100.0, 0.0)
    with pytest.raises(ValueError, match="Longitude"):
        natal.build_natal_positions(dt, 0.0, 200.0)


# --- T015: positions via pyswisseph (covered by build_natal) ---


def test_compute_positions_returns_deterministic_order():
    """T015: compute_positions returns standard planets in fixed order."""
    pytest.importorskip("swisseph")
    jd = eph.datetime_to_julian_utc(datetime(1990, 6, 15, 12, 0, 0, tzinfo=timezone.utc))
    positions = eph.compute_positions(jd)
    names = [p["planet"] for p in positions]
    assert names == ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
    for p in positions:
        assert "longitude" in p
        assert 0 <= p["longitude"] < 360


# --- T016: aspect detection ---


def test_angular_separation():
    """T016: Angular separation 0–180."""
    assert asp.angular_separation(0, 0) == 0
    assert asp.angular_separation(0, 180) == 180
    assert asp.angular_separation(350, 10) == 20


def test_detect_aspects_uses_orb_config():
    """T016: detect_aspects uses OrbConfig orbs."""
    positions = [
        {"planet": "Sun", "longitude": 0.0},
        {"planet": "Moon", "longitude": 90.0},  # square
    ]
    found = asp.detect_aspects(positions)
    # May have Square Sun–Moon
    names = {(a["planet1"], a["planet2"], a["aspect"]) for a in found}
    assert ("Sun", "Moon", "Square") in names or ("Moon", "Sun", "Square") in names


def test_orb_config_defaults():
    """T016: OrbConfig exposes per-aspect orbs."""
    cfg = asp.OrbConfig()
    assert cfg.get_orb("Square") == 7.0
    assert cfg.get_orb("Sextile") == 6.0


# --- T017: deterministic natal_positions structure ---


def test_natal_positions_structure():
    """T017: build_natal_positions returns required keys."""
    pytest.importorskip("swisseph")
    dt = datetime(1990, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    out = natal.build_natal_positions(dt, 55.75, 37.62)
    assert "birth_datetime_utc" in out
    assert "latitude" in out and "longitude" in out
    assert "jd_ut" in out
    assert "positions" in out
    assert "aspects" in out
    assert len(out["positions"]) == 7
    assert all("planet" in p and "longitude" in p for p in out["positions"])
