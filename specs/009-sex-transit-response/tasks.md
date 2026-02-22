# Tasks: 009 — Sex Affects Transit Response (Dynamic Modulation)

**Input**: Design documents from `specs/009-sex-transit-response/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Goal (009)**: Sex affects personality **over the whole span of life**, not only in the natal chart (008): transit-driven deltas (d_*) at every step are modulated by sex, so identity *expression* along the life trajectory is sex-dependent.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. Tests are included per plan (unit, integration, calibration).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Repository**: `hnh/`, `tests/`, `scripts/` at repo root (per plan.md Target Package Layout)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify feature environment and dependencies

- [ ] T001 Verify feature branch 009-sex-transit-response and dependencies (008, 006) per specs/009-sex-transit-response/plan.md — ensure 008 identity (E, W32_V1) and 006 Agent/BehavioralCore/TransitState are available

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Config, validation, Wdyn registry, and SexTransitModulator — MUST be complete before any user story

**Checkpoint**: Foundation ready — user story implementation can begin

- [ ] T002 Add 009 config fields (sex_transit_mode, sex_transit_beta, sex_transit_mcap, sex_transit_Wdyn_profile) with defaults off, 0.05, 0.10, "v1" in hnh/config/replay_config.py or a dedicated 009 config dataclass used by Agent (per plan; ReplayConfig may be frozen)
- [ ] T003 Implement 009 config resolution (Agent config over ReplayConfig) and document resolution order in hnh/agent.py or in a helper in hnh/config/
- [ ] T004 Implement validation: invalid sex_transit_mode (not in off/scale_delta/scale_sensitivity) or unknown sex_transit_Wdyn_profile → fail-fast with explicit error; document error type and message in docstrings or specs/009-sex-transit-response/plan.md
- [ ] T005 [P] Register Wdyn profile "v1" mapping to W32_V1 in hnh/sex/transit_modulator.py (or hnh/sex/profiles.py); unknown profile name must raise (fail-fast)
- [ ] T006 Implement SexTransitModulator: compute M[i] = clamp(1 + beta*E*Wdyn[i], 1-mcap, 1+mcap) and optional bounded_delta_eff given bounded_delta in hnh/sex/transit_modulator.py; deterministic, no I/O

---

## Phase 3: User Story 1 — Sex affects d_* over the life span (Priority: P1) — MVP

**Goal**: With sex_transit_mode="scale_delta", transit-driven deltas (d_*) at **every step of life** differ between male and female for the same natal/date range — identity expression along the life trajectory becomes sex-dependent. Mode=off preserves baseline; determinism preserved.

**Independent Test**: Run Agent.step() for same natal and date range with male vs female: mode=off → same d_*; scale_delta → at least one d_* differs (unless transit deltas zero). Same inputs → same outputs (determinism).

### Implementation for User Story 1

- [ ] T007 [US1] In Agent.step(), resolve 009 config (Agent over ReplayConfig); when sex_transit_mode="scale_delta" and E non-zero, compute M and bounded_delta_eff, build TransitState with bounded_delta=bounded_delta_eff, pass to behavior.apply_transits() — so transit response at every step (and thus identity expression over the life span) depends on sex; when off or E=0 pass transit_state unchanged in hnh/agent.py
- [ ] T008 [US1] Integration test: sex_transit_mode="off" → male and female d_* identical; scale_delta with non-zero transit deltas → at least one axis d_* differs between male and female (transit-driven deltas over life differ by sex) in tests/integration/test_009_sex_transit_response.py
- [ ] T009 [US1] Integration test: determinism — same natal/date/config/identity → same step() outputs with scale_delta in tests/integration/test_009_sex_transit_response.py

**Checkpoint**: US1 complete — scale_delta makes transit-driven d_* (and thus identity expression over the life span) depend on sex; mode=off and determinism verified

---

## Phase 4: User Story 2 — Bounded & symmetric modulation (Priority: P1)

**Goal**: Multipliers M[i] in [1-mcap, 1+mcap]; M(male) ≈ 2 - M(female) for opposite E; invalid config → fail-fast.

**Independent Test**: Unit tests for modulator bounds and symmetry; config validation tests for invalid mode and unknown profile.

### Implementation for User Story 2

- [ ] T010 [P] [US2] Unit tests for SexTransitModulator: M[i] in [1-mcap, 1+mcap], symmetry M(male) ≈ 2 - M(female) for opposite E, E=0 → M[i]=1 in tests/unit/test_009_transit_modulator.py
- [ ] T011 [US2] Unit test: invalid sex_transit_mode and unknown sex_transit_Wdyn_profile raise documented errors (fail-fast) in tests/unit/test_009_config_validation.py

**Checkpoint**: US2 complete — bounds and symmetry and validation verified

---

## Phase 5: User Story 3 — Observability (Priority: P2)

**Goal**: When 008 debug/audit mode is on, step output includes 009 fields (sex_transit_mode, beta, mcap, Wdyn_profile, multiplier_stats); no separate 009 debug flag.

**Independent Test**: With 008 debug enabled and 009 scale_delta active, step result includes 009 debug fields; with debug disabled, output minimal.

### Implementation for User Story 3

- [ ] T012 [US3] When 008 debug/audit mode is enabled and 009 is active, extend step result (or debug payload) with sex_transit_mode, beta, mcap, Wdyn_profile, multiplier_stats (min_M, max_M, mean_abs(M-1)); optionally max_abs(transit_delta), max_abs(transit_delta_eff) in hnh/agent.py
- [ ] T013 [US3] Test: with 008 debug enabled and sex_transit_mode=scale_delta, step output includes 009 debug fields in tests/unit/test_009_agent_debug.py or tests/integration/test_009_sex_transit_response.py

**Checkpoint**: US3 complete — observability via 008 debug only

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Calibration (SC-004), documentation, constitution compliance

- [ ] T014 Calibration script: deterministic synthetic population (fixed seed, N≥10k, 50/50 sex), fixed date range; run male/female per natal with scale_delta (transit response over life); compute per-axis mean diff, p95, and overlap (Cohen's d / overlap coefficient per 008); document thresholds in script or config; fail if SC-004 violated in scripts/009/calibration_sex_transit.py
- [ ] T015 Document calibration thresholds and CI invocation (when to run script, script path) in specs/009-sex-transit-response/plan.md or scripts/009/README.md
- [ ] T016 [P] Integration test for calibration: run calibration script on fixed seed and assert SC-004 thresholds (or allow configurable thresholds) in tests/integration/test_009_calibration.py
- [ ] T017 Constitution compliance: confirm determinism (no RNG in 009 path), Identity/Core separation (009 modulates only transit path at each step — identity expression over life span is sex-dependent, Core at birth unchanged), logging (009 debug only when 008 debug on); note in specs/009-sex-transit-response/plan.md or checklist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 — MVP
- **Phase 4 (US2)**: Depends on Phase 2 (modulator from T006); can run in parallel with Phase 3 after T006
- **Phase 5 (US3)**: Depends on Phase 3 (Agent.step() integration) for debug extension
- **Phase 6 (Polish)**: Depends on Phase 3 (calibration script uses scale_delta)

### User Story Dependencies

- **US1 (P1)**: After Foundational only — no dependency on US2/US3
- **US2 (P1)**: After Foundational (T006 modulator) — unit tests only; independent of US1 integration
- **US3 (P2)**: After US1 (T007) — debug output extends step result built in US1

### Parallel Opportunities

- T005 and T006 can run after T004 (validation contract known); T005 and T006 are independent of each other if Wdyn registry is in same file as modulator
- T010, T011 (US2 tests) can run in parallel after T006
- T014 (script) and T016 (calibration test) can run after T007/T008

---

## Parallel Example: User Story 1

```bash
# After T007:
# Run integration tests together:
pytest tests/integration/test_009_sex_transit_response.py -v
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (T001)
2. Complete Phase 2 (T002–T006)
3. Complete Phase 3 (T007–T009)
4. **STOP and VALIDATE**: Run integration tests; verify mode=off and scale_delta and determinism
5. Optionally add US2 tests (T010–T011) and US3 (T012–T013), then Polish (T014–T017)

### Incremental Delivery

1. Phase 1 + 2 → foundation (config, modulator, validation)
2. Phase 3 (US1) → scale_delta in step(), tests → MVP
3. Phase 4 (US2) → bounds/symmetry and fail-fast tests
4. Phase 5 (US3) → debug output
5. Phase 6 → calibration script and docs

### Task Count Summary

| Phase        | Tasks   | Story |
|-------------|---------|-------|
| Phase 1     | 1       | —     |
| Phase 2     | 5       | —     |
| Phase 3 US1 | 3       | US1   |
| Phase 4 US2 | 2       | US2   |
| Phase 5 US3 | 2       | US3   |
| Phase 6     | 4       | —     |
| **Total**   | **17**  |       |

**Format validation**: All tasks use checklist format `- [ ] Tnnn [P?] [US?] Description with file path`.
