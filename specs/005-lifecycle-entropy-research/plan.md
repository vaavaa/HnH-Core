# Implementation Plan: 005 — Lifecycle & Entropy Model (Research Mode Only)

**Branch**: `005-lifecycle-entropy-research` | **Date**: 2025-02-19 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/005-lifecycle-entropy-research/spec.md`.  
**Clarifications**: Session 2025-02-19 (see spec § Clarifications) — R from base_vector; Age_psy output in years; edge case F(0)≥L / W(0)≥0.995 before first step; orjson for snapshot; median lifespan > 800y = validation target with defaults.

---

## Summary

Introduce a deterministic **Lifecycle & Entropy** layer: fatigue F(t), limit L, activity factor A_g(t), psychological age, death condition, spiritual will W, transcendence. Active only when `mode = "research"` and `lifecycle_enabled = true`. All formulas O(1) per day; no historical scans; running averages where needed. Production mode unchanged. Integration point: replay/state pipeline (e.g. after `run_step_v2` or in a wrapper that gates lifecycle when enabled).

---

## Technical Context

**Language/Version**: Python 3.12 (existing HnH stack)  
**Dependencies**: Existing 002/003/004 (orjson, xxhash, replay_config, 32-param schema)  
**Testing**: pytest; 99%+ coverage for lifecycle modules  
**Constraints**: Deterministic; Research Mode only; no impact on Product Mode  
**Performance**: O(1) per day; support ≥ 2000 year simulation; float stability 1e-6 per 10k steps

---

## Constitution Check

- [ ] **Deterministic Mode**: Lifecycle evolution deterministic; same inputs → same F, W, state; no randomness.
- [ ] **Mode gating**: Lifecycle logic only when mode=research and lifecycle_enabled=true; Product Mode untouched.
- [ ] **Identity/Core**: Lifecycle may freeze params at death/transcendence but does not mutate Identity Core (base_vector, sensitivity_vector); state = DISABLED/TRANSCENDED is explicit.
- [ ] **Logging**: Final snapshot at death; lifecycle fields optional in log when research mode.
- [ ] **Repository standards**: Python, orjson, xxhash, pytest; config for lifecycle constants.

---

## Implementation Outline

1. **Config & gating**  
   Add `mode`, `lifecycle_enabled`, and optional `initial_f`, `initial_w` (default 0) to replay (or lifecycle) config. Initial F(0), W(0) are replay-relevant (spec §3.1). In Product Mode or when lifecycle_enabled=false, skip all lifecycle logic; no F, W, A_g, death, transcendence.

2. **Transit stress**  
   Per contract [contracts/transit-stress.md](contracts/transit-stress.md): hard aspects = Conjunction, Opposition, Square; orb_decay = max(0, 1 − dev/orb). Module: compute I_T(t) = Σ(hard_aspect_weight × orb_decay); S_T(t) = clip(I_T/C_T, 0, 1). C_T = 3.0 default; calibrate so 95th percentile S_T < 0.9.

3. **Fatigue engine**  
   Inputs: S_T(t), R (from **base_vector** Stability axis — constant per identity), S_g (mean sensitivity). Compute load(t), recovery(t); update F(t+1) = max(0, F(t) + lambda_up*load - lambda_down*recovery). L = L0*(1+delta_r*R)*(1-delta_s*S_g). q(t) = clip(F(t)/L, 0, 1). At init: if F(0)≥L or W(0)≥0.995, set state DISABLED/TRANSCENDED before first step.

4. **Activity suppression**  
   A_g(t) = clip(1 - q^rho, 0, 1), rho=2.5. Apply to transit_delta and memory_delta (effective = A_g × raw). Behavioral degradation for activity-sensitive params (initiative, curiosity, persistence, pacing, challenge_level, verbosity): x_p -= delta_p*(1-A_g), clamp; cap absolute reduction at 0.1.

5. **Psychological age**  
   Age_psy_raw(t) = A(t) × (eta_0 + eta_1 × q(t)^kappa) with A(t) in days; **output Age_psy in years** (convert when logging/API). Optional log field in research mode.

6. **Death**  
   If F(t) >= L: state = DISABLED; freeze params; stop memory/transit updates; log final snapshot (**orjson** when writing to log; schema in plan/contract). Compute delta_W from lifetime v(t) and burn(t); update W = clip(W + delta_W, 0, 1); clamp delta_W in [-0.03, +0.02].

7. **Will & transcendence**  
   Daily v(t) = A_g*S_T, burn(t) = max(0, q - q_crit). Will update only at death. If W >= 0.995: state = TRANSCENDED; fatigue off; no further modulation; personality frozen.

8. **Replay & tests**  
   Replay signature when lifecycle enabled MUST include initial F(0), W(0), configuration_hash, and per-step (or at end) F(t), W(t), state, optionally A_g(t), q(t) (spec §9.2). Final snapshot at death/transcendence MUST include at least F, L, q, W, state, sum_v, sum_burn, count_days, params_final, axis_final (§9.1). Document exact snapshot and signature fields in data-model or contract. Deterministic replay over 10k+ steps; tests for fatigue growth, recovery, suppression curve, rare death, will accumulation/decay, transcendence threshold.

---

## Constants Summary (defaults)

| Symbol | Default | Notes |
|--------|---------|--------|
| C_T | 3.0 | Transit stress normalization |
| theta_shock | 0.90 | Shock threshold for S_T |
| alpha_shock | 0.6 | Shock multiplier increment |
| beta_s | 0.6 | Sensitivity factor in load |
| beta_r | 0.7 | Resilience factor in load |
| gamma_0 | 0.12 | Recovery constant |
| gamma_r | 0.30 | Recovery from R |
| gamma_c | 0.20 | Recovery from low S_T |
| lambda_up | 0.010 | Fatigue accumulation |
| lambda_down | 0.009 | Fatigue recovery rate |
| L0 | 14.0 | Base fatigue limit |
| delta_r | 0.8 | R scaling for L |
| delta_s | 0.5 | S_g scaling for L |
| rho | 2.5 | Activity suppression exponent |
| delta_p | 0.08 | Behavioral degradation strength |
| eta_0, eta_1, kappa | 0.80, 0.45, 2.0 | Psychological age |
| q_crit | 0.75 | Will burn threshold |
| eta_w | 0.12 | Will growth at death |
| xi_w | 0.30 | Will penalty at death |
| W_transcend | 0.995 | Transcendence threshold |

---

## Project Structure

- **New module**: `hnh/lifecycle/` (e.g. `fatigue.py`, `stress.py`, `will.py`, or single `engine.py`).
- **Config**: Lifecycle constants and mode in `ReplayConfig` or dedicated `LifecycleConfig`; replay-relevant fields in configuration_hash when lifecycle enabled.
- **Integration**: Call lifecycle step after (or inside) replay step when mode=research and lifecycle_enabled=true; pass S_T, R, S_g, current F, W; return updated F, W, A_g, state, effective_deltas.
- **Scripts & demos**: папка **scripts/005/** — скрипты, демонстрирующие функционал 005 (режим research, усталость, активность, смерть, воля, трансценденция). Файлы описания по аналогии с 001/002/004: README.md в scripts/005 с таблицей скриптов и инструкцией по запуску; при необходимости README.en.md.

---

## Scripts & demos (scripts/005)

Цель: после реализации 005 в папке **scripts/005** должны быть скрипты и описание, по аналогии с scripts/002 и scripts/004.

**Содержимое:**

1. **README.md** — краткое описание спецификации 005, требования (venv, опционально `pip install -e ".[astrology]"` для полного пайплайна), таблица скриптов с описанием и опциями командной строки. Ссылка на спеки specs/005-lifecycle-entropy-research/.
2. **Опционально README.en.md** — то же на английском, если в проекте принято дублировать описание (как в 001).

**Планируемые скрипты** (реализуются по мере готовности hnh/lifecycle):

| Скрипт | Назначение |
|--------|------------|
| 01_lifecycle_formulas_demo.py | Демо формул без зависимости от hnh.lifecycle: S_T, load/recovery, F(t+1), L, q, A_g, психовозраст — несколько шагов с фиктивными S_T, R, S_g. Показывает логику спеки до появления модуля. |
| 02_transit_stress.py | I_T(t), S_T(t) из аспектов (контракт transit-stress); при наличии 002/004 — реальные транзиты. |
| 03_fatigue_engine.py | Движок усталости: load, recovery, F, L, q за N дней; вывод траектории F(t), q(t). |
| 04_activity_suppression.py | A_g(q), effective_transit_delta и effective_memory_delta, деградация шести параметров. |
| 05_death_and_will.py | Условие смерти F >= L, финальный снапшот, delta_W и обновление W при смерти. |
| 06_transcendence.py | Порог W >= 0.995, state TRANSCENDED, заморозка профиля. |
| 07_lifecycle_replay.py | Полный шаг с lifecycle (research + lifecycle_enabled): подпись реплея, детерминизм (два прогона с одинаковыми входами → одинаковые F, W, state). |
| 08_life_simulation_lifecycle.py | Симуляция жизни с lifecycle: одна или несколько жизней, по дням, вывод F, W, A_g, state; при смерти — снапшот; опции --days, --lives, --seed, --no-lifecycle (сравнение с 002). |

Порядок создания: README.md и 01_lifecycle_formulas_demo.py можно сделать сразу (демо формул не требует hnh/lifecycle). Остальные скрипты — после Phase 5 интеграции (T019–T021).

---

## Risks & Mitigations

- **Float drift**: Use running averages with bounded history or closed form; avoid cumulative sum over 2000 years without periodic normalization or stable formulation.
- **Death too frequent**: Tune lambda_up/lambda_down, L0, delta_r, delta_s; validation target median lifespan > 800y with **default constants** (no separate "accelerated" mode; check in tests/scripts).
- **Transcendence too easy**: Keep W update clamped and xi_w high; validate < 1% transcendence in 10k agents.
