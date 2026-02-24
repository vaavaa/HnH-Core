# Tasks: 010 — Age Influence (Astrological Life Stages → 32D)

**Input**: Design documents from `specs/010-age-astrological-stages/`  
**Prerequisites**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md)

**Goal (010)**: Ввести возраст от birth_datetime_utc и injected_time_utc, 5 признаков астрологических стадий и ограниченную age_delta_32 в сборку 32D; детерминизм, границы, daily Lipschitz.

**Organization**: Tasks grouped by phase; [P] = parallel, [USn] = user story. Paths per plan.md.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel
- **[Story]**: US1 (age determinism), US2 (bounded 32D), US3 (stage timing), US4 (observability)

---

## Phase 1: Setup & constants

- [ ] T001 Verify feature branch 010-age-astrological-stages and dependencies (006, 002, 008, 009) per plan.md — Agent, BehavioralCore, assemble_state, 32D schema available

---

## Phase 2: Config and stage features

**Checkpoint**: AgeConfig and stage feature functions ready

- [ ] T002 Add AgeConfig in hnh/config/age_config.py: age_mode, age_strength, age_max_param_delta, age_daily_lipschitz, age_profile, age_max_years with spec defaults; age_mode in ("off", "on") else fail-fast; invalid numeric values (e.g. negative, zero where forbidden, out of valid range) MUST raise explicit error when config is used — document valid ranges and error type/message (spec Clarifications)
- [ ] T002b [P] Unit test: invalid AgeConfig (unknown age_mode, negative/out-of-range numeric values) raises documented error in tests/unit/test_010_age_config.py
- [ ] T003 [P] Add period constants (TROPICAL_YEAR_DAYS, SATURN_PERIOD_YEARS, JUPITER_PERIOD_YEARS, URANUS_PERIOD_YEARS, NODE_PERIOD_YEARS) in hnh/age/constants.py or hnh/age/stage_features.py
- [ ] T004 [P] Implement bump(age, center, width), sigmoid(x), age_years_from_delta_days(delta_days, age_max_years) in hnh/age/stage_features.py
- [ ] T005 [P] Implement maturity, saturn_event, jupiter_return, nodal_return, uranus_opposition and age_stage_features_v1(age_years) in hnh/age/stage_features.py; all values in [0,1]

---

## Phase 3: W_age and age_delta_32

**Checkpoint**: compute_age_delta_32 and Lipschitz ready

- [ ] T006 Implement W_age v1 matrix (5×32) per spec and compute_age_delta_32(features, age_strength, age_max_param_delta) in hnh/age/delta_32.py; per-parameter clamp
- [ ] T007 Implement apply_daily_lipschitz(prev_delta_32, raw_delta_32, L) in hnh/age/delta_32.py or hnh/age/engine.py
- [ ] T008 [P] Unit tests: age_years from two datetimes, bump/sigmoid, all 5 stage features at fixed ages, compute_age_delta_32 bounds, apply_daily_lipschitz cap (per call, not scaled by days) in tests/unit/test_010_stage_features.py and tests/unit/test_010_delta_32.py

---

## Phase 4: AgeEngine

**Checkpoint**: AgeEngine.compute() returns AgeOutput; state for Lipschitz

- [ ] T009 Implement AgeEngine(config) and compute(birth_datetime_utc, injected_time_utc) -> AgeOutput in hnh/age/engine.py; use stage_features_v1, compute_age_delta_32, apply_daily_lipschitz; update _last_age_delta_32
- [ ] T010 When birth_datetime_utc is missing and age_engine present (age_mode=on): MUST raise explicit error (fail-fast); document error type and message in engine or Agent (spec Clarifications)
- [ ] T011 [P] Unit test: AgeEngine.compute determinism and output shape; when birth_datetime_utc missing and age_mode=on, Agent or engine raises documented error in tests/unit/test_010_engine.py

---

## Phase 5: Integration — assembler, BehavioralCore, Agent, run_step_v2 (US1, US2, FR-199)

**Checkpoint**: All assembly inside Agent.step(); age_delta_32 and memory_delta flow into params_final; bounds and determinism

- [ ] T012 [US1][US2] Add age_delta_32: tuple[float, ...] | None = None to assemble_state in hnh/state/assembler.py; formula params_final[p] = clamp01(base + transit + mem[p] + age_delta_32[p]); length 32 check
- [ ] T013 [US1][US2] Add memory_delta=None, age_delta_32=None to BehavioralCore.apply_transits in hnh/state/behavioral_core.py; pass both to assemble_state
- [ ] T014 [US1] In Agent: optional age_config in constructor; if age_mode=on create AgeEngine, else _age_engine=None; step(date_or_dt, memory_delta=None) — accept optional memory_delta; get birth_datetime_utc from birth_data (if age_engine and missing → fail-fast); call _age_engine.compute(...) when present; call behavior.apply_transits(transit_state, memory_delta=memory_delta, age_delta_32=...) in hnh/agent.py
- [ ] T014a [FR-199] run_step_v2: delegate to Agent.step() whenever possible. Extend use_agent condition so that non-zero memory_delta does NOT skip delegation: when no phase and no transit_effect_history, call Agent with birth_data (from identity/natal_positions), pass memory_delta to Agent.step(dt_utc, memory_delta=memory_delta), and return result from agent (do not call assemble_state in run_step_v2 for this path). Refactor _run_step_v2_via_agent to accept and forward memory_delta to agent.step() in hnh/state/replay_v2.py
- [ ] T015 [US1] Integration test: same inputs → same step() output hashes (determinism); age_mode=on vs off, params_final differs when age differs; step with memory_delta matches expected assembly in tests/integration/test_010_age_integration.py
- [ ] T016 [US2] Assert max_abs(age_delta_32) <= age_max_param_delta in unit or integration test; params_final in [0,1]
- [ ] T016a [FR-199] Integration test: run_step_v2 with memory_delta (no phase) delegates to Agent.step(memory_delta=...) and params_final/axis_final match; no assemble_state called outside Agent for this path in tests/integration/test_010_replay_delegation.py or extend test_replay_v2

---

## Phase 6: Observability (US4)

**Checkpoint**: Debug output includes age fields when debug=True

- [ ] T017 [US4] When debug=True and age_engine used, add age_years, age_stage_features, age_delta_32_stats to the **object returned by step()** (e.g. extend StepResult), not a separate debug container (spec Clarifications) in hnh/agent.py
- [ ] T018 [US4] Test: debug=True and age_mode=on → step() return object includes age_years, age_stage_features, age_delta_32_stats; debug=False → backward compatible in tests/unit/test_010_agent_debug.py or integration

---

## Phase 7: Replay hash and polish (US3 optional)

- [ ] T019 Include age config fields (age_mode, age_strength, age_max_param_delta, age_daily_lipschitz, age_profile, age_max_years) in configuration_hash when age_mode=on in hnh/config/replay_config.py or equivalent
- [ ] T020 [US3] Optional: script or test that saturn_event peaks near quarter-cycle landmarks and uranus_opposition near ~42y (calibration/interpretability) in scripts/010/ or tests/. Success Criterion 5 (population guardrails): automated script/CI **not required** for 010 (calibration target only).
- [ ] T021 Constitution check: confirm determinism, no RNG, logging only when debug; note in plan.md or checklist
