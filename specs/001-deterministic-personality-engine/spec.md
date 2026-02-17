# Feature Specification: Deterministic Personality Engine v0.1 (HnH Core)

**Feature Branch**: `001-deterministic-personality-engine`  
**Created**: 2025-02-17  
**Status**: Draft  
**Input**: First deterministic reference implementation of the HnH personality engine. Identity Core + Dynamic State, Deterministic Simulation Mode, no LLM, state logging, replay with fixed seed and injected time.

---

## 1. Scope

### In Scope

- Identity Core definition structure  
- Deterministic Dynamic State computation  
- Seed injection  
- Time injection  
- State transition logging  
- Replay mode  
- Structured behavioral output parameters  

### Out of Scope (v0.1)

- LLM integration  
- UI  
- API server  
- External astrology API  
- Persistent database  

---

## Clarifications

### Session 2025-02-17

- Q: When the same identity_id is used again with different base_traits (or other fields), should the engine reject creation, overwrite, or treat as idempotent? → A: B — One Identity Core per identity_id; attempting to create a Core with an identity_id that already exists (regardless of other fields) MUST yield an error (already exists).
- Q: In v0.1, is the set of behavioral dimensions fixed (exactly the seven listed) or may the implementation add more? → A: A — Fixed set of exactly seven dimensions; implementation must not add others in v0.1.
- Q: Should the spec fix a minimal log format for replay and tests, or leave format entirely to the plan? → A: A — Spec fixes minimal contract: one record per state transition; required fields: seed, injected_time, identity_hash, active_modifiers, final_behavioral_vector; text-based, one record per line (e.g. JSON Lines). Details in plan.
- Q: For values outside [0, 1], reject at Core creation / State input, or clamp? → A: A — Reject: values outside [0, 1] at Identity Core creation or at Dynamic State input are an error (reject); do not allow into the system.
- Q: User scope for Relational Memory: single ID only and schema in plan, or fix minimal schema in spec? → A: B — User scope = single identifier (e.g. user_id, string); one memory per user; minimal schema fixed in spec (e.g. key-value or list of events with fields).

---

## 2. User Scenarios & Testing *(mandatory)*

### User Story 1 - Identity Core and Base Behavioral Vector (Priority: P1)

As a developer or tester, I need the engine to define an immutable Identity Core that produces a deterministic base behavioral vector (warmth, strictness, verbosity, correction_rate, humor_level, challenge_intensity, pacing), so that personality is defined once and never mutated at runtime.

**Why this priority**: Foundation for all state computation; Constitution requires Identity Core immutability.

**Independent Test**: Create an Identity Core with fixed inputs; obtain base vector; create again with same inputs; assert identical vector and that Core is serializable and hashable.

**Acceptance Scenarios**:

1. **Given** valid Identity Core inputs (identity_id, base_traits, optional symbolic_input), **When** Identity Core is created, **Then** it produces a base behavioral vector with all seven dimensions normalized (0.0–1.0) and is immutable, serializable, and hashable.  
2. **Given** the same Identity Core inputs, **When** a second Identity Core is created, **Then** the base behavioral vector is identical to the first.  
3. **Given** an existing Identity Core, **When** any attempt is made to mutate it after creation, **Then** the Core remains unchanged (immutability enforced).

---

### User Story 2 - Dynamic State with Seed and Time Injection (Priority: P1)

As a developer or tester, I need Dynamic State to accept an injected seed and time, compute modifiers deterministically, and output a modified behavioral vector and state snapshot without mutating Identity Core, so that simulation is fully reproducible.

**Why this priority**: Core of Deterministic Simulation Mode; required for replay and testing.

**Independent Test**: Run state computation twice with same Identity Core, seed, time, and relational memory state; assert identical modified vector and active modifiers.

**Acceptance Scenarios**:

1. **Given** Identity Core, seed, and injected time, **When** Dynamic State is computed, **Then** output includes modified behavioral vector, list of active modifiers, and internal state snapshot; Identity Core is not mutated.  
2. **Given** identical inputs (identity, seed, time, relational memory state), **When** Dynamic State is computed multiple times, **Then** outputs are identical.  
3. **Given** any use of randomness in core modules, **When** state is computed, **Then** randomness uses the injected seed only (no hidden entropy).

---

### User Story 3 - State Logging and Replay Mode (Priority: P1)

As a developer or tester, I need the engine to log every state transition (seed, injected time, identity hash, active modifiers, final behavioral vector) in a structured, diffable format and to support step-by-step replay that reproduces identical outputs without depending on system clock.

**Why this priority**: Observability and Constitution compliance; enables validation and debugging.

**Independent Test**: Run a simulation step; capture log; run replay with same seed/time; assert log and outputs match and replay does not use system clock.

**Acceptance Scenarios**:

1. **Given** a simulation step, **When** the engine runs, **Then** it logs seed, injected time, identity hash, active modifiers, and final behavioral vector in a structured, diffable format.  
2. **Given** logged state and inputs, **When** replay mode is run step-by-step, **Then** outputs are identical to the original run and replay does not depend on system clock.  
3. **Given** a deterministic test harness, **When** replay is executed, **Then** identical inputs produce identical outputs (replay correctness).

---

### User Story 4 - Minimal Relational Memory (Priority: P2)

As a developer, I need a minimal in-memory, user-scoped Relational Memory with deterministic update rules that can influence Dynamic State via defined mapping rules, without mutating Identity Core.

**Why this priority**: Completes Constitution’s four pillars; minimal version keeps v0.1 scope bounded.

**Independent Test**: Create user-scoped memory; apply deterministic update rules; feed into Dynamic State; assert Identity Core unchanged and behavior deterministic for same memory state.

**Acceptance Scenarios**:

1. **Given** a user scope, **When** Relational Memory is created and updated via defined rules, **Then** updates are deterministic and user-scoped; Identity Core is not modified.  
2. **Given** Relational Memory state, **When** Dynamic State is computed, **Then** memory MAY influence state only via documented mapping rules; no implicit behavioral mutation.

---

### Edge Cases

- What happens when seed or time is missing? Engine MUST require explicit injection (no defaults that introduce non-determinism).  
- What happens when behavioral parameters are out of range? Values outside [0, 1] MUST be rejected (error) at Identity Core creation and at Dynamic State input; no clamping. Outputs inside the engine are always in 0.0–1.0.  
- How does the system handle duplicate identity_id? At most one Identity Core per identity_id; creating a Core with an identity_id that already exists MUST fail with an error (already exists).  
- What happens when replay is given a different seed? Replay MUST produce the output that would occur for that seed; no cross-run state leakage.

---

## 3. Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Identity Core MUST be immutable after creation, serializable, and hashable.  
- **FR-002**: Identity Core MUST produce a base behavioral vector with exactly the seven dimensions: warmth, strictness, verbosity, correction_rate, humor_level, challenge_intensity, pacing; all normalized 0.0–1.0. In v0.1 the set is fixed; implementation must not add other dimensions. Any input value outside [0, 1] for these dimensions MUST be rejected (error) at creation; no clamping.  
- **FR-003**: Identity Core MUST support required fields: identity_id, base_traits (structured numeric parameters), optional symbolic_input (e.g. natal chart metadata); symbolic inputs MUST map to measurable parameters. At most one Identity Core per identity_id; creation with an existing identity_id MUST fail (already-exists error).  
- **FR-004**: Dynamic State MUST accept injected seed and injected time.  
- **FR-005**: Dynamic State MUST compute modifiers deterministically and MUST NOT mutate Identity Core.  
- **FR-006**: Dynamic State MUST output: modified behavioral vector, list of active modifiers, internal state snapshot. Any behavioral parameter values supplied as input to Dynamic State (e.g. from Relational Memory) that are outside [0, 1] MUST be rejected (error); no clamping.  
- **FR-007**: Simulation MUST be reproducible when identity, seed, time input, and relational memory state are identical; identical inputs MUST produce identical outputs.  
- **FR-008**: All randomness MUST use injected seed; no non-deterministic code in core modules.  
- **FR-009**: Relational Memory (v0.1) MUST be in-memory, user-scoped by a single identifier (e.g. user_id, string); one memory instance per user. It MUST use a minimal schema: ordered list of events; each event MUST have at least: sequence index (or step), type, and payload (key-value or opaque data). Update rules MUST be deterministic. Relational Memory MUST NOT mutate Identity Core and MAY influence Dynamic State only via documented mapping rules.  
- **FR-010**: Engine MUST log each state transition with a minimal contract: one record per transition; required fields: seed, injected_time, identity_hash, active_modifiers, final_behavioral_vector; format text-based, one record per line (e.g. JSON Lines). Logging MUST be diffable and support replay validation. Concrete field names and encoding are defined in the implementation plan.  
- **FR-011**: Engine MUST support step-by-step state replay, validation of identical outputs, and a deterministic test harness; replay MUST NOT depend on system clock.  
- **FR-012**: Engine MUST NOT depend on any LLM or external API.  
- **FR-013**: Tests MUST verify: Identity immutability, deterministic state computation, seed reproducibility, replay correctness, parameter range 0–1, no cross-layer mutation; coverage target 90%+ for core modules.

### State Transition Log (Minimal Contract)

Each state transition MUST produce exactly one log record. Required fields: `seed`, `injected_time`, `identity_hash`, `active_modifiers`, `final_behavioral_vector`. Format: text-based, one record per line (e.g. JSON Lines). Concrete field names and encoding are defined in the implementation plan. Log MUST be diffable and support replay validation.

### Key Entities

- **Identity Core**: Immutable entity after creation. Attributes: identity_id, base_traits (structured numeric parameters), optional symbolic_input. Produces base behavioral vector (seven dimensions, 0.0–1.0). Must be serializable and hashable.  
- **Dynamic State**: Computed state per step. Consumes Identity Core, seed, time, optional Relational Memory. Outputs: modified behavioral vector, active modifiers, state snapshot. Must not mutate Identity Core.  
- **Behavioral Vector**: Fixed set of exactly seven normalized (0.0–1.0) parameters in v0.1: warmth, strictness, verbosity, correction_rate, humor_level, challenge_intensity, pacing. No additional dimensions.  
- **Relational Memory (v0.1)**: In-memory, one instance per user (user scope = single identifier, e.g. user_id). Minimal schema: ordered list of events; each event has at least sequence index (step), type, and payload (key-value or opaque). Deterministic update rules; optional input to Dynamic State via documented mapping rules; MUST NOT mutate Identity Core.

### Relational Memory v0.1 (Minimal Schema)

- **User scope**: Single identifier (e.g. `user_id`, string); one memory instance per user.
- **Schema**: Ordered list of events. Each event MUST have: sequence index (step), type, payload (key-value or opaque data). Concrete field names and types are defined in the implementation plan. Updates MUST be deterministic and append-only (or otherwise defined so replay is deterministic).

---

## 4. Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Engine runs without any LLM or external API dependency.  
- **SC-002**: Same seed + time + identity + memory state produce identical behavior (verified by automated tests).  
- **SC-003**: All state transitions are logged in a structured, diffable format that supports replay validation.  
- **SC-004**: Replay mode reproduces identical outputs for the same inputs; replay does not use system clock.  
- **SC-005**: All tests pass; Identity immutability, deterministic computation, seed reproducibility, replay correctness, parameter range, and no cross-layer mutation are covered.  
- **SC-006**: Constitution compliance checklist (Identity Core immutable, Dynamic State deterministic, seed/time injection, logging, replay, no LLM, external contracts documented) passes.  
- **SC-007**: Test coverage for core modules is at least 90%.

---

## 5. Constitution Alignment *(HnH)*

- [x] **Deterministic Mode**: Spec requires seed/time injection and replay; identical inputs → identical outputs; no unseeded randomness in core.  
- [x] **Identity/Core / Memory / Interface**: Identity Core immutable; Dynamic State does not mutate Core; Relational Memory user-scoped with explicit rules; Behavioral Interface (output vector) is pure mapping; no personality logic in prompts (no LLM).  
- [x] **Parameterization**: Symbolic inputs (e.g. natal chart metadata) map to measurable parameters; base_traits and behavioral vector are numeric.  
- [x] **Observability**: Spec requires state transition logging, identity hash, modifiers, behavioral vector; replay and snapshot support.  
- [x] **Ethical guardrails**: Engine is a deterministic simulation core; no claim of consciousness; no chatbot/emotional-dependency design.  
- [x] **Non-goals**: Explicitly out of scope: horoscope generator, chatbot wrapper, prompt toolkit, roleplay framework; this is the core engine only.

---

## 6. Compliance Checklist (v0.1)

- [ ] Identity Core immutable  
- [ ] Dynamic State deterministic  
- [ ] Seed injection supported  
- [ ] Time injection supported  
- [ ] Logging implemented (structured, diffable, replay-validatable)  
- [ ] Replay mode implemented (step-by-step, no system clock)  
- [ ] No LLM dependency  
- [ ] External contracts documented (behavioral vector, state snapshot, log format)

---

## 7. Future Extensions (Not in v0.1)

- LLM adapter layer  
- Astrology computation module  
- Multi-agent orchestration  
- Progression ladder engine  
- Persistence layer  
