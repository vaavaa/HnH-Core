"""
Agent: single orchestrator (Spec 006). Composition: natal, behavior, transits, optional lifecycle.
step(date) order: (1) transit_state, (2) lifecycle update (resilience from current_vector), (3) behavior.apply_transits.
Spec 008: birth_data.sex/sex_mode, identity includes sex_delta_32; step() output includes sex and sex_polarity_E.
FR-021a: By default do not log sex, birth_data, or derived identifiers; opt-in audit/debug mode must be documented.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from hnh.identity.schema import NUM_PARAMETERS
from hnh.identity.sensitivity import compute_sensitivity
from hnh.lifecycle.fatigue import global_sensitivity, resilience_from_base_vector
from hnh.config.replay_config import ReplayConfig

# Default ReplayConfig when config=None
_DEFAULT_CONFIG = ReplayConfig(global_max_delta=0.08, shock_threshold=0.5, shock_multiplier=1.0)


def _build_identity_config_from_natal(
    natal: Any, birth_data: dict[str, Any], config: Any, identity_hash_digest: bytes | None = None
) -> Any:
    """Build protocol object (base_vector, sensitivity_vector, sex, sex_polarity_E) from natal + birth_data. Deterministic. Spec 008."""
    from hnh.sex.validation import validate_sex
    from hnh.sex.resolution import resolve_sex_mode
    from hnh.sex.resolver import resolve_sex, resolve_sex_explicit
    from hnh.sex.sign_polarity import sign_polarity_score
    from hnh.sex.sect import sect_score_from_natal
    from hnh.sex.polarity import compute_E
    from hnh.sex.delta_32 import compute_sex_delta_32
    from hnh.sex.identity_hash import identity_hash_for_tie_break

    validate_sex(birth_data)  # fail-fast if invalid (FR-001)
    mode = resolve_sex_mode(birth_data, config)
    digest = identity_hash_digest if identity_hash_digest is not None else identity_hash_for_tie_break(birth_data)
    if mode == "explicit":
        resolved_sex = resolve_sex_explicit(birth_data, config)
    else:
        resolved_sex = resolve_sex(birth_data, config, natal, identity_hash_digest=digest)
    natal_data = natal.to_natal_data() if hasattr(natal, "to_natal_data") else natal
    sensitivity_vector = compute_sensitivity(natal_data)
    if resolved_sex is None:
        E = 0.0
        sex_delta_32 = (0.0,) * NUM_PARAMETERS
    else:
        planet_signs = {p.name.strip().title(): p.sign_index for p in natal.planets} if hasattr(natal, "planets") else {}
        try:
            sp_score = sign_polarity_score(planet_signs)
        except ValueError:
            sp_score = 0.0
        sect_sc = sect_score_from_natal(natal_data)
        E = compute_E(resolved_sex, sp_score, sect_sc)
        sex_delta_32 = compute_sex_delta_32(E)
    base_vector = tuple(max(0.0, min(1.0, 0.5 + sex_delta_32[i])) for i in range(NUM_PARAMETERS))
    return type("_IdentityFromNatal", (), {
        "base_vector": base_vector,
        "sensitivity_vector": sensitivity_vector,
        "sex": resolved_sex,
        "sex_polarity_E": E,
    })()


@dataclass
class StepResult:
    """FR-020: step() output includes sex and sex_polarity_E. FR-021: debug/research may extend with sign_polarity_score, sect, sect_score, sex_delta_32 (e.g. from identity_config)."""
    sex: str | None
    sex_polarity_E: float


class Agent:
    """
    Single orchestrator: natal, behavior, transits, lifecycle (optional).
    ZodiacExpression not in constructor — use zodiac_expression() when needed.
    """

    __slots__ = ("natal", "behavior", "transits", "lifecycle", "_config", "_identity_config", "_zodiac", "_last_step_result")

    def __init__(
        self,
        birth_data: dict[str, Any],
        config: ReplayConfig | None = None,
        lifecycle: bool = False,
        identity_config: Any = None,
    ) -> None:
        """
        birth_data: per data-model §0 (variant A or B); may include sex, sex_mode (Spec 008).
        config: ReplayConfig for step(); default used if None.
        lifecycle: if True, create LifecycleEngine; else lifecycle=None (product mode).
        identity_config: protocol (base_vector, sensitivity_vector); if None, built from natal + birth_data.
        """
        from hnh.astrology.natal_chart import NatalChart
        from hnh.astrology.transits import TransitEngine
        from hnh.lifecycle.engine import LifecycleEngine
        from hnh.state.behavioral_core import BehavioralCore

        self._config = config if config is not None else _DEFAULT_CONFIG
        self.natal = NatalChart.from_birth_data(birth_data)
        if identity_config is None:
            from hnh.sex.identity_hash import identity_hash_for_tie_break
            identity_hash_digest = identity_hash_for_tie_break(birth_data)
            identity_config = _build_identity_config_from_natal(
                self.natal, birth_data, self._config, identity_hash_digest=identity_hash_digest
            )
        self._identity_config = identity_config
        self.behavior = BehavioralCore(self.natal, identity_config)
        self.transits = TransitEngine(self.natal)
        self.lifecycle = LifecycleEngine(
            initial_f=getattr(self._config, "initial_f", 0.0),
            initial_w=getattr(self._config, "initial_w", 0.0),
        ) if lifecycle else None
        self._zodiac = None
        self._last_step_result: StepResult | None = None

    def step(self, date_or_dt: date | datetime) -> StepResult:
        """
        Order: (1) transit_state = transits.state(date, config);
               (2) resilience from behavior.current_vector (before apply_transits);
               (3) if lifecycle: update_lifecycle(stress, resilience);
               (4) behavior.apply_transits(transit_state).
        Returns StepResult(sex, sex_polarity_E) per FR-020.
        """
        transit_state = self.transits.state(date_or_dt, self._config)
        resilience = resilience_from_base_vector(self.behavior.current_vector)
        if self.lifecycle is not None:
            s_g = global_sensitivity(self._identity_config.sensitivity_vector)
            self.lifecycle.update_lifecycle(transit_state.stress, resilience, s_g=s_g)
        self.behavior.apply_transits(transit_state)
        sex = getattr(self._identity_config, "sex", None)
        E = getattr(self._identity_config, "sex_polarity_E", 0.0)
        result = StepResult(sex=sex, sex_polarity_E=E)
        self._last_step_result = result
        return result

    def zodiac_expression(self) -> Any:
        """Lazy ZodiacExpression (read-only view over natal)."""
        if self._zodiac is None:
            from hnh.astrology.zodiac_expression import ZodiacExpression
            self._zodiac = ZodiacExpression(self.natal)
        return self._zodiac
