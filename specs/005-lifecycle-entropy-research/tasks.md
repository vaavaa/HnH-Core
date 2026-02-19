# Tasks: 005 — Lifecycle & Entropy Model (Research Mode Only)

**Input**: Design documents from `specs/005-lifecycle-entropy-research/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/transit-stress.md

**Tests**: Spec 005 requires 99%+ coverage for lifecycle modules and explicit tests (fatigue growth/recovery, activity curve, death, will, transcendence, determinism over 10k steps).

**Organization**: Phase 1 — config & gating; Phase 2 — stress & fatigue; Phase 3 — activity & behavioral degradation; Phase 4 — death, will, transcendence; Phase 5 — integration & replay; Phase 6 — tests; Phase 7 — scripts & description files.

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)

## Path Conventions

- Package: `hnh/` (existing). New: `hnh/lifecycle/` (e.g. `stress.py`, `fatigue.py`, `engine.py`, `config.py`)
- Config: extend `hnh/config/replay_config.py` or add lifecycle config; replay-relevant lifecycle fields in configuration_hash
- Tests: `tests/unit/lifecycle/`, `tests/integration/` for long replay

---

## Phase 1: Config & Mode Gating

- [ ] T001 Add `mode` ("product" | "research"), `lifecycle_enabled: bool`, and optional `initial_f`, `initial_w` (default 0) to replay/lifecycle config; document in plan or contract (spec §3.1)
- [ ] T002 [P] Implement gating: when mode != "research" or lifecycle_enabled=false, no fatigue/will/death/psych_age; all lifecycle outputs disabled or identity pass-through
- [ ] T003 Include lifecycle-related config fields (mode, lifecycle_enabled, initial F/W, constants, transit-stress C_T and weights) in configuration_hash when lifecycle_enabled=true; document exact set in plan or contracts/transit-stress.md

---

## Phase 2: Transit Stress & Fatigue Engine

- [ ] T004 Implement raw transit intensity I_T(t) = Σ(hard_aspect_weight × orb_decay) per contracts/transit-stress.md (hard aspects: Conjunction, Opposition, Square; orb_decay = max(0, 1 - dev/orb)); reuse 002/004 aspect list
- [ ] T005 Implement S_T(t) = clip(I_T(t)/C_T, 0, 1) with C_T=3.0; unit test that 95th percentile S_T < 0.9 on representative aspect sets
- [ ] T006 Implement R from Stability axis (axis index 1): R = mean of 4 params of stability_regulation from current params or base; range [0,1]
- [ ] T007 Implement S_g = mean of 32 sensitivity parameters; input from Identity
- [ ] T008 Implement load(t), recovery(t), F(t+1) update per spec §5; all constants from config with defaults from spec
- [ ] T009 Implement L = L0*(1+delta_r*R)*(1-delta_s*S_g); q(t) = clip(F(t)/L, 0, 1)

---

## Phase 3: Activity Suppression & Behavioral Degradation

- [ ] T010 Implement A_g(t) = clip(1 - q^rho, 0, 1), rho=2.5; unit tests for curve (minimal suppression q<0.4, strong q>0.8)
- [ ] T011 Apply effective_transit_delta = A_g × sensitivity × transit_delta and effective_memory_delta = A_g × memory_delta in lifecycle-aware pipeline
- [ ] T012 Implement behavioral degradation for activity-sensitive params (initiative, curiosity, persistence, pacing, challenge_level, verbosity): x_p -= delta_p*(1-A_g), clamp [0,1]; cap absolute reduction at 0.1
- [ ] T013 Map parameter names to Spec 002 indices (hnh/identity/schema.py) for degradation step

---

## Phase 4: Psychological Age, Death, Will, Transcendence

- [ ] T014 Implement Age_psy(t) = A(t)*(eta_0 + eta_1*q^kappa); optional in log
- [ ] T015 Implement death condition: if F(t) >= L then state=DISABLED; freeze params; stop memory/transit updates; log final snapshot
- [ ] T016 Implement daily v(t)=A_g*S_T, burn(t)=max(0, q - q_crit); at death compute delta_W = eta_w*mean(v) - xi_w*mean(burn); clamp delta_W in [-0.03, +0.02]; W = clip(W + delta_W, 0, 1)
- [ ] T017 Implement transcendence: if W >= 0.995 then state=TRANSCENDED; fatigue disabled; no further modulation; personality frozen
- [ ] T018 Ensure running mean for v(t) and burn(t) over lifetime is O(1) per day (e.g. running sum/count or closed form)

---

## Phase 5: Integration & Replay

- [ ] T019 Integrate lifecycle step with replay pipeline: after run_step_v2 (or equivalent), if research+lifecycle_enabled call lifecycle engine with S_T, R, S_g, F, W; return F', W', A_g, state, effective_deltas
- [ ] T020 Add lifecycle state to replay signature per spec §9.2: initial F(0), W(0), and per-step (or at end) F(t), W(t), state, optionally A_g(t), q(t); document exact list in plan or data-model.md
- [ ] T021 Document integration point and data flow in plan or quickstart; document final snapshot contents (§9.1) in data-model or contract

---

## Phase 6: Tests (Spec §14)

- [ ] T022 Unit tests: fatigue growth (load > recovery → F increases), recovery decay (recovery > load → F decreases)
- [ ] T023 Unit tests: activity suppression curve A_g(q) for q in [0, 0.4, 0.8, 1.0]
- [ ] T024 Unit tests: death trigger when F >= L; state DISABLED; no further updates
- [ ] T025 Unit tests: will accumulation and decay (delta_W clamp, W update at death)
- [ ] T026 Unit tests: transcendence trigger W >= 0.995; state TRANSCENDED
- [ ] T027 Integration test: deterministic replay over 10,000 steps — same inputs → same F, W, state trajectory
- [ ] T028 Validation (optional): 10k agents simulation; median lifespan > 800y; transcendence rate < 1%
- [ ] T029 Coverage 99%+ for hnh/lifecycle/

---

## Phase 7: Scripts & description files (scripts/005)

- [ ] T030 Create folder scripts/005 and README.md: описание спеки 005, требования (venv, опции установки), таблица скриптов с описанием и опциями CLI; ссылка на specs/005-lifecycle-entropy-research/ (plan § Scripts & demos)
- [ ] T031 [P] Add scripts/005/01_lifecycle_formulas_demo.py: демо формул без hnh.lifecycle (S_T, load, recovery, F update, L, q, A_g, Age_psy за несколько шагов с фиктивными входами); runnable из корня проекта
- [ ] T032 After Phase 5: add scripts/005/02_transit_stress.py — I_T, S_T из аспектов (contract transit-stress)
- [ ] T033 After Phase 5: add scripts/005/03_fatigue_engine.py — траектория F(t), q(t) за N дней
- [ ] T034 After Phase 5: add scripts/005/04_activity_suppression.py — A_g, effective deltas, деградация 6 параметров
- [ ] T035 After Phase 5: add scripts/005/05_death_and_will.py — смерть, снапшот, delta_W, W update
- [ ] T036 After Phase 5: add scripts/005/06_transcendence.py — W >= 0.995, state TRANSCENDED
- [ ] T037 After Phase 5: add scripts/005/07_lifecycle_replay.py — полный шаг с lifecycle, replay signature, проверка детерминизма
- [ ] T038 After Phase 5: add scripts/005/08_life_simulation_lifecycle.py — симуляция жизни с lifecycle (F, W, A_g, state; опции --days, --lives, --seed, --no-lifecycle)
- [ ] T039 Optional: add scripts/005/README.en.md if project convention requires English duplicate

---

## Checkpoints

- **After Phase 2**: S_T, F, L, q computable; unit tests pass.
- **After Phase 4**: Death, will, transcendence implemented; running means O(1).
- **After Phase 6**: Full replay deterministic; 99% coverage; acceptance criteria met.
- **After Phase 7**: scripts/005/README.md and demos in place; 01_lifecycle_formulas_demo.py runnable; remaining scripts use hnh/lifecycle when implemented.
