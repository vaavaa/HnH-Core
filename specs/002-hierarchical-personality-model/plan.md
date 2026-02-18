# /speckit.plan
## HnH Personality Model v0.2 Implementation Plan
### Hierarchical 8×4 Model with Sensitivity & Deterministic Replay

**Spec**: [spec.md](spec.md) · **Tasks**: [tasks.md](tasks.md)

---

# 1. Objective

Implement Personality Model v0.2:

- 8 axes × 4 sub-parameters (32 total)
- Natal-derived base values
- Natal-derived sensitivity
- Transit-based modulation
- Configurable delta hierarchy
- Deterministic replay
- Structured logging (orjson)
- 99%+ test coverage (core modules)

This plan is execution-focused.

---

# 2. Architecture Milestones

---

## Milestone 1 — Core Schema Layer

### Deliverables

- `PersonalityAxis` model
- `PersonalityParameter` model
- `IdentityCore` model
- Base value storage (32)
- Sensitivity storage (32)
- Identity hash computation

### Requirements

- Immutable after construction
- Deterministic serialization
- Canonical ordering of parameters
- Configuration-independent

### Tests

- Immutability tests
- Sensitivity normalization tests
- Identity hash determinism tests

Coverage target: 99%

---

## Milestone 2 — Sensitivity Engine

### Deliverables

- Natal → Sensitivity computation module
- Modality weighting logic
- Saturn/Uranus influence computation
- Normalization to [0,1]
- Debug histogram export

### Requirements

- No randomness
- Pure function from natal → sensitivity vector
- Statistical distribution check tool (debug only)

### Tests

- Known natal fixtures
- Sensitivity range validation
- Distribution sanity tests

---

## Milestone 3 — Transit Engine

### Deliverables

- pyswisseph integration
- Natal position computation
- Transit position computation
- Aspect detection
- Raw delta computation (32 params)

### Requirements

- Injected UTC time only
- No system clock
- Pure deterministic function

### Tests

- Known date fixtures
- Aspect detection correctness
- Deterministic repeated runs

---

## Milestone 4 — Delta Boundary System

### Deliverables

- Config loader (YAML/TOML)
- ReplayConfig extraction (subset only)
- Hierarchical resolution:
  parameter > axis > global
- Shock system
- Hard cap enforcement:
  ENGINE_SHOCK_MULTIPLIER_HARD_CAP = 2.0

### Requirements

- Minimal config (global only) must work
- Inheritance rules strictly enforced
- Fail-fast if shock_multiplier > hard cap
- Configuration hash (SHA256 canonicalized)

### Tests

- Hierarchy resolution tests
- Minimal config behavior test
- Override behavior test
- Hard cap failure test
- configuration_hash determinism

---

## Milestone 5 — State Assembly Engine

### Deliverables

- Base + transit + memory merge
- clamp01 enforcement
- Axis aggregation
- Replay signature generation:
  identity_hash +
  configuration_hash +
  transit_signature +
  memory_signature

### Requirements

- Absolute float tolerance 1e-9
- Deterministic ordering
- No environment dependencies

### Tests

- Replay identical outputs
- Floating tolerance tests
- Parameter bounds tests

---

## Milestone 6 — Relational Memory Layer

### Deliverables

- Memory state model
- Deterministic update rules
- Memory delta bounds:
  |memory_delta| ≤ 0.5 × global_max_delta

### Requirements

- No mutation of IdentityCore
- Snapshot hash included in replay
- Deterministic updates only

### Tests

- Memory delta bounds
- Replay with memory changes
- Identity immutability tests

---

## Milestone 7 — Logging Layer

### Deliverables

- orjson-based serializer
- effective_max_delta_summary (production mode)
- effective_max_delta_hash
- Debug-mode full parameter deltas

### Requirements

Production log must include:
- identity_hash
- configuration_hash
- injected_time
- shock_flag
- max_effective_delta
- effective_max_delta_hash

Debug log additionally:
- 32 deltas
- sensitivities
- base values

### Tests

- orjson enforced
- Log schema validation
- Hash consistency tests

---

## Milestone 8 — Performance Validation

### Deliverables

- Benchmark: daily state computation
- Benchmark: serialization speed
- Baseline performance report

### Requirements

- No Python `json` in core path
- Numeric loops minimized
- Evaluate vectorization if deterministic

---

# 3. Repository Structure (Target)

hnh/
│
├── identity/
│ ├── schema.py
│ ├── sensitivity.py
│
├── astrology/
│ ├── natal.py
│ ├── transits.py
│ ├── aspects.py
│
├── modulation/
│ ├── delta.py
│ ├── boundaries.py
│ ├── shock.py
│
├── memory/
│ ├── relational.py
│
├── state/
│ ├── assembler.py
│ ├── replay.py
│
├── config/
│ ├── loader.py
│ ├── replay_config.py
│
├── logging/
│ ├── logger.py
│
├── tests/
│
└── cli.py


---

# 4. Execution Order

1. Core schema
2. Sensitivity engine
3. Transit engine
4. Boundary + config system
5. State assembler
6. Replay
7. Memory
8. Logging
9. Performance pass
10. Coverage gate

---

# 5. Definition of Done

The feature is complete when:

- 32 hierarchical parameters implemented
- Sensitivity computed from natal and immutable
- Delta boundaries deterministic and hierarchical
- Shock capped at 2.0 and enforced
- configuration_hash replay-safe
- Replay identical under same inputs
- Logs structured via orjson
- 99%+ coverage for core modules
- No system clock usage
- No hidden randomness

---

End of Plan.
