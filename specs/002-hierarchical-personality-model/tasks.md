# /speckit.tasks
## HnH Personality Model v0.2 — Task Breakdown

**Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

---

# Phase 1 — Core Schema

## T1.1 Define Axis & Parameter Registry
- [x] Create canonical ordered list of 8 axes
- [x] Create canonical ordered list of 32 parameters
- [x] Ensure deterministic order

Acceptance:
- Order stable across runs
- Unit test verifies index mapping

---

## T1.2 Implement PersonalityParameter Model
- [x] Fields: name, axis, base_value, sensitivity
- [x] Constraints: base_value, sensitivity ∈ [0,1]

Acceptance:
- Validation tests
- Immutability test

---

## T1.3 Implement IdentityCore
- [x] Fields: identity_id, natal_data, base_vector (32), sensitivity_vector (32), identity_hash

Acceptance:
- Hash deterministic
- Identity immutable
- Serialization deterministic

---

# Phase 2 — Sensitivity Engine

## T2.1 Implement Modality Weighting
- [x] Map fixed/cardinal/mutable → weights
- [x] Deterministic mapping

## T2.2 Implement Saturn Stabilization
- [x] Penalize sensitivity based on Saturn strength

## T2.3 Implement Uranus Disruption
- [x] Increase sensitivity based on Uranus tension

## T2.4 Normalize Sensitivity
- [x] Normalize to [0,1]
- [x] Preserve relative differences

Acceptance:
- Sensitivity vector stable across runs
- Debug histogram export works
- Range validation tests pass

---

# Phase 3 — Transit Engine

## T3.1 Integrate pyswisseph
- [x] Natal positions (existing ephemeris)
- [x] Transit positions (existing transits)
- [x] Injected UTC only

## T3.2 Implement Aspect Detection
- [x] Hard aspects (existing aspects.py)
- [x] Orb support
- [x] Weight assignment

## T3.3 Implement Raw Delta Calculation
- [x] Map aspects → parameter weights
- [x] Compute raw_delta vector (32)

Acceptance:
- Known natal + date fixtures deterministic
- Aspect detection tests
- Raw delta bounded test

---

# Phase 4 — Delta Boundaries & Config

## T4.1 Implement Config Loader
- [x] YAML/TOML support
- [x] Extract ReplayConfig subset

## T4.2 Implement configuration_hash
- [x] Canonical serialization
- [x] SHA256
- [x] Replay-relevant fields only

## T4.3 Implement Hierarchy Resolution
- [x] parameter > axis > global
- [x] Default inheritance from global

## T4.4 Implement Shock System
- [x] shock_threshold
- [x] shock_multiplier
- [x] Hard cap = 2.0
- [x] Fail-fast if exceeded

Acceptance:
- Minimal config works
- Override works
- Shock cap enforced
- configuration_hash stable

---

# Phase 5 — State Assembly

## T5.1 Compute bounded_delta
- [x] Apply hierarchy limits (modulation/boundaries.py)

## T5.2 Apply sensitivity scaling
- [x] bounded_delta × sensitivity (in assembler)

## T5.3 Apply memory_delta
- [x] Enforce memory bounds (assembler accepts memory_delta)

## T5.4 Clamp final vector
- [x] Ensure [0,1] (clamp01 in assembler)

## T5.5 Axis aggregation
- [x] Compute axis_final (mean of 4 sub-params)

Acceptance:
- No parameter outside [0,1]
- Deterministic replay
- Float tolerance ≤ 1e-9

---

# Phase 6 — Relational Memory

## T6.1 Implement Memory Model
- [x] user_id
- [x] interaction stats (derived; get_memory_delta_32)

## T6.2 Implement Memory Update Rules
- [x] Deterministic rules only (compute_memory_delta_32)

## T6.3 Implement memory_signature
- [x] Hash snapshot (SHA256 of user_id + events)

Acceptance:
- Memory delta bounds enforced
- IdentityCore untouched
- Replay works with memory snapshot

---

# Phase 7 — Logging Layer

## T7.1 Implement orjson serializer
- [x] orjson in core path (state_logger_v2)
- [x] No stdlib json in v2 logging

## T7.2 Implement effective_max_delta_summary
- [x] 8 values (one per axis, max of 4 sub-params)
- [x] Production record fields; debug: full 32 delta optional

## T7.3 Log replay signature
- [x] identity_hash, configuration_hash, injected_time_utc
- [x] transit_signature, memory_signature, shock_flag

Acceptance:
- Log schema validated
- Hash stable
- Debug mode outputs full detail

---

# Phase 8 — Replay System

## T8.1 Implement Replay Harness
- [x] Inputs: identity (IdentityCore), config (ReplayConfig), time, memory_delta + memory_signature
- [x] run_step_v2 in hnh/state/replay_v2.py

## T8.2 Validate Replay Determinism
- [x] N repeated runs identical (output hash + replay_match 1e-9)

Acceptance:
- Output hash identical
- Float tolerance 1e-9 respected

---

# Phase 9 — Performance & Coverage

## T9.1 Benchmark Serialization
- [x] orjson vs json (scripts/benchmark_002.py, documented in phase9.md)

## T9.2 Benchmark Daily State Computation
- [x] run_step_v2 timed in benchmark_002.py

## T9.3 Coverage Gate
- [x] Core 002 modules measured; fail_under=99 (spec §SC-005, §17)

Acceptance:
- Coverage report
- No performance regressions

---

# Phase 10 — CLI Integration (optional)

## T10.1 CLI invokes 002 flow
- [x] Entry point `hnh` (or `hnh run-v2`) uses IdentityCore v0.2, ReplayConfig, run_step_v2
- [ ] Output: params_final (32), axis_final (8); optional: legacy 7-param view or `--legacy` flag
- [ ] Same deterministic replay and logging (state_logger_v2) when CLI runs a step

Acceptance:
- `hnh run-v2 --date <date>` produces 32-parameter output (params_final, axis_final); `hnh run --date <date>` for legacy 7-param
- Replay from CLI log matches run_step_v2 contract

*Note: Scripts in `scripts/002/` already demonstrate the 002 API; this task wires the same flow into the CLI.*

---

# Cross-Cutting Constraints

- No system clock usage
- No hidden randomness
- Deterministic ordering
- Strict type validation
- Black + Ruff + Mypy enforced

---

# Definition of Done

- All tasks complete
- 99% coverage
- Replay deterministic
- Shock hard cap enforced
- Hierarchical delta resolution correct
- Logs structured via orjson
- Performance acceptable

---

End of Tasks.
