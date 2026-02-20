"""
Agent: single orchestrator (Spec 006). Composition: natal, behavior, transits, optional lifecycle.
step(date) order: (1) transit_state, (2) lifecycle update (resilience from current_vector), (3) behavior.apply_transits.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from hnh.identity.schema import NUM_PARAMETERS
from hnh.identity.sensitivity import compute_sensitivity
from hnh.lifecycle.fatigue import global_sensitivity, resilience_from_base_vector
from hnh.config.replay_config import ReplayConfig

# Default ReplayConfig when config=None
_DEFAULT_CONFIG = ReplayConfig(global_max_delta=0.08, shock_threshold=0.5, shock_multiplier=1.0)


def _build_identity_config_from_natal(natal: Any) -> Any:
    """Build protocol object (base_vector, sensitivity_vector) from natal. Deterministic."""
    natal_data = natal.to_natal_data() if hasattr(natal, "to_natal_data") else natal
    sensitivity_vector = compute_sensitivity(natal_data)
    base_vector = (0.5,) * NUM_PARAMETERS  # neutral base
    return type("_IdentityFromNatal", (), {"base_vector": base_vector, "sensitivity_vector": sensitivity_vector})()


class Agent:
    """
    Single orchestrator: natal, behavior, transits, lifecycle (optional).
    ZodiacExpression not in constructor — use zodiac_expression() when needed.
    """

    __slots__ = ("natal", "behavior", "transits", "lifecycle", "_config", "_identity_config", "_zodiac")

    def __init__(
        self,
        birth_data: dict[str, Any],
        config: ReplayConfig | None = None,
        lifecycle: bool = False,
        identity_config: Any = None,
    ) -> None:
        """
        birth_data: per data-model §0 (variant A or B).
        config: ReplayConfig for step(); default used if None.
        lifecycle: if True, create LifecycleEngine; else lifecycle=None (product mode).
        identity_config: protocol (base_vector, sensitivity_vector); if None, built from natal.
        """
        from hnh.astrology.natal_chart import NatalChart
        from hnh.astrology.transits import TransitEngine
        from hnh.lifecycle.engine import LifecycleEngine
        from hnh.state.behavioral_core import BehavioralCore

        self._config = config if config is not None else _DEFAULT_CONFIG
        self.natal = NatalChart.from_birth_data(birth_data)
        if identity_config is None:
            identity_config = _build_identity_config_from_natal(self.natal)
        self._identity_config = identity_config
        self.behavior = BehavioralCore(self.natal, identity_config)
        self.transits = TransitEngine(self.natal)
        self.lifecycle = LifecycleEngine(
            initial_f=getattr(self._config, "initial_f", 0.0),
            initial_w=getattr(self._config, "initial_w", 0.0),
        ) if lifecycle else None
        self._zodiac = None

    def step(self, date_or_dt: date | datetime) -> None:
        """
        Order: (1) transit_state = transits.state(date, config);
               (2) resilience from behavior.current_vector (before apply_transits);
               (3) if lifecycle: update_lifecycle(stress, resilience);
               (4) behavior.apply_transits(transit_state).
        """
        transit_state = self.transits.state(date_or_dt, self._config)
        resilience = resilience_from_base_vector(self.behavior.current_vector)
        if self.lifecycle is not None:
            s_g = global_sensitivity(self._identity_config.sensitivity_vector)
            self.lifecycle.update_lifecycle(transit_state.stress, resilience, s_g=s_g)
        self.behavior.apply_transits(transit_state)

    def zodiac_expression(self) -> Any:
        """Lazy ZodiacExpression (read-only view over natal)."""
        if self._zodiac is None:
            from hnh.astrology.zodiac_expression import ZodiacExpression
            self._zodiac = ZodiacExpression(self.natal)
        return self._zodiac
