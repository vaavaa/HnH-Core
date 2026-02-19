"""
Lifecycle & Entropy constants (Spec 005). Defaults from spec; all replay-relevant when lifecycle enabled.
"""

from __future__ import annotations

from dataclasses import dataclass

# Transit stress (contract transit-stress)
C_T_DEFAULT: float = 3.0
HARD_ASPECTS: frozenset[str] = frozenset({"Conjunction", "Opposition", "Square"})
HARD_ASPECT_WEIGHT_DEFAULT: float = 1.0

# Fatigue §5
THETA_SHOCK: float = 0.90
ALPHA_SHOCK: float = 0.6
BETA_S: float = 0.6
BETA_R: float = 0.7
GAMMA_0: float = 0.12
GAMMA_R: float = 0.30
GAMMA_C: float = 0.20
LAMBDA_UP: float = 0.010
LAMBDA_DOWN: float = 0.009

# Fatigue limit §6
L0: float = 14.0
DELTA_R: float = 0.8
DELTA_S: float = 0.5

# Activity §7
RHO: float = 2.5
DELTA_P: float = 0.08
ACTIVITY_SUPPRESSION_CAP: float = 0.1

# Psychological age §8 (A in days; output in years)
ETA_0: float = 0.80
ETA_1: float = 0.45
KAPPA: float = 2.0
DAYS_PER_YEAR: float = 365.25

# Will §10
Q_CRIT: float = 0.75
ETA_W: float = 0.12
XI_W: float = 0.30
DELTA_W_MIN: float = -0.03
DELTA_W_MAX: float = 0.02

# Transcendence §11
W_TRANSCEND: float = 0.995


@dataclass(frozen=True)
class LifecycleConstants:
    """All lifecycle constants (defaults from spec). Replay-relevant when lifecycle enabled."""

    c_t: float = C_T_DEFAULT
    theta_shock: float = THETA_SHOCK
    alpha_shock: float = ALPHA_SHOCK
    beta_s: float = BETA_S
    beta_r: float = BETA_R
    gamma_0: float = GAMMA_0
    gamma_r: float = GAMMA_R
    gamma_c: float = GAMMA_C
    lambda_up: float = LAMBDA_UP
    lambda_down: float = LAMBDA_DOWN
    l0: float = L0
    delta_r: float = DELTA_R
    delta_s: float = DELTA_S
    rho: float = RHO
    delta_p: float = DELTA_P
    eta_0: float = ETA_0
    eta_1: float = ETA_1
    kappa: float = KAPPA
    q_crit: float = Q_CRIT
    eta_w: float = ETA_W
    xi_w: float = XI_W
    delta_w_min: float = DELTA_W_MIN
    delta_w_max: float = DELTA_W_MAX
    w_transcend: float = W_TRANSCEND


DEFAULT_LIFECYCLE_CONSTANTS = LifecycleConstants()
