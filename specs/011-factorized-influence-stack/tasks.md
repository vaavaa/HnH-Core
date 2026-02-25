# Tasks: 011 — Factorized Influence Stack (Mini-Rule) + Contribution Logging

**Input**: [spec.md](spec.md), [plan.md](plan.md)  
**Depends on**: 002, 006, 009, 010

**Goal**: Ввести протокол Factor, StepContext, FactorStack; единая точка интеграции в Agent.step(); структурированный factor_breakdown при debug; явные границы baseline-diff; обратная совместимость по умолчанию.

---

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel

---

## Phase 1: Types and protocol

- [ ] T001 Add Vector32 type alias (tuple[float, ...] length 32) and StepContext dataclass/immutable snapshot (fields per FR-001/FR-002: natal, transit_state, transit_delta_eff, age_delta_32, memory_delta_32, config, date, etc.) in hnh/factors/ or equivalent
- [ ] T002 Define Factor protocol (name, kind: Literal["producer","transform"], apply(ctx, delta_in) -> Vector32) and document producer vs transform semantics
- [ ] T003 [P] Unit tests: StepContext immutability, Factor protocol compliance for a minimal producer and a minimal transform

---

## Phase 2: FactorStack and config

- [ ] T004 Implement FactorStack: ordered list of factors, run(ctx, debug_factors=False) -> (delta_total_32, factor_breakdown | None); accumulation order per spec (Transit → SexScale → Age → Memory → FinalCap)
- [ ] T005 Add config keys to ReplayConfig (or dedicated config): factor_stack_mode, debug_factors, delta_budget_mode, final_delta_cap, baseline_diff_max_abs_param, baseline_diff_max_abs_axis with spec defaults; include in configuration_hash / replay signature
- [ ] T006 [P] Implement optional FinalBudgetCapFactor (transform) when delta_budget_mode="scale_to_cap"; apply per-parameter cap per FR-003
- [ ] T007 [P] Unit tests: FactorStack run determinism; factor_breakdown schema (name, kind, mean_abs_delta, max_abs_delta, axis_mean_abs_delta[8]); delta_total_stats

---

## Phase 3: Concrete factors (v1)

- [ ] T008 Implement TransitDeltaFactor (producer): from StepContext.transit_delta_eff (or equivalent), return bounded 32D delta per 002
- [ ] T009 Implement SexTransitScaleFactor (transform): apply 009 scale_delta to delta_in (transit delta); input from previous factor
- [ ] T010 Implement AgeDeltaFactor (producer): from StepContext.age_delta_32
- [ ] T011 Implement MemoryDeltaFactor (producer): from StepContext.memory_delta_32
- [ ] T012 Wire FactorStack v1 order: TransitDeltaFactor → SexTransitScaleFactor → AgeDeltaFactor → MemoryDeltaFactor → [FinalBudgetCapFactor if enabled]
- [ ] T013 [P] Unit tests: each factor apply() returns Vector32; transforms receive correct delta_in; producers ignore delta_in

---

## Phase 4: Agent.step() integration

- [ ] T014 In Agent.step(date): when factor_stack_mode="on", build StepContext from natal, TransitEngine.state(), transit_delta_eff, age_delta_32, memory_delta_32, config, date; call FactorStack.run(ctx, debug_factors); use delta_total_32 for assemble params_final/axis_final
- [ ] T015 When factor_stack_mode="off", preserve legacy path exactly (no FactorStack call); assert output unchanged (tolerance 1e-9) vs pre-011 implementation
- [ ] T016 When debug_factors=True and factor_stack_mode="on", attach factor_breakdown and delta_total_stats to step result / state_log per FR-004, FR-005
- [ ] T017 [P] Integration tests: Agent.step() with factor_stack_mode=on/off; determinism (T-011-02); backward compat (T-011-04)

---

## Phase 5: Tests (spec-mandated)

- [ ] T018 T-011-01: Test that factor_breakdown contributions sum to delta_total_32 (within 1e-9)
- [ ] T019 T-011-02: Test determinism — two step() calls with same inputs yield identical params_final, axis_final, factor_breakdown, delta_total_stats
- [ ] T020 T-011-03: Test baseline-diff bounds — age_mode=off vs age_mode=on; max_abs_param_diff <= baseline_diff_max_abs_param (0.08), max_abs_axis_diff <= baseline_diff_max_abs_axis (0.04)
- [ ] T021 T-011-04: Test backward compatible default — factor_stack_mode=off matches legacy output (golden or replay logs, tolerance 1e-9)

---

## Phase 6: Edge cases and hashes

- [ ] T022 Factor list or order change MUST update configuration_hash or factor_stack_hash so replay detects it; document in contract
- [ ] T023 Edge cases: missing sex with sex_transit_mode=scale_delta (per 009); age_mode=on without birth date (fail-fast per 010); missing ephemeris (factor framework unchanged)
- [ ] T024 [P] Logging: when state logging enabled, include factor_breakdown and delta_total_stats (JSON-compatible, stable ordering) per FR-005
