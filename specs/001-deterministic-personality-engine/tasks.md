# Tasks: Deterministic Personality Engine v0.1 (HnH Core)

**Input**: Design documents from `specs/001-deterministic-personality-engine/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story (spec 001). Based on "HnH Task List — Planetary Agent MVP" with alignment to spec (7 behavioral dimensions, reject out-of-range, scope 001).

**Path convention**: Repository root = project root; package under `hnh/` per plan.md. Tests live at repo root: `tests/unit/`, `tests/integration/` (see plan.md §4).

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[USn]**: User story (US1–US4 from spec.md)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and tooling

- [ ] T001 Create project structure per plan (hnh/core/, hnh/astrology/, hnh/state/, hnh/memory/, hnh/interface/, hnh/logging/, tests/)
- [ ] T002 Initialize Python 3.12+ project with pyproject.toml (hnh/, dependencies)
- [ ] T003 [P] Add dependencies to pyproject.toml: pydantic, pytest, pytest-cov, structlog; optional pyswisseph
- [ ] T004 [P] Configure Black and Ruff in pyproject.toml or config files
- [ ] T005 [P] Enable pre-commit hooks (.pre-commit-config.yaml)
- [ ] T006 [P] Enable strict type checking (mypy) in pyproject.toml or mypy.ini

**Checkpoint**: Project builds; lint/format/typecheck pass

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Behavioral vector schema and validation shared by all user stories

**⚠️ CRITICAL**: No user story work until this phase is complete.

- [ ] T007 [P] Define BehavioralVector schema (exactly 7 dimensions per spec) in hnh/core/parameters.py: warmth, strictness, verbosity, correction_rate, humor_level, challenge_intensity, pacing; all float [0.0, 1.0]
- [ ] T008 Add validation in hnh/core/parameters.py: reject any value outside [0.0, 1.0] (no clamping); reject NaN/overflow
- [ ] T009 [P] Add contracts for behavioral vector in hnh/logging/contracts.py aligned with specs/001-deterministic-personality-engine/contracts/behavioral-vector.json

**Checkpoint**: Behavioral vector is validated and reusable; foundation ready for US1–US4

---

## Phase 3: User Story 1 — Identity Core and Base Behavioral Vector (P1) 🎯 MVP

**Goal**: Immutable Identity Core producing deterministic base behavioral vector; serializable, hashable; at most one Core per identity_id.

**Independent Test**: Create Identity Core with fixed inputs; get base vector; create again with same inputs → identical vector; assert serializable and hashable; duplicate identity_id → error.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test Identity Core creation and base vector in tests/unit/test_identity.py (same inputs → same vector)
- [ ] T011 [P] [US1] Unit test Identity Core immutability and duplicate identity_id rejection in tests/unit/test_identity.py
- [ ] T012 [P] [US1] Unit test natal reproducibility (if astrology used) in tests/unit/test_natal.py: same birth input → identical natal output and hash

### Implementation for User Story 1

- [ ] T013 [US1] Implement birth datetime normalization (UTC only) in hnh/core/natal.py or hnh/astrology/ephemeris.py
- [ ] T014 [US1] Implement location validation (lat/lon bounds) in hnh/core/natal.py or hnh/astrology/ephemeris.py
- [ ] T015 [US1] Compute planetary positions with pyswisseph in hnh/astrology/ephemeris.py (optional for 001)
- [ ] T016 [US1] Implement aspect detection (major aspects for v0.1) and orb config in hnh/astrology/aspects.py
- [ ] T017 [US1] Generate deterministic natal_positions structure in hnh/core/natal.py
- [ ] T018 [US1] Implement Identity Core in hnh/core/identity.py: identity_id, base_traits (BehavioralVector), optional symbolic_input; identity_hash; immutable, hashable, serializable; reject duplicate identity_id
- [ ] T019 [US1] Create identity_hash generation logic in hnh/core/identity.py (stable, deterministic)

**Checkpoint**: Identity Core created; same inputs → identical vector and hash; duplicate identity_id raises

**Minimal 001 path (no astrology)**: Identity Core can be created from `base_traits` only (no natal/symbolic_input). Skip T013–T017 and pass base_behavior_vector directly into T018/T019; all other checkpoints still apply.

---

## Phase 4: User Story 2 — Dynamic State with Seed and Time Injection (P1)

**Goal**: Dynamic State accepts injected seed and time; computes modifiers deterministically; outputs modified vector and snapshot; does not mutate Identity Core; identical inputs → identical outputs.

**Independent Test**: Run state computation twice with same Identity Core, seed, time, relational memory → identical modified vector and modifiers.

### Tests for User Story 2

- [ ] T020 [P] [US2] Unit test transit determinism in tests/unit/test_transits.py: same injected time → identical transit_signature
- [ ] T021 [P] [US2] Unit test mapping determinism in tests/unit/test_modulation.py: identical natal + transit → identical behavioral vector
- [ ] T022 [US2] Integration test Dynamic State replay in tests/integration/test_dynamic_state.py: same inputs → identical state output

### Implementation for User Story 2

- [ ] T023 [US2] Implement injected time interface (no datetime.now()) in hnh/astrology/transits.py
- [ ] T024 [US2] Compute daily planetary positions and transit→natal aspects in hnh/astrology/transits.py; generate transit_signature (stable)
- [ ] T025 [US2] Create aspect→parameter weight config and weighted aggregation in hnh/state/modulation.py
- [ ] T026 [US2] Implement base vector + modulation merge logic in hnh/state/modulation.py
- [ ] T027 [US2] Implement DynamicState in hnh/state/dynamic_state.py: identity_hash, timestamp (injected), transit_signature, relational_modifier, final_behavior_vector, active_modifiers; no Identity mutation; reject any behavioral parameter values from relational modifier outside [0, 1] (FR-006)
- [ ] T028 [US2] Implement replay in hnh/state/replay.py: inject seed, time, relational snapshot; build replay harness; no system clock in core
- [ ] T029 [US2] Verify identical output across replay runs (tests/integration or tests/unit)

**Checkpoint**: Dynamic State and replay produce identical state for same inputs; no core use of system clock

---

## Phase 5: User Story 3 — State Logging and Replay Mode (P1)

**Goal**: Every state transition logged (seed, injected_time, identity_hash, active_modifiers, final_behavioral_vector); structured, diffable, one record per line (e.g. JSON Lines); replay reproduces identical outputs.

**Independent Test**: Run one step; capture log; run replay with same seed/time; assert log and outputs match; replay does not use system clock.

### Tests for User Story 3

- [ ] T030 [P] [US3] Log replay validation test in tests/integration/test_state_logger.py: log format matches contract; replay from log produces identical state

### Implementation for User Story 3

- [ ] T031 [US3] Implement structured state logger in hnh/logging/state_logger.py per specs/001-deterministic-personality-engine/contracts/state-log-spec.md
- [ ] T032 [US3] Log required fields: identity_hash, injected_time, seed, active_modifiers, final_behavioral_vector; optional: transit_signature, relational_snapshot_hash
- [ ] T033 [US3] Ensure one record per state transition; text-based, one line per record (JSON Lines); diffable

**Checkpoint**: All state transitions logged; replay validation test passes

---

## Phase 6: User Story 4 — Minimal Relational Memory (P2)

**Goal**: In-memory, user-scoped Relational Memory; ordered list of events (sequence, type, payload); deterministic update rules; no Identity Core mutation; optional input to Dynamic State via mapping rules.

**Independent Test**: Create user-scoped memory; apply deterministic update rules; feed snapshot into Dynamic State; assert Identity unchanged and same memory state → same behavior.

### Tests for User Story 4

- [ ] T034 [P] [US4] Unit test relational memory update rules in tests/unit/test_relational.py: same history → same modifiers
- [ ] T035 [US4] Integration test replay with identical relational history in tests/integration/test_relational.py

### Implementation for User Story 4

- [ ] T036 [US4] Implement user-scoped memory in hnh/memory/relational.py: user_id, ordered events (sequence, type, payload)
- [ ] T037 [US4] Track interaction_count, error_rate, responsiveness (or equivalent) as derived/payload in hnh/memory/relational.py
- [ ] T038 [US4] Implement deterministic update rules in hnh/memory/update_rules.py; no mutation of Identity Core
- [ ] T039 [US4] Implement snapshot export (serializable) in hnh/memory/relational.py for replay and Dynamic State input

**Checkpoint**: Relational Memory v0.1 works; same history → same modifiers; snapshot export and replay test pass

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: CLI, coverage, constitution compliance

- [ ] T040 [P] Build CLI in hnh/cli.py to simulate agent for specific date; print behavioral vector and relational modifiers; support replay mode flag
- [ ] T041 Run quickstart.md validation scenarios (specs/001-deterministic-personality-engine/quickstart.md)
- [ ] T042 [P] Enforce immutability of Identity Core (review and tests in hnh/core/identity.py)
- [ ] T043 [P] Enforce no datetime.now() in core modules (grep/review and tests)
- [ ] T044 Enforce deterministic test suite (all tests reproducible; seed/time injected where needed)
- [ ] T045 Achieve 90%+ test coverage for core modules (pytest-cov)
- [ ] T046 Review Constitution compliance checklist (spec §6 Compliance Checklist)

### Constitution Compliance (HnH)

- [ ] **Deterministic Mode compliance**: Seed/time injection and replay verified; no unseeded randomness in core
- [ ] **Identity/Core separation**: Identity Core immutable; Dynamic State / Relational Memory boundaries respected
- [ ] **Logging validation**: State transitions and observability implemented and verifiable

---

## Future (Out of Scope for 001)

*Implemented as optional extension; not required for spec 001.*

### Phase 5 (Future) — LLM Behavioral Adapter ✅

- **Implemented**: `hnh/interface/llm_adapter.py` — `LLMAdapter` protocol, `MockLLMAdapter`, `LessonContext`; behavioral vector injection; mock test harness in `tests/unit/test_llm_adapter.py`. Teacher scenario: lesson context + relational summary + vector → style payload; observable style shift (different vector → different payload).
- Adapter layer: behavioral vector injection; personality logic separate from prompt; LLM adapter optional; mock LLM test harness.
- Teacher scenario: lesson context structure; inject relational summary and behavioral vector; validate observable style shift.

### Phase 6 (Future) — Teacher MVP Deployment ✅

- **Implemented**: `hnh/interface/teacher.py` — `PlanetaryTeacher`, `create_planetary_teacher(label, birth, lat, lon, base_traits?)`, `state_for_date()`, `pilot_run(teacher, start, end, seed, step_days)`. CLI simulation (Phase 7) already provides date/vector/modifiers/replay.
- CLI simulation for specific date; print vector and modifiers; replay flag.
- Instantiate first Planetary Teacher; fix birth date; daily modulation; internal logs; 2–4 week pilot.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start first
- **Phase 2 (Foundational)**: Depends on Setup — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Foundational — Identity Core + natal/params
- **Phase 4 (US2)**: Depends on Foundational and US1 (Identity) — Dynamic State, transit, replay
- **Phase 5 (US3)**: Depends on US2 — Logging and replay validation
- **Phase 6 (US4)**: Depends on Foundational — Relational Memory; can parallel with US2/US3 after Foundational
- **Phase 7 (Polish)**: Depends on US1–US4 complete

### Parallel Opportunities

- T003, T004, T005, T006 (Setup) can run in parallel
- T007, T009 (Foundational) can run in parallel
- T010, T011, T012 (US1 tests) can run in parallel
- T020, T021 (US2 tests) can run in parallel
- T030 (US3 test), T034 (US4 test) — parallel where no shared state
- T040, T042, T043 (Polish) can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational)
2. Complete Phase 3 (US1 — Identity Core)
3. Stop and validate: Identity Core tests and independent test criteria pass
4. Then add US2 → US3 → US4 → Polish

### Done Definition (001)

- Identity is immutable; one Core per identity_id
- Deterministic replay works; identical inputs → identical state
- Logs capture full state transitions per contract
- Relational Memory v0.1 works with deterministic rules
- No LLM dependency in core
- Tests pass; 90%+ coverage on core; Constitution compliance checklist passed
