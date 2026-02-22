"""
009 Sex Transit Response: SexTransitModulator (Spec 009).
Computes per-parameter multipliers M[i] and optional bounded_delta_eff.
Wdyn registry: "v1" → W32_V1. Unknown profile → ValueError (FR-012).
"""

from __future__ import annotations

from hnh.identity.schema import NUM_PARAMETERS
from hnh.sex.delta_32 import W32_V1

# Wdyn profile registry: profile_name → tuple of 32 weights (canonical order, spec 002).
# Unknown profile name MUST raise; see get_wdyn_profile().
_WDYN_REGISTRY: dict[str, tuple[float, ...]] = {
    "v1": tuple(float(x) for x in W32_V1),
}


def get_wdyn_profile(profile_name: str) -> tuple[float, ...]:
    """
    Return Wdyn vector for the given profile name.
    FR-012: Unknown or invalid profile → fail-fast ValueError.
    Error type: ValueError. Message: 'sex_transit_Wdyn_profile must be a registered profile (e.g. "v1"), got: {name}'.
    """
    if profile_name not in _WDYN_REGISTRY:
        raise ValueError(
            f'sex_transit_Wdyn_profile must be a registered profile (e.g. "v1"), got: {profile_name!r}'
        )
    return _WDYN_REGISTRY[profile_name]


def registered_wdyn_profiles() -> frozenset[str]:
    """Return set of registered profile names (for validation)."""
    return frozenset(_WDYN_REGISTRY)


def compute_multipliers(
    E: float,
    profile_name: str,
    beta: float = 0.05,
    mcap: float = 0.10,
) -> tuple[float, ...]:
    """
    M[i] = clamp(1 + beta * E * Wdyn[i], 1 - mcap, 1 + mcap).
    Deterministic, no I/O. FR-011, SC-002.
    If E is 0, returns (1.0,) * 32 (identity). Unknown profile_name → ValueError from get_wdyn_profile().
    """
    if E == 0.0:
        return (1.0,) * NUM_PARAMETERS
    wdyn = get_wdyn_profile(profile_name)
    if len(wdyn) != NUM_PARAMETERS:
        raise ValueError(f"Wdyn profile {profile_name!r} must have length {NUM_PARAMETERS}, got {len(wdyn)}")
    out: list[float] = []
    for i in range(NUM_PARAMETERS):
        raw = 1.0 + beta * E * wdyn[i]
        out.append(max(1.0 - mcap, min(1.0 + mcap, raw)))
    return tuple(out)


def apply_bounded_delta_eff(
    bounded_delta: tuple[float, ...],
    M: tuple[float, ...],
) -> tuple[float, ...]:
    """
    transit_delta_eff[i] = bounded_delta[i] * M[i]. FR-010.
    Both inputs must have length NUM_PARAMETERS.
    """
    if len(bounded_delta) != NUM_PARAMETERS or len(M) != NUM_PARAMETERS:
        raise ValueError(
            f"bounded_delta and M must have length {NUM_PARAMETERS}, "
            f"got {len(bounded_delta)} and {len(M)}"
        )
    return tuple(bounded_delta[i] * M[i] for i in range(NUM_PARAMETERS))
