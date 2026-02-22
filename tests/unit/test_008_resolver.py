"""T017: SexResolver infer — determinism, tie-break, insufficient data fail-fast."""

import pytest

from hnh.sex.resolver import resolve_sex, resolve_sex_explicit, _infer_sex, InsufficientNatalDataError
from hnh.sex.identity_hash import identity_hash_for_tie_break, tie_break_parity


class _MockNatal:
    """Minimal natal with planets (name, sign_index)."""

    def __init__(self, positions: list[dict]):
        self._positions = positions

    @property
    def planets(self):
        from types import SimpleNamespace
        return [SimpleNamespace(name=p.get("planet", ""), sign_index=p.get("sign", 0)) for p in self._positions]

    def to_natal_data(self):
        return {"positions": self._positions}


def test_infer_determinism_same_natal_same_sex():
    """Same birth_data + natal -> same inferred sex (determinism)."""
    birth_data = {"positions": [{"planet": "Sun", "longitude": 90.0}], "sex_mode": "infer"}
    natal = _MockNatal([{"planet": "Sun", "longitude": 90.0, "sign": 2}])  # Gemini
    r1 = resolve_sex(birth_data, natal=natal)
    r2 = resolve_sex(birth_data, natal=natal)
    assert r1 == r2
    assert r1 in ("male", "female")


def test_infer_tie_break_stable():
    """Tie-break: same identity_hash digest -> same sex."""
    # S in [-T, T] for same digest -> same outcome
    birth_data = {"a": 1, "sex_mode": "infer"}
    digest = identity_hash_for_tie_break(birth_data)
    natal = _MockNatal([{"planet": "Sun", "sign": 0}])
    r1 = resolve_sex(birth_data, natal=natal, identity_hash_digest=digest)
    r2 = resolve_sex(birth_data, natal=natal, identity_hash_digest=digest)
    assert r1 == r2


def test_infer_insufficient_data_no_sun_fail_fast():
    """Insufficient natal data (no Sun sign) -> fail-fast, no fallback to None."""
    birth_data = {"sex_mode": "infer"}
    natal = _MockNatal([{"planet": "Moon", "sign": 1}])  # no Sun
    with pytest.raises(InsufficientNatalDataError, match="Sun"):
        resolve_sex(birth_data, natal=natal)


def test_infer_insufficient_data_no_planets_fail_fast():
    """No planets with sign -> fail-fast."""
    birth_data = {"sex_mode": "infer"}
    natal = _MockNatal([])
    with pytest.raises((InsufficientNatalDataError, ValueError), match="Sun|no planet"):
        resolve_sex(birth_data, natal=natal)


def test_infer_explicit_unchanged():
    """Explicit mode unchanged: resolve_sex with sex_mode=explicit returns validate_sex."""
    assert resolve_sex({"sex": "male"}) == "male"
    assert resolve_sex({}) is None
    assert resolve_sex({"sex": "female"}) == "female"
