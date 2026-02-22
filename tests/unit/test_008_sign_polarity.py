"""T011: SignPolarityEngine (FR-005, FR-006, FR-011, FR-012)."""

import pytest

from hnh.sex.sign_polarity import sign_polarity, sign_polarity_score, DEFAULT_PLANET_WEIGHTS


def test_sign_polarity_mapping():
    """FR-011: +1 Aries,Gemini,Leo,Libra,Sagittarius,Aquarius; -1 else."""
    assert sign_polarity(0) == 1   # Aries
    assert sign_polarity(1) == -1  # Taurus
    assert sign_polarity(2) == 1   # Gemini
    assert sign_polarity(10) == 1  # Aquarius
    assert sign_polarity(11) == -1 # Pisces


def test_sign_polarity_score_weighted():
    """FR-006: weighted average over planets with known sign."""
    # Sun=2, Moon=2; Sun sign 0 (+1), Moon sign 1 (-1) -> (2*1 + 2*(-1))/4 = 0
    planet_signs = {"Sun": 0, "Moon": 1}
    assert sign_polarity_score(planet_signs) == 0.0
    # All positive signs -> +1
    assert sign_polarity_score({"Sun": 0, "Moon": 2}) == 1.0
    # All negative -> -1
    assert sign_polarity_score({"Sun": 1, "Moon": 3}) == -1.0


def test_sign_polarity_score_no_planets_raises():
    """Infer path: no planet with sign -> ValueError (fail-fast)."""
    with pytest.raises(ValueError, match="no planet with known sign"):
        sign_polarity_score({})
