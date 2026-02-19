"""
Lifecycle & Entropy layer (Spec 005). Research Mode only.
Fatigue F, limit L, activity A_g, death, will W, transcendence. Deterministic; O(1) per day.
"""

from hnh.lifecycle.constants import (
    DEFAULT_LIFECYCLE_CONSTANTS,
    LifecycleConstants,
)
from hnh.lifecycle.engine import (
    ACTIVITY_SENSITIVE_INDICES,
    LifecycleSnapshot,
    LifecycleState,
    LifecycleStepState,
    activity_factor,
    age_psy_years,
    apply_behavioral_degradation,
    check_init_death_or_transcendence,
    lifecycle_step,
)
from hnh.lifecycle.fatigue import (
    fatigue_limit,
    global_sensitivity,
    load,
    normalized_fatigue,
    recovery,
    resilience_from_base_vector,
    update_fatigue,
)
from hnh.lifecycle.stress import (
    compute_raw_transit_intensity,
    compute_transit_stress,
)

__all__ = [
    "LifecycleConstants",
    "DEFAULT_LIFECYCLE_CONSTANTS",
    "LifecycleState",
    "LifecycleStepState",
    "LifecycleSnapshot",
    "activity_factor",
    "age_psy_years",
    "apply_behavioral_degradation",
    "check_init_death_or_transcendence",
    "lifecycle_step",
    "ACTIVITY_SENSITIVE_INDICES",
    "resilience_from_base_vector",
    "global_sensitivity",
    "load",
    "recovery",
    "fatigue_limit",
    "normalized_fatigue",
    "update_fatigue",
    "compute_raw_transit_intensity",
    "compute_transit_stress",
]
