"""
Agent: single orchestrator (Spec 006). Composition: natal, behavior, transits, optional lifecycle.
step(date) order: (1) transit_state, (2) lifecycle update (resilience from current_vector), (3) behavior.apply_transits.
Spec 008: birth_data.sex/sex_mode, identity includes sex_delta_32; step() output includes sex and sex_polarity_E.
Spec 009: optional sex_transit_config; when sex_transit_mode=scale_delta, transit response at every step depends on sex.
FR-021a: By default do not log sex, birth_data, or derived identifiers; opt-in audit/debug mode must be documented.

009 config resolution (FR-002a): When both Agent and ReplayConfig could provide 009 fields, Agent config wins.
Currently 009 fields live only on Agent (sex_transit_config). ReplayConfig is frozen and does not include 009 fields.
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
    """FR-020: step() output includes sex and sex_polarity_E. FR-021: debug/research may extend with sign_polarity_score, sect, sect_score, sex_delta_32 (e.g. from identity_config). US3 (009): when 008 debug is on and 009 scale_delta active, debug_009 holds multiplier_stats etc."""
    sex: str | None
    sex_polarity_E: float
    debug_009: dict[str, Any] | None = None


class Agent:
    """
    Single orchestrator: natal, behavior, transits, lifecycle (optional).
    ZodiacExpression not in constructor — use zodiac_expression() when needed.
    """

    __slots__ = (
        "natal", "behavior", "transits", "lifecycle",
        "_config", "_identity_config", "_zodiac", "_last_step_result",
        "_sex_transit_config", "_debug",
    )

    def __init__(
        self,
        birth_data: dict[str, Any],
        config: ReplayConfig | None = None,
        lifecycle: bool = False,
        identity_config: Any = None,
        sex_transit_config: Any = None,
        debug: bool = False,
    ) -> None:
        """
        birth_data: per data-model §0 (variant A or B); may include sex, sex_mode (Spec 008).
        config: ReplayConfig for step(); default used if None.
        lifecycle: if True, create LifecycleEngine; else lifecycle=None (product mode).
        identity_config: protocol (base_vector, sensitivity_vector); if None, built from natal + birth_data.
        sex_transit_config: optional 009 config (SexTransitConfig). If None, sex_transit_mode is effectively "off".
        debug: 008 audit/debug mode (FR-021a). When True, step() may include 009 debug_009 when 009 is active.
        Resolution order (FR-002a): Agent sex_transit_config wins over any 009 fields on config.
        """
        from hnh.astrology.natal_chart import NatalChart
        from hnh.astrology.transits import TransitEngine
        from hnh.lifecycle.engine import LifecycleEngine
        from hnh.state.behavioral_core import BehavioralCore

        self._config = config if config is not None else _DEFAULT_CONFIG
        self._sex_transit_config = sex_transit_config
        self._debug = debug
        # Validate 009 profile at build when mode != off (FR-012 fail-fast)
        if sex_transit_config is not None and getattr(sex_transit_config, "sex_transit_mode", "off") != "off":
            from hnh.sex.transit_modulator import get_wdyn_profile
            get_wdyn_profile(getattr(sex_transit_config, "sex_transit_Wdyn_profile", "v1"))
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
               (4) 009 if enabled: scale bounded_delta by M, pass modified TransitState;
               (5) behavior.apply_transits(transit_state).
        Returns StepResult(sex, sex_polarity_E) per FR-020.
        """
        from hnh.astrology.transit_state import TransitState

        transit_state = self.transits.state(date_or_dt, self._config)
        debug_009: dict[str, Any] | None = None
        # 009: optional sex-based modulation of transit response (scale_delta)
        stc = getattr(self, "_sex_transit_config", None)
        if stc is not None and getattr(stc, "sex_transit_mode", "off") == "scale_delta":
            E = getattr(self._identity_config, "sex_polarity_E", 0.0)
            sex = getattr(self._identity_config, "sex", None)
            if E != 0.0 and sex is not None:
                from hnh.sex.transit_modulator import (
                    compute_multipliers,
                    apply_bounded_delta_eff,
                )
                beta = getattr(stc, "sex_transit_beta", 0.05)
                mcap = getattr(stc, "sex_transit_mcap", 0.10)
                profile = getattr(stc, "sex_transit_Wdyn_profile", "v1")
                M = compute_multipliers(E, profile, beta=beta, mcap=mcap)
                bounded_eff = apply_bounded_delta_eff(transit_state.bounded_delta, M)
                if getattr(self, "_debug", False):
                    min_M, max_M = min(M), max(M)
                    mean_abs_M_minus_1 = sum(abs(M[i] - 1.0) for i in range(len(M))) / len(M)
                    debug_009 = {
                        "sex_transit_mode": "scale_delta",
                        "sex_transit_beta": beta,
                        "sex_transit_mcap": mcap,
                        "sex_transit_Wdyn_profile": profile,
                        "multiplier_stats": {
                            "min_M": min_M,
                            "max_M": max_M,
                            "mean_abs_M_minus_1": mean_abs_M_minus_1,
                        },
                        "max_abs_transit_delta": max(abs(x) for x in transit_state.bounded_delta),
                        "max_abs_transit_delta_eff": max(abs(x) for x in bounded_eff),
                    }
                transit_state = TransitState(
                    stress=transit_state.stress,
                    raw_delta=transit_state.raw_delta,
                    bounded_delta=bounded_eff,
                )
        resilience = resilience_from_base_vector(self.behavior.current_vector)
        if self.lifecycle is not None:
            s_g = global_sensitivity(self._identity_config.sensitivity_vector)
            self.lifecycle.update_lifecycle(transit_state.stress, resilience, s_g=s_g)
        self.behavior.apply_transits(transit_state)
        sex = getattr(self._identity_config, "sex", None)
        E = getattr(self._identity_config, "sex_polarity_E", 0.0)
        result = StepResult(sex=sex, sex_polarity_E=E, debug_009=debug_009)
        self._last_step_result = result
        return result

    def zodiac_expression(self) -> Any:
        """Lazy ZodiacExpression (read-only view over natal)."""
        if self._zodiac is None:
            from hnh.astrology.zodiac_expression import ZodiacExpression
            self._zodiac = ZodiacExpression(self.natal)
        return self._zodiac
