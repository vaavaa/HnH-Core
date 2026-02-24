"""
AgeEngine: compute(birth_datetime_utc, injected_time_utc) -> AgeOutput.
Uses age_stage_features_v1, compute_age_delta_32, apply_daily_lipschitz. Spec 010.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from hnh.age.delta_32 import apply_daily_lipschitz, compute_age_delta_32
from hnh.age.stage_features import age_stage_features_v1, age_years_from_delta_days
from hnh.config.age_config import AgeConfig


@dataclass
class AgeOutput:
    """Result of AgeEngine.compute(). Spec 010 data-model §3."""

    age_years: float
    age_stage_features: tuple[float, ...]  # length 5
    age_delta_32: tuple[float, ...]  # length 32
    age_delta_32_stats: dict[str, float] | None = None  # max_abs, mean_abs, nonzero_count


def _stats(delta_32: tuple[float, ...]) -> dict[str, float]:
    """Compute max_abs, mean_abs, nonzero_count for age_delta_32."""
    abs_vals = [abs(x) for x in delta_32]
    return {
        "max_abs": max(abs_vals),
        "mean_abs": sum(abs_vals) / len(abs_vals),
        "nonzero_count": sum(1 for x in delta_32 if x != 0.0),
    }


class AgeEngine:
    """
    Computes age_years, age_stage_features, age_delta_32 from birth and injected time.
    Maintains _last_age_delta_32 for apply_daily_lipschitz between consecutive compute() calls.
    """

    __slots__ = ("_config", "_last_age_delta_32")

    def __init__(self, config: AgeConfig) -> None:
        if config.age_mode != "on":
            raise ValueError("AgeEngine requires age_config.age_mode == 'on'")
        self._config = config
        self._last_age_delta_32: tuple[float, ...] | None = None

    def compute(
        self,
        birth_datetime_utc: datetime,
        injected_time_utc: datetime,
        *,
        include_stats: bool = False,
    ) -> AgeOutput:
        """
        Compute age and age_delta_32. First call returns raw delta; subsequent calls apply daily Lipschitz.
        """
        delta_seconds = (injected_time_utc - birth_datetime_utc).total_seconds()
        delta_days = delta_seconds / 86400.0
        age_years = age_years_from_delta_days(delta_days, self._config.age_max_years)
        features = age_stage_features_v1(age_years)
        raw_delta_32 = compute_age_delta_32(
            features,
            self._config.age_strength,
            self._config.age_max_param_delta,
        )
        age_delta_32 = apply_daily_lipschitz(
            self._last_age_delta_32,
            raw_delta_32,
            self._config.age_daily_lipschitz,
        )
        self._last_age_delta_32 = age_delta_32

        stats: dict[str, float] | None = _stats(age_delta_32) if include_stats else None
        return AgeOutput(
            age_years=age_years,
            age_stage_features=features,
            age_delta_32=age_delta_32,
            age_delta_32_stats=stats,
        )


def get_birth_datetime_utc_from_birth_data(birth_data: dict) -> datetime | None:
    """
    Extract birth_datetime_utc from birth_data (006 data-model).
    Returns None if not present. Used by Agent for fail-fast when age_mode=on.
    Documented error when missing and age_mode=on: ValueError('birth_datetime_utc required when age_mode=on but missing in birth_data').
    """
    # Variant A: datetime_utc (str ISO or datetime)
    dt = birth_data.get("datetime_utc")
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    if isinstance(dt, str):
        try:
            parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


# Documented error for missing birth_datetime_utc when age_mode=on (spec Clarifications)
MISSING_BIRTH_DATETIME_UTC_MESSAGE = (
    "birth_datetime_utc required when age_mode=on but missing in birth_data"
)
