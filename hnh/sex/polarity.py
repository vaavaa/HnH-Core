"""
SexPolarityEngine (Spec 008, FR-008, FR-009).
E = clamp(a*sex_score + b*sign_polarity_score + c*sect_score, -1, +1).
"""

from __future__ import annotations


def sex_score(sex: str | None) -> float:
    """FR-008: male +1, female -1, None 0."""
    if sex is None:
        return 0.0
    s = sex.strip().lower()
    if s == "male":
        return 1.0
    if s == "female":
        return -1.0
    return 0.0


def compute_E(
    sex: str | None,
    sign_polarity_score: float,
    sect_score: int,
    *,
    a: float = 0.70,
    b: float = 0.20,
    c: float = 0.10,
) -> float:
    """
    FR-009: E = clamp(a*sex_score + b*sign_polarity_score + c*sect_score, -1, +1).
    Defaults a=0.70, b=0.20, c=0.10. For E from sex only, use b=0, c=0.
    """
    raw = a * sex_score(sex) + b * sign_polarity_score + c * float(sect_score)
    return max(-1.0, min(1.0, raw))
