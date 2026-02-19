# Feature Specification: HnH 005 — Lifecycle & Entropy Model (Research Mode Only)

**Feature Branch**: `005-lifecycle-entropy-research`  
**Created**: 2025-02-19  
**Status**: Draft  
**Implementation plan**: [plan.md](plan.md) · **Tasks**: [tasks.md](tasks.md)  
**Input**: Introduce a deterministic Lifecycle & Entropy layer on top of the stable 32-parameter planetary model; Research Mode only.

---

## Clarifications

### Session 2025-02-19

- Q: Откуда берётся R (resilience) для load/recovery и L: из base_vector или из params_final на шаге t? → A: R = mean of 4 parameters of Stability axis from **base_vector** (constant per identity).
- Q: В каких единицах A(t) и Age_psy в формуле психологического возраста? → A: A(t) в днях; Age_psy выводится в годах (конвертация при выводе).
- Q: Если F(0) ≥ L или W(0) ≥ 0.995 в начале прогона — как вести себя? → A: Сразу применить death/transcendence **до** первого шага (state = DISABLED или TRANSCENDED, шаг 0 не выполнять).
- Q: Финальный снапшот: требовать orjson и/или фиксированную схему? → A: **orjson** обязателен для сериализации снапшота при записи в лог; точная схема полей — в плане/контракте.
- Q: Что такое «accelerated mode» в «median lifespan > 800 years (accelerated mode)»? → A: Не отдельный режим: целевая метрика валидации при **дефолтных** константах спеки (проверка в тестах/скриптах).

---

## 1. Objective

Introduce a deterministic **Lifecycle & Entropy** layer on top of the stable 32-parameter planetary model.

Design constraints:

- Activity suppression must scale smoothly and conservatively
- Death must be rare
- Will growth must be rare
- Transcendence must be extremely rare and achievable only under exceptional natal configurations
- Deterministic replay must remain intact
- Production Mode must remain unaffected

Lifecycle logic MUST operate only in **Research Mode**.

---

## 2. Mode Gating

Lifecycle logic is active only if:

- `mode = "research"`
- `lifecycle_enabled = true`

In **Product Mode**:

- Fatigue = disabled
- Will = disabled
- Death = disabled
- Psychological age = disabled

---

## 3. Definitions

**Time step:** 1 day

**Variables:**

| Symbol   | Range / Constraint | Description |
|----------|--------------------|-------------|
| F(t)     | ≥ 0                | Fatigue index |
| L        | > 0                | Fatigue limit (death threshold) |
| q(t)     | [0, 1]             | q(t) = clip(F(t)/L, 0, 1) |
| A_g(t)   | [0, 1]             | Activity factor |
| W        | [0, 1]             | Spiritual will |
| R        | [0, 1]             | Resilience: mean of 4 params of Stability axis from **base_vector** (constant per identity; Spec 002) |
| S_g      | [0, 1]             | Global sensitivity (mean of 32 sensitivity parameters) |
| S_T(t)   | [0, 1]             | Normalized daily transit stress |

All values MUST remain bounded and deterministic.

### 3.1 Initial state (F, W)

- **Initial fatigue** F(0) and **initial will** W(0) are part of lifecycle state and MUST be set explicitly (config or API).
- **Defaults**: F(0) = 0, W(0) = 0 when not specified.
- Both initial F and initial W are **replay-relevant**: they MUST be included in the replay signature (or in the serialized lifecycle state) when lifecycle is enabled, so that identical inputs — including F(0) and W(0) — yield identical evolution.
- Implementations MUST document where F(0) and W(0) are read from (e.g. `lifecycle_config.initial_f`, `lifecycle_config.initial_w`).

---

## 4. Transit Stress Normalization

**Raw transit intensity:**

```
I_T(t) = Σ (hard_aspect_weight × orb_decay)
```

Sum over **hard aspects** only; weights and orb_decay formula are fixed for determinism. **Contract**: [contracts/transit-stress.md](contracts/transit-stress.md) defines which aspects count as hard (Conjunction, Opposition, Square), per-aspect weight, and orb_decay (linear falloff: max(0, 1 − dev/orb)).

**Normalize:**

```
S_T(t) = clip(I_T(t) / C_T, 0, 1)
```

**Default:** `C_T = 3.0`

95th percentile S_T should remain < 0.9 (calibration target; see contract).

---

## 5. Fatigue Engine

### 5.1 Daily Load

```
shock_multiplier(t) = 1 + alpha_shock   if S_T(t) >= theta_shock
                      else 1
```

**Defaults:** `theta_shock = 0.90`, `alpha_shock = 0.6`

**Load:**

```
load(t) = shock_multiplier(t)
          × S_T(t)
          × (1 + beta_s × S_g)
          × (1 - beta_r × R)
```

**Defaults:** `beta_s = 0.6`, `beta_r = 0.7`

### 5.2 Recovery

```
recovery(t) = gamma_0
              + gamma_r × R
              + gamma_c × (1 - S_T(t))
```

**Defaults:** `gamma_0 = 0.12`, `gamma_r = 0.30`, `gamma_c = 0.20`

### 5.3 Update Rule

```
F(t+1) = max(0,
             F(t)
             + lambda_up × load(t)
             - lambda_down × recovery(t))
```

**Defaults:** `lambda_up = 0.010`, `lambda_down = 0.009`

These values ensure death is rare under normal conditions.

---

## 6. Fatigue Limit (Rare Death)

```
L = L0 × (1 + delta_r × R) × (1 - delta_s × S_g)
```

**Defaults:** `L0 = 14.0`, `delta_r = 0.8`, `delta_s = 0.5`

**Expected outcome (validation target with default constants):**

- Median lifespan > 800 years when running many agents with spec defaults (to be checked in tests/scripts; no separate "accelerated" config).
- Death rare unless repeated high-stress cycles.

---

## 7. Activity Suppression (Smooth Scaling)

**Activity factor:**

```
A_g(t) = clip(1 - q(t)^rho, 0, 1)
```

**Default:** `rho = 2.5`

**Properties:**

- Minimal suppression when q < 0.4
- Strong suppression when q > 0.8

### 7.1 Suppression Effects

**Transit modulation:**

```
effective_transit_delta = A_g(t) × sensitivity × transit_delta
```

**Memory drift:**

```
effective_memory_delta = A_g(t) × memory_delta
```

### 7.2 Behavioral Degradation

For **activity-sensitive parameters** (Spec 002 parameter names):

- initiative, curiosity, persistence (axis motivation_drive)
- pacing, challenge_level (axis teaching_style)
- verbosity (axis communication_style)

Apply:

```
x_p(t) = clip(x_p(t) - delta_p × (1 - A_g(t)), 0, 1)
```

**Default:** `delta_p = 0.08`

Suppression MUST NOT exceed 0.1 absolute reduction per parameter.

---

## 8. Psychological Age

**Chronological age:** A(t) — в **днях** (согласовано с time step 1 day).

**Psychological age (формула в днях):**

```
Age_psy_raw(t) = A(t) × (eta_0 + eta_1 × q(t)^kappa)
```

**Output:** Age_psy в **годах**; реализация MUST конвертировать при выводе (например Age_psy_years = Age_psy_raw / 365.25 или эквивалент). Лог и API отдают возраст в годах.

**Defaults:** `eta_0 = 0.80`, `eta_1 = 0.45`, `kappa = 2.0`

Low fatigue → psychologically younger. High fatigue → accelerated aging.

---

## 9. Death Condition

**If** `F(t) >= L` **then:**

- state = DISABLED
- Freeze all behavioral parameters
- Stop memory updates
- Stop transit modulation
- Log final snapshot (§9.1)
- Replay signature for the run MUST include lifecycle snapshot fields (§9.2)

Death MUST occur only under sustained high stress.

**Edge case — start of run:** If F(0) ≥ L or W(0) ≥ 0.995 at initialization, the engine MUST apply death or transcendence **before** the first step: set state = DISABLED (if F(0) ≥ L) or TRANSCENDED (if W(0) ≥ 0.995), do not run step 0, log snapshot if applicable.

### 9.1 Final snapshot contents

When state becomes DISABLED (or TRANSCENDED), the engine MUST produce a **lifecycle snapshot** that is logged and MAY be included in the replay payload. Snapshot MUST contain at least:

| Field | Type | Notes |
|-------|------|--------|
| F | float | Fatigue at death/transcendence |
| L | float | Fatigue limit used |
| q | float | F/L clipped |
| W | float | Will after final update (at death) or current W (at transcendence) |
| state | string | DISABLED or TRANSCENDED |
| sum_v | float | Lifetime sum of v(t) (for mean(v)) |
| sum_burn | float | Lifetime sum of burn(t) |
| count_days | int | Days lived |
| params_final | tuple[float, ...] | 32 params at freeze |
| axis_final | tuple[float, ...] | 8 axes at freeze |
| Age_psy | float (optional) | Psychological age at end, in years |

Additional implementation-defined fields are allowed; replay-relevant fields MUST be listed in the implementation contract so that replay consistency is verifiable.

**Serialization:** When the snapshot is written to a log or external storage, it MUST be serialized with **orjson** (per Spec 003). Exact field schema and ordering are defined in the implementation plan or contract.

### 9.2 Replay signature (lifecycle)

When `mode = "research"` and `lifecycle_enabled = true`, the **replay signature** (or the structure used to verify deterministic replay) MUST include lifecycle state so that two runs with the same inputs produce the same trajectory. At minimum, include:

- initial F(0), initial W(0)
- configuration_hash (already including lifecycle constants and mode/lifecycle_enabled)
- For each step (or at end): F(t), W(t), state, and optionally A_g(t), q(t)

Implementations MUST document the exact set of lifecycle fields included in the replay signature (e.g. in plan or contracts) so that tests can assert equality between runs.

---

## 10. Spiritual Will (Rare Growth)

### 10.1 Daily Will Signal

```
v(t) = A_g(t) × S_T(t)
```

**Burn penalty:**

```
burn(t) = max(0, q(t) - q_crit)
```

**Default:** `q_crit = 0.75`

### 10.2 Lifetime Will Update

At death:

```
delta_W = eta_w × mean(v(t)) - xi_w × mean(burn(t))
```

**Defaults:** `eta_w = 0.12`, `xi_w = 0.30`

**Clamp:** `delta_W ∈ [-0.03, +0.02]`

**Update:** `W = clip(W + delta_W, 0, 1)`

Growth MUST be slow and rare.

---

## 11. Transcendence (Extremely Rare)

**Condition:** `W >= 0.995`

**When triggered:**

- state = TRANSCENDED
- Fatigue disabled
- No further modulation
- Personality frozen in stable profile
- No further rebirth

Transcendence probability MUST be < 1% across 10,000 simulated agents.

**Edge case — start of run:** If W(0) ≥ 0.995, set state = TRANSCENDED before the first step (§9 edge case).

---

## 12. Determinism Requirements

Given identical:

- natal data
- transit data
- **initial F(0)** and **initial W(0)**
- configuration (including all lifecycle constants and mode/lifecycle_enabled)
- time input

Lifecycle evolution MUST be identical.

No random operations allowed.

---

## 13. Performance Constraints

- All updates O(1) per day
- No historical scans (use running averages where needed)
- Support ≥ 2000 year simulation
- No floating drift beyond 1e-6 per 10,000 steps

---

## 14. Test Requirements

Coverage target: **99%+** for lifecycle modules.

Must test:

- fatigue growth
- recovery decay
- activity suppression curve
- rare death trigger
- will accumulation
- will decay
- transcendence threshold
- deterministic replay over 10,000 steps

---

## 15. Acceptance Criteria

Feature complete when:

- Death occurs rarely
- Activity suppression is gradual
- Will rarely increases
- Transcendence almost unreachable without extreme resilience
- 32D model remains numerically stable
- Production mode unaffected
- 99% coverage achieved for lifecycle modules

---

## 16. References

- Spec 001: Deterministic engine, state logging, replay.
- Spec 002: 32 parameters, axes, natal sensitivity, transits, replay_config.
- Spec 003: orjson, xxhash; no stdlib json in core.
- Spec 004: Planetary core, zodiac layer; lifecycle compatibility (fatigue via planetary modulation).
- **Contract**: [005 — Transit Stress](contracts/transit-stress.md): hard aspects, orb_decay, I_T/S_T for determinism.
- Project: `hnh/state/replay_v2.py`, `hnh/modulation/delta.py`, `hnh/identity/schema.py`.
