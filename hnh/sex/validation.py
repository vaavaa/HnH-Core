"""
Birth_data sex validation (Spec 008, FR-001).
Valid values: "male", "female", or None (absent). Any other value → fail-fast.
"""

from __future__ import annotations

from typing import Any

# Documented error type and semantics: FR-001
# Raises: ValueError with message describing the invalid value (e.g. "sex must be 'male', 'female', or None; got ...")


VALID_SEX_VALUES: frozenset[str] = frozenset({"male", "female"})


def validate_sex(birth_data: dict[str, Any]) -> str | None:
    """
    Validate and return sex from birth_data.

    Accepts birth_data["sex"] in {"male", "female"} or absent/None.
    Returns "male" | "female" | None (if absent or explicitly None).

    Raises:
        ValueError: If sex is present and not in {"male", "female"}.
            Message format: "sex must be 'male', 'female', or None; got {value!r}".
            Error type and message are documented per FR-001.
    """
    raw = birth_data.get("sex")
    if raw is None:
        return None
    if isinstance(raw, str):
        s = raw.strip().lower()
        if s in VALID_SEX_VALUES:
            return s
        if s == "":
            raise ValueError("sex must be 'male', 'female', or None; got empty string")
        raise ValueError(f"sex must be 'male', 'female', or None; got {raw!r}")
    raise ValueError(f"sex must be 'male', 'female', or None; got {type(raw).__name__}: {raw!r}")
