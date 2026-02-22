"""T013: Invalid sex -> fail-fast (FR-001); sex_mode resolution."""

import pytest

from hnh.sex.validation import validate_sex
from hnh.sex.resolution import resolve_sex_mode


def test_validate_sex_valid():
    assert validate_sex({}) is None
    assert validate_sex({"sex": "male"}) == "male"
    assert validate_sex({"sex": "female"}) == "female"
    assert validate_sex({"sex": None}) is None


def test_validate_sex_invalid_fail_fast():
    """FR-001: invalid sex raises ValueError with message."""
    with pytest.raises(ValueError, match="male.*female"):
        validate_sex({"sex": "x"})
    with pytest.raises(ValueError, match="male.*female"):
        validate_sex({"sex": ""})
    with pytest.raises(ValueError):
        validate_sex({"sex": 123})


def test_resolve_sex_mode_order():
    """birth_data.sex_mode first, then config, default explicit."""
    assert resolve_sex_mode({}) == "explicit"
    assert resolve_sex_mode({"sex_mode": "infer"}) == "infer"
    class C:
        sex_mode = "infer"
    assert resolve_sex_mode({}, C()) == "infer"
    assert resolve_sex_mode({"sex_mode": "explicit"}, C()) == "explicit"
