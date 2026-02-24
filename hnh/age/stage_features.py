"""
Deterministic age stage features (Spec 010 v1). All values in [0, 1].
Order: maturity, saturn_event, jupiter_return, nodal_return, uranus_opposition.
"""

from __future__ import annotations

import math

from hnh.age.constants import (
    JUPITER_PERIOD_YEARS,
    NODE_PERIOD_YEARS,
    SATURN_PERIOD_YEARS,
    TROPICAL_YEAR_DAYS,
    URANUS_PERIOD_YEARS,
)


def bump(age: float, center: float, width: float) -> float:
    """Triangular bump: max(0, 1 - |age - center| / width). width MUST be > 0."""
    if width <= 0:
        raise ValueError(f"width must be > 0, got {width}")
    return max(0.0, 1.0 - abs(age - center) / width)


def sigmoid(x: float) -> float:
    """Numerically stable sigmoid: 1/(1+exp(-x)) for x>=0, exp(x)/(1+exp(x)) for x<0. Output in (0, 1)."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


def age_years_from_delta_days(delta_days: float, age_max_years: float) -> float:
    """Clamp age in years from delta_days / TROPICAL_YEAR_DAYS to [0, age_max_years]."""
    age = delta_days / TROPICAL_YEAR_DAYS
    return max(0.0, min(age_max_years, age))


def maturity(age_years: float) -> float:
    """Continuous monotone; sigmoid((age_years - 25) / 7). Value in [0, 1]."""
    return sigmoid((age_years - 25.0) / 7.0)


def saturn_event(age_years: float) -> float:
    """Phase-based Saturn landmarks; max of bumps at return, squares, opposition. Value in [0, 1]."""
    p = age_years % SATURN_PERIOD_YEARS
    T = SATURN_PERIOD_YEARS
    c0, c1, c2, c3 = 0.0, 0.25 * T, 0.5 * T, 0.75 * T
    return max(
        bump(p, c0, 1.5),
        bump(p, c1, 1.0),
        bump(p, c2, 1.0),
        bump(p, c3, 1.0),
    )


def jupiter_return(age_years: float) -> float:
    """Jupiter return bump at 0 within cycle. Value in [0, 1]."""
    pj = age_years % JUPITER_PERIOD_YEARS
    return bump(pj, 0.0, 0.75)


def nodal_return(age_years: float) -> float:
    """Nodal return: max of two bumps at 0 and half period. Value in [0, 1]."""
    pn = age_years % NODE_PERIOD_YEARS
    half = 0.5 * NODE_PERIOD_YEARS
    return max(bump(pn, 0.0, 1.0), bump(pn, half, 1.0))


def uranus_opposition(age_years: float) -> float:
    """Uranus opposition (midlife) at half cycle. Value in [0, 1]."""
    pu = age_years % URANUS_PERIOD_YEARS
    center = 0.5 * URANUS_PERIOD_YEARS
    return bump(pu, center, 2.0)


def age_stage_features_v1(age_years: float) -> tuple[float, float, float, float, float]:
    """
    Canonical order: (maturity, saturn_event, jupiter_return, nodal_return, uranus_opposition).
    All values in [0, 1]. Spec 010 data-model §4.
    """
    return (
        maturity(age_years),
        saturn_event(age_years),
        jupiter_return(age_years),
        nodal_return(age_years),
        uranus_opposition(age_years),
    )
