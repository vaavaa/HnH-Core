# Feature Specification: HnH Personality Model v0.2 — 8 Axes × 4 Sub-Parameters

**Feature Branch**: `002-hierarchical-personality-model`  
**Created**: 2025-02-17  
**Status**: Draft  
**Implementation plan**: [plan.md](plan.md) · **Tasks**: [tasks.md](tasks.md)  
**Input**: Upgrade from flat 7-parameter vector to hierarchical 8 axes × 4 sub-parameters (32 params) with natal-derived sensitivity and daily modulation. Source: new_spec.md (updated).

---

## Clarifications

### Session 2025-02-17

- Q: При отсутствии натальной карты откуда берутся base[32] и sensitivity[32]? → A: Только явный ввод: при отсутствии натала вызывающий код обязан передать base[32] и sensitivity[32]; в спеке не определяем дефолтные значения.
- Q: configuration_hash строится от всего файла конфигурации или только от replay-relevant полей? → A: Хеш только от replay-relevant полей (delta limits, shock, orb/weights и т.д.); перечень полей фиксируется в плане/контракте.
- Q: effective_max_delta_summary в логе — что именно (одно число, 8 по осям, 32 по параметрам)? → A: 8 значений (по одному на ось — агрегат effective_max_delta по 4 параметрам оси).
- Q: При наличии в конфиге только global max_delta — откуда берутся parameter/axis уровни? → A: По умолчанию все уровни равны global: если задан только global_max_delta, то parameter = axis = global до явного переопределения в конфиге.
- Q: Жёсткий верхний предел shock_multiplier — откуда задаётся? → A: В спеке зафиксировать максимум (например, shock_multiplier ≤ 2.0); в конфиге можно задать только меньше или равное этому значению.

---

## 1. Objective

Upgrade the HnH personality engine to a hierarchical **8 axes × 4 sub-parameters = 32 parameters** model.

Each parameter MUST include:

- **Base Value** (0.0–1.0) derived from natal chart (Identity Core)
- **Modulation Sensitivity** (0.0–1.0) derived from natal chart
- **Daily Modulation** derived from real transits (bounded, then scaled by sensitivity)

Agent MUST NOT expose astrology knowledge. Astrology is internal physics; psychology is the interface.

---

## 2. Scope

### In Scope
- 8-axis hierarchical schema (32 parameters)
- Axis aggregation rules (deterministic mean)
- Per-parameter Modulation Sensitivity (natal-derived)
- Configurable delta boundaries (parameter > axis > global hierarchy)
- Deterministic daily modulation from transits; shock events (deterministic, logged, replayable)
- Relational Memory integration (memory_delta with default bound)
- Deterministic replay (including configuration_hash; floating tolerance 1e-9)
- Structured logging (orjson); configuration versioned and in replay signature
- 99%+ test coverage for core modules
- Performance: orjson mandatory; vectorized operations preferred; config (YAML/TOML)

### Out of Scope
- UI / web app
- Full teacher curriculum logic
- Multi-agent orchestration
- Cloud persistence (local files acceptable for tests)
- Psychological narrative beyond structured strengths/weaknesses

---

## 3. User Scenarios & Testing *(mandatory)*

### User Story 1 — Hierarchical 8×4 output (Priority: P1)

As a developer or consumer, I need the engine to output a **hierarchical 8×4 model** (8 axes, 32 sub-parameters) with base, sensitivity, and final values so that downstream systems use axis-level and parameter-level values.

**Independent Test**: Create Identity with natal; request state for a date; assert output contains `params_final` (32), `axis_final` (8), all in [0, 1].

**Acceptance Scenarios**:
1. **Given** Identity Core with natal-derived base and sensitivity, **When** Dynamic State is computed for a date, **Then** output includes `params_final`, `axis_final`; optional debug: `params_base`, `sensitivities`.
2. **Given** same Identity and date, **When** state is computed twice, **Then** outputs are identical (determinism).

---

### User Story 2 — Natal-derived sensitivity (Priority: P1)

As a developer, I need **Modulation Sensitivity** derived from the natal chart (not hardcoded), with ~60% low / ~40% high sensitivity as a statistical validation target; engine MUST expose sensitivity histogram in debug mode.

**Independent Test**: Run sensitivity computation for fixture natal charts; assert scores in [0, 1]; assert distribution is not hardcoded.

**Acceptance Scenarios**:
1. **Given** a natal chart, **When** sensitivity is computed, **Then** each of 32 parameters has sensitivity in [0, 1], stored in Identity Core, immutable.
2. **Given** debug mode, **When** requested, **Then** sensitivity distribution statistics (e.g. histogram) are exposed.

---

### User Story 3 — Configurable delta boundaries and replay (Priority: P1)

As a developer or tester, I need **delta boundaries** to be configurable with hierarchy (parameter > axis > global), versioned and included in replay signature, and **replay** to reproduce identical `params_final` and `axis_final` for identical identity, time, config, and memory snapshot; floating comparison tolerance 1e-9.

**Independent Test**: Run engine N times with same inputs; assert identical output hashes. Replay from log; assert same 32+8 values within 1e-9.

**Acceptance Scenarios**:
1. **Given** identity, injected time, transit config, and optional memory snapshot, **When** state is computed, **Then** raw transit influence is bounded by max_delta (parameter/axis/global resolution), then scaled by sensitivity; formula holds.
2. **Given** logged state and inputs, **When** replay is run, **Then** params_final and axis_final match within absolute tolerance 1e-9; configuration_hash part of replay signature.

---

### User Story 4 — Structured logging (orjson, contract) (Priority: P1)

As a developer or operator, I need state transitions logged with **orjson**, required fields including identity_hash, configuration_hash, injected_time_utc, transit_signature, shock_flag, effective_max_delta_summary, axis_final, params_final, memory_signature; optional debug: params_base, sensitivities, raw_delta, bounded_delta.

**Independent Test**: Run one step; read log; assert required fields present; assert orjson used in core path; no Python `json` in core path.

**Acceptance Scenarios**:
1. **Given** a state transition, **When** logging runs, **Then** one record is written with all required fields.
2. **Given** core logging path, **Then** orjson is used for serialization.

---

### Edge Cases
- Base + deltas outside [0, 1] → clamp01.
- Natal missing → engine MUST support identity without natal: base[32] and sensitivity[32] MUST be supplied explicitly by the caller; the spec does not define default values.
- Transit computation failure → fail deterministically (no silent random fallback).
- Shock: only affects delta bounds (effective_max_delta); MUST NOT alter base or sensitivity; MUST be logged and replayable.

---

## 4. Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Engine MUST output hierarchical 8×4 personality model (32 parameters, 8 axes); each parameter in [0.0, 1.0].
- **FR-002**: Each parameter MUST have Base Value and Modulation Sensitivity (both in [0, 1]) in Identity Core. When natal is present: sensitivity MUST be derived from natal (modality, aspect tension, Saturn/Uranus, prominence) and normalized to [0,1]. When natal is missing: both base and sensitivity MUST be supplied explicitly by the caller; no default values are defined in the spec. Stored values are immutable.
- **FR-003**: Core formula: `final[p] = clamp01(base[p] + (bounded_delta[p] × sensitivity[p]) + memory_delta[p])`. `max_delta` applies to raw transit influence BEFORE sensitivity scaling.
- **FR-004**: Transit delta MUST be bounded. Hierarchy: parameter-level limit > axis-level limit > global limit. When only global_max_delta is configured, parameter-level and axis-level default to that global value until explicitly overridden in config. Limits MUST be versioned, immutable at runtime, included in replay signature, and logged.
- **FR-005**: Raw delta: `raw_delta[p] = Σ(aspect_weight × mapping_weight × intensity_factor)`. Bounded: `bounded_delta[p] = clamp(raw_delta[p], -max_delta[p], +max_delta[p])`. Transit effect: `transit_effect[p] = bounded_delta[p] × sensitivity[p]`. Time MUST be injected; no system clock.
- **FR-006**: Shock events: when transit intensity > configured threshold (or configured major events), `effective_max_delta[p] = max_delta[p] × shock_multiplier`. shock_multiplier MUST be versioned and have a hard upper bound fixed in the spec (e.g. shock_multiplier ≤ 2.0); config MAY set a lower value only. Shock MUST NOT alter base or sensitivity; shock MUST be logged and replayable.
- **FR-007**: Relational Memory provides deterministic `memory_delta[p]` (user-scoped). Default: `|memory_delta[p]| ≤ 0.5 × global_max_delta`. Memory MUST NOT mutate base or sensitivity.
- **FR-008**: Axis aggregation: axis_base = mean(base sub-parameters), axis_final = mean(final sub-parameters); MUST be deterministic.
- **FR-009**: Replay MUST reproduce identical params_final and axis_final given identical identity, time, transit config, relational memory snapshot; absolute floating tolerance 1e-9; configuration_hash in replay signature.
- **FR-010**: Logging MUST use orjson; no Python `json` in core path. Required fields: identity_hash, configuration_hash, injected_time_utc, transit_signature, shock_flag, effective_max_delta_summary (8 values, one per axis — aggregate of effective_max_delta for the 4 sub-parameters of that axis), axis_final (8), params_final (32), memory_signature. Optional debug: params_base, sensitivities, raw_delta, bounded_delta.
- **FR-011**: Configuration (delta limits, shock threshold, etc.) MUST be in YAML or TOML. configuration_hash MUST be computed from replay-relevant fields only (e.g. delta limits, shock threshold, shock_multiplier cap, orb/weights); the exact set of fields MUST be defined in the plan or logging contract. configuration_hash MUST be included in replay signature and in the log.
- **FR-012**: Agent interface MUST NOT expose astrology; only strengths/weaknesses and measurable parameters.
- **FR-013**: Identity Core immutable; Dynamic State MUST NOT mutate Identity; Relational Memory user-scoped; Constitution invariants preserved.

### Key Entities
- **Axis**: Top-level dimension (8); axis_base, axis_final = mean of 4 sub-parameters.
- **Sub-Parameter**: 32 total; base, sensitivity, raw_delta, bounded_delta, transit_effect, memory_delta, final.
- **Identity Core (v0.2)**: base[32], sensitivity[32] (natal-derived), immutable.
- **Dynamic State (v0.2)**: bounded_delta, transit_effect, memory_delta, params_final, axis_final, shock_flag, effective_max_delta_summary, transit_signature, configuration_hash.

---

## 5. Success Criteria *(mandatory)*

- **SC-001**: 32-parameter hierarchical model operational for every state request.
- **SC-002**: Sensitivity stored and immutable; derived from natal; distribution exposable in debug.
- **SC-003**: Delta boundaries configurable (parameter/axis/global), versioned, and replayable.
- **SC-004**: Shock deterministic and logged; does not alter base or sensitivity.
- **SC-005**: orjson used in logging; required fields present; 99%+ coverage for core.
- **SC-006**: Deterministic replay validated (tolerance 1e-9); configuration_hash in signature.
- **SC-007**: No astrology exposed to agent interface.

---

## 6. Core Mathematical Model

For each parameter `p`:

`final[p] = clamp01(base[p] + (bounded_delta[p] × sensitivity[p]) + memory_delta[p])`

Where:

- `base[p]` — immutable (Identity Core)
- `sensitivity[p]` — immutable (Identity Core)
- `bounded_delta[p]` — daily transit delta after applying max_delta clamp (before sensitivity scaling)
- `memory_delta[p]` — deterministic relational adjustment
- `clamp01(x)` — clamp to [0, 1]

Important: `max_delta` applies to raw transit influence BEFORE sensitivity scaling.

---

## 7. Personality Schema: 8 Axes × 4 Parameters

| Axis | Sub-parameters |
|------|----------------|
| **1 — Emotional Tone** | warmth, empathy, patience, emotional_intensity |
| **2 — Stability & Regulation** | stability, reactivity, resilience, stress_response |
| **3 — Cognitive Style** | analytical_depth, abstraction_level, detail_orientation, big_picture_focus |
| **4 — Structure & Discipline** | structure_preference, consistency, rule_adherence, planning_bias |
| **5 — Communication Style** | verbosity, directness, questioning_frequency, explanation_bias |
| **6 — Teaching Style** | correction_intensity, challenge_level, encouragement_level, pacing |
| **7 — Power & Boundaries** | authority_presence, dominance, tolerance_for_errors, conflict_tolerance |
| **8 — Motivation & Drive** | ambition, curiosity, initiative, persistence |

All parameters: float ∈ [0, 1].

---

## 8. Axis Aggregation

- axis_base = mean(base sub-parameters)
- axis_final = mean(final sub-parameters)
- Aggregation MUST be deterministic.

---

## 9. Sensitivity Model (Natal-Derived)

Sensitivity MUST be computed from natal chart factors:

- sign modality (fixed/cardinal/mutable)
- aspect tension score
- Saturn stabilization influence
- Uranus disruption influence
- planetary prominence

Sensitivity MUST: be normalized to [0,1]; be stored in Identity Core; be immutable; expose distribution statistics (e.g. histogram) in debug mode.

**Distribution validation**: Engine MUST provide sensitivity histogram in debug mode. Target: ~60% low sensitivity, ~40% high (statistical validation, not hard constraint).

---

## 10. Transit Modulation

**Inputs**: natal chart, injected UTC time, transit configuration, relational memory snapshot. No system clock.

**Delta boundaries (configurable)**:
- Hierarchy: parameter-level > axis-level > global. Resolution: parameter > axis > global.
- When only global_max_delta is in config, parameter and axis levels default to global until overridden.
- Limits MUST be versioned, immutable at runtime, included in replay signature, and logged.

**Delta computation**:
- Raw: `raw_delta[p] = Σ(aspect_weight × mapping_weight × intensity_factor)`
- Bounded: `bounded_delta[p] = clamp(raw_delta[p], -max_delta[p], +max_delta[p])`
- Transit effect: `transit_effect[p] = bounded_delta[p] × sensitivity[p]`

---

## 11. Shock Events

Shock events are deterministic amplifications of max_delta.

- Trigger: transit intensity > configured threshold, or configured major planetary events.
- Effect: `effective_max_delta[p] = max_delta[p] × shock_multiplier`
- Rules: shock_multiplier is versioned; hard upper bound is fixed in the spec (e.g. shock_multiplier ≤ 2.0 — config may set only values ≤ this bound). Shock MUST NOT alter base or sensitivity; shock only affects delta bounds; shock MUST be logged and replayable.

---

## 12. Relational Memory

Memory provides deterministic `memory_delta[p]`. Default rule: `|memory_delta[p]| ≤ 0.5 × global_max_delta`. Memory MUST NOT mutate base or sensitivity.

---

## 13. Logging Contract

- Serialization MUST use **orjson** (no Python `json` in core path).
- Per state transition: identity_hash, configuration_hash, injected_time_utc, transit_signature, shock_flag, effective_max_delta_summary (8 values, one per axis), axis_final (8), params_final (32), memory_signature. configuration_hash is derived from replay-relevant config fields only (see FR-011; exact set in plan/contract).
- Optional debug: params_base, sensitivities, raw_delta, bounded_delta.

---

## 14. Deterministic Replay

Replay MUST reproduce identical params_final and axis_final given identical: identity core, time input, transit config, relational memory snapshot. **Absolute floating tolerance: 1e-9.** Configuration hash MUST be part of replay signature.

---

## 15. Performance Requirements

- orjson for structured logging; no Python `json` in core path.
- Numeric operations: avoid Python loops where possible; vectorized operations preferred if determinism preserved.
- Configuration: YAML or TOML; configuration hash included in replay signature.

---

## 16. Test Requirements

- **Coverage**: 99%+ for core modules.
- **Required tests**: delta limit enforcement; hierarchy resolution correctness; shock upper bound enforcement; replay determinism; sensitivity normalization; memory delta bounds; floating tolerance stability (1e-9).
- **Regression fixtures**: predefined natal charts and dates.
- **Replay**: multiple executions MUST produce identical output hashes.

---

## 17. Acceptance Criteria (Definition of Done)

Feature complete when:

- 32-parameter hierarchical model operational
- sensitivity stored and immutable
- delta boundaries configurable and replayable
- shock deterministic and logged
- orjson used in logging
- 99% coverage achieved
- deterministic replay validated (tolerance 1e-9)

---

## 18. Deliverables

- Core personality schema (8 axes, 32 params)
- Sensitivity computation module (natal-derived)
- Transit modulation module (configurable bounds, hierarchy)
- State assembly module (base + bounded_delta × sensitivity + memory)
- Shock event handling (versioned multiplier, logged)
- Replay harness (configuration_hash, tolerance 1e-9)
- Structured logging (orjson)
- **CLI entry point**: subcommands and per-command help; 002 flow (params_final, axis_final); optional legacy 7-param output
- Test suite, fixtures, 99% coverage gate

---

## 19. Future Work (Not in this spec)

- LLM teacher curriculum and ladder logic
- Multi-agent ecosystem protocols
- Public “personality cards” and narrative layers
- Persistence backend (db)
- Formal RFC documents

---

## 20. Constitution Alignment *(HnH)*

- [x] **Deterministic Mode**: Injected time, replay, no system clock; identical inputs → identical outputs; config in replay signature.
- [x] **Identity/Core / Memory / Interface**: Identity immutable; Dynamic State does not mutate Core; Relational Memory user-scoped; no personality logic in prompts; astrology not exposed to agent.
- [x] **Parameterization**: Natal and transits map to measurable parameters; no symbolic-only behavior.
- [x] **Observability**: Structured logging, replay, configuration_hash, optional debug fields.
- [x] **Ethical guardrails**: Engine is simulation; no consciousness claim; no emotional dependency design.
- [x] **Non-goals**: Not a horoscope generator, chatbot wrapper, or roleplay framework; fits deterministic personality engine scope.
