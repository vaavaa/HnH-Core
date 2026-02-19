# Data Model: 005 — Lifecycle & Entropy (Research Mode)

Entities and structures introduced by 005. All lifecycle state is active only when `mode = "research"` and `lifecycle_enabled = true`.

## 1. Lifecycle state (per identity / run)

**Initial state (replay-relevant):**

| Field | Type | Notes |
|-------|------|--------|
| F(0) | float ≥ 0 | Initial fatigue; default 0 |
| W(0) | float [0, 1] | Initial will; default 0 |

Both MUST be set via config or API and MUST be part of replay signature when lifecycle enabled (spec §3.1, §12).

**Per-step state:**

| Field | Type | Notes |
|-------|------|--------|
| F | float ≥ 0 | Fatigue index |
| L | float > 0 | Fatigue limit (death threshold) |
| q | float [0, 1] | F/L clipped |
| A_g | float [0, 1] | Activity factor |
| W | float [0, 1] | Spiritual will |
| state | enum | ALIVE \| DISABLED \| TRANSCENDED |
| Age_psy | float (optional) | Psychological age (for log) |

Running aggregates (O(1) per day) for will update at death:

| Field | Type | Notes |
|-------|------|--------|
| sum_v | float | Sum of v(t) over lifetime |
| sum_burn | float | Sum of burn(t) over lifetime |
| count_days | int | Number of days (for mean) |

## 2. Inputs (per step)

| Symbol | Source | Notes |
|--------|--------|--------|
| S_T(t) | Aspects | clip(I_T/C_T, 0, 1) |
| R | Stability axis | Mean of 4 params (axis index 1) |
| S_g | Identity | Mean of 32 sensitivity params |
| A(t) | Time | Chronological age in days (or years) |

## 3. Config (replay-relevant when lifecycle enabled)

All constants from spec §4–§11 (C_T, theta_shock, alpha_shock, beta_s, beta_r, gamma_*, lambda_*, L0, delta_r, delta_s, rho, delta_p, eta_0, eta_1, kappa, q_crit, eta_w, xi_w, W_transcend). **Initial F(0), W(0)** (if configurable) and **mode**, **lifecycle_enabled** must be part of configuration_hash (or replay signature) when lifecycle is used. Transit-stress constants (C_T, hard aspect weights, orb source) used for I_T/S_T — see [contracts/transit-stress.md](contracts/transit-stress.md) — MUST be included in configuration_hash when lifecycle enabled.

## 4. Activity-sensitive parameters (Spec 002)

Parameter names for behavioral degradation (§7.2): initiative, curiosity, persistence, pacing, challenge_level, verbosity. Indices from `hnh/identity/schema.py` (PARAMETERS tuple).

## 5. Lifecycle snapshot and replay signature

**Final snapshot** (spec §9.1): at state DISABLED or TRANSCENDED, the logged snapshot MUST include at least: F, L, q, W, state, sum_v, sum_burn, count_days, params_final, axis_final; optionally Age_psy. Exact set is implementation-defined but MUST be documented for replay consistency.

**Replay signature** (spec §9.2): when lifecycle enabled, the structure used to verify deterministic replay MUST include initial F(0), W(0), configuration_hash, and per-step (or at end) lifecycle state: F(t), W(t), state, and optionally A_g(t), q(t). Implementation MUST document the exact list of lifecycle fields in the signature.

## 6. Integration with 002

- **effective_transit_delta** = A_g × (sensitivity × transit_delta)  
- **effective_memory_delta** = A_g × memory_delta  
- **params_final**: after 002 assembler, optionally apply degradation to the 6 activity-sensitive params (cap 0.1 reduction).  
- At state DISABLED or TRANSCENDED: no further updates to params, memory, or F/W (except W update once at death before marking DISABLED).
