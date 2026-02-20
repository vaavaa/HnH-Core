"""
BehavioralCore: 32D state layer (Spec 006). base_vector immutable; current_vector updated by apply_transits.
identity_config: protocol (base_vector, sensitivity_vector); delegates to state.assembler.
"""

from __future__ import annotations

from typing import Any, Protocol

from hnh.identity.schema import NUM_PARAMETERS
from hnh.state.assembler import assemble_state

# Avoid circular import: TransitState from astrology
try:
    from hnh.astrology.transit_state import TransitState
except ImportError:
    TransitState = Any  # type: ignore[misc, assignment]


class IdentityConfigProtocol(Protocol):
    """Protocol: any object with base_vector and sensitivity_vector (tuple[float, ...] length 32)."""

    base_vector: tuple[float, ...]
    sensitivity_vector: tuple[float, ...]


def _check_identity_config(obj: Any) -> None:
    if len(getattr(obj, "base_vector", ())) != NUM_PARAMETERS or len(
        getattr(obj, "sensitivity_vector", ())
    ) != NUM_PARAMETERS:
        raise ValueError(f"identity_config must have base_vector and sensitivity_vector of length {NUM_PARAMETERS}")


class BehavioralCore:
    """
    32-parameter behavioral state. base_vector from identity_config (never mutated).
    current_vector updated only by apply_transits(transit_state).
    """

    __slots__ = ("_natal", "_identity_config", "_base_vector", "_current_vector")

    def __init__(self, natal: Any, identity_config: IdentityConfigProtocol) -> None:
        """
        natal: NatalChart (used for reference; sensitivity/base may be derived from it elsewhere).
        identity_config: object with .base_vector and .sensitivity_vector (both length 32).
        """
        _check_identity_config(identity_config)
        self._natal = natal
        self._identity_config = identity_config
        base = identity_config.base_vector
        self._base_vector = tuple(base)
        self._current_vector = tuple(base)

    @property
    def base_vector(self) -> tuple[float, ...]:
        """Immutable base (from identity_config at construction)."""
        return self._base_vector

    @property
    def current_vector(self) -> tuple[float, ...]:
        """Current 32D state (updated by apply_transits)."""
        return self._current_vector

    def apply_transits(self, transit_state: TransitState) -> None:
        """
        Update current_vector from transit_state.bounded_delta and sensitivity from identity_config.
        Delegates to assemble_state; memory_delta = zeros. Does not mutate base_vector.
        """
        sens = self._identity_config.sensitivity_vector
        params_final, _axis_final = assemble_state(
            self._base_vector,
            sens,
            transit_state.bounded_delta,
            memory_delta=None,
        )
        self._current_vector = params_final
