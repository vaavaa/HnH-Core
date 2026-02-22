"""
009 Sex Transit Response config (Spec 009).
Separate from ReplayConfig (frozen). Agent holds optional sex_transit_config;
resolution order: Agent config wins over ReplayConfig when both provide 009 fields.
"""

from __future__ import annotations

from dataclasses import dataclass

# Allowed values for sex_transit_mode (FR-001). Unknown → ValueError.
SEX_TRANSIT_MODES: frozenset[str] = frozenset({"off", "scale_delta", "scale_sensitivity"})


@dataclass(frozen=True)
class SexTransitConfig:
    """
    009 config: sex_transit_mode, beta, mcap, Wdyn profile.
    Defaults: off, 0.05, 0.10, "v1". Validation (invalid mode or unknown profile)
    raises ValueError with documented message — see validate_sex_transit_config().
    """

    sex_transit_mode: str = "off"
    sex_transit_beta: float = 0.05
    sex_transit_mcap: float = 0.10
    sex_transit_Wdyn_profile: str = "v1"

    def __post_init__(self) -> None:
        if self.sex_transit_mode not in SEX_TRANSIT_MODES:
            raise ValueError(
                f"sex_transit_mode must be one of {sorted(SEX_TRANSIT_MODES)}, got: {self.sex_transit_mode!r}"
            )
        if self.sex_transit_beta < 0 or self.sex_transit_mcap < 0 or self.sex_transit_mcap > 1:
            raise ValueError(
                f"sex_transit_beta and sex_transit_mcap must be non-negative; mcap ≤ 1; "
                f"got beta={self.sex_transit_beta}, mcap={self.sex_transit_mcap}"
            )


def validate_sex_transit_mode(mode: str) -> None:
    """
    FR-001: Invalid sex_transit_mode → fail-fast.
    Raises ValueError with message: 'sex_transit_mode must be one of ... got: {value}'.
    """
    if mode not in SEX_TRANSIT_MODES:
        raise ValueError(
            f"sex_transit_mode must be one of {sorted(SEX_TRANSIT_MODES)}, got: {mode!r}"
        )


def validate_wdyn_profile(profile: str, registered: frozenset[str]) -> None:
    """
    FR-012: Unknown sex_transit_Wdyn_profile → fail-fast.
    Raises ValueError with message: 'sex_transit_Wdyn_profile must be a registered profile ... got: {value}'.
    """
    if profile not in registered:
        raise ValueError(
            f"sex_transit_Wdyn_profile must be a registered profile (e.g. 'v1'), got: {profile!r}"
        )
