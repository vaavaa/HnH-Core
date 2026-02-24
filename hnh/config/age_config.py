"""
Age configuration for Spec 010 (Age Influence).
Valid ranges (documented for fail-fast): age_strength ∈ (0, 0.2], age_max_param_delta ∈ (0, 0.2],
age_daily_lipschitz ≥ 0, age_max_years > 0. age_mode in ("off", "on") else ValueError.
Error type: ValueError. Message includes field name and constraint.
"""

from __future__ import annotations

from dataclasses import dataclass

# Documented valid ranges (spec Clarifications)
AGE_STRENGTH_MAX: float = 0.2
AGE_MAX_PARAM_DELTA_MAX: float = 0.2


@dataclass(frozen=True)
class AgeConfig:
    """
    Config for age-based 32D delta. Spec 010 data-model.
    Invalid numeric values or unknown age_mode raise ValueError when used (fail-fast).
    """

    age_mode: str = "off"
    age_strength: float = 0.04
    age_max_param_delta: float = 0.06
    age_daily_lipschitz: float = 0.001
    age_profile: str = "v1"
    age_max_years: float = 120.0

    def __post_init__(self) -> None:
        if self.age_mode not in ("off", "on"):
            raise ValueError(
                f"age_mode must be 'off' or 'on', got {self.age_mode!r}"
            )
        if self.age_strength <= 0 or self.age_strength > AGE_STRENGTH_MAX:
            raise ValueError(
                f"age_strength must be in (0, {AGE_STRENGTH_MAX}], got {self.age_strength}"
            )
        if self.age_max_param_delta <= 0 or self.age_max_param_delta > AGE_MAX_PARAM_DELTA_MAX:
            raise ValueError(
                f"age_max_param_delta must be in (0, {AGE_MAX_PARAM_DELTA_MAX}], got {self.age_max_param_delta}"
            )
        if self.age_daily_lipschitz < 0:
            raise ValueError(
                f"age_daily_lipschitz must be >= 0, got {self.age_daily_lipschitz}"
            )
        if self.age_max_years <= 0:
            raise ValueError(
                f"age_max_years must be > 0, got {self.age_max_years}"
            )
