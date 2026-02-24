# Feature Specification: HnH 010 — Age Influence (Astrological Life Stages → 32D)

**Feature Branch**: `010-age-astrological-stages`  
**Created**: 2026-02-24  
**Status**: Draft  
**Spec-Driven Development**: [spec-kit](https://github.com/github/spec-kit) — **Plan**: [plan.md](plan.md) · **Tasks**: [tasks.md](tasks.md) · **Data model**: [data-model.md](data-model.md) · **Design detail**: [sdd.md](sdd.md)  
**Depends on**: 006 (Agent layers), 002 (8×4 / 32D), 008 (sex polarity), 009 (sex transit modulation)

---

## Clarifications

### Session 2026-02-24

- Q: When birth_datetime_utc is missing and age_mode=on, should the system treat as age_mode=off (zero delta) or raise an error? → A: Fail-fast: when birth_datetime_utc is missing and age_mode=on, the system MUST raise an explicit error (e.g. ValueError); implementation MUST document the error type and message.
- Q: When age config values are invalid (e.g. negative, zero where forbidden), fail-fast or clamp? → A: Fail-fast: invalid config MUST raise an explicit error; implementation MUST document valid ranges and the error type and message.
- Q: When step is called with e.g. 7-day gap, is Lipschitz cap L per call or scaled by days (7×L)? → A: Cap per call: max change per component between consecutive compute() calls is L (age_daily_lipschitz), regardless of calendar days between calls.
- Q: Where do age_years, age_stage_features, age_delta_32_stats appear when debug is on — in step() return value or separate debug dict or state_log? → A: Extend the object returned by step() (e.g. StepResult): when debug=True and age_mode=on, add fields age_years, age_stage_features, age_delta_32_stats to that same object.
- Q: Is an automated script or CI validating Success Criterion 5 (population guardrails) required for this feature? → A: No: treat as calibration/validation target; script or manual check may be added later; thresholds remain in spec as targets. Automated script/CI is not required for 010.

---

## Goal

Introduce **chronological age** (computed from `birth_datetime_utc`) and a deterministic **astrological life-stage model** that produces a bounded **age_delta_32** modifier applied to the 32 behavioral parameters.

This spec focuses on **absolute personality modulation** (not just step-to-step transit deltas). Age is computed from birth date; no "psychological fatigue" concepts are used here.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Compute age deterministically (P1)

As a developer, I want age to be computed deterministically from birth date and injected step time, so that replay is stable.

**Acceptance Scenarios**
1. **Given** `birth_datetime_utc` and `injected_time_utc`, **When** I compute `age_years`, **Then** the value matches `Δt / 365.2425` (within 1e-9).
2. **Given** same inputs (birth/time/config), **When** I run `Agent.step()` twice, **Then** output hashes match (determinism).

---

### User Story 2 — Age produces bounded 32D shifts (P1)

As a maintainer, I want age to create measurable, bounded shifts in the 32D vector, without breaking ranges or causing discontinuities.

**Acceptance Scenarios**
1. **Given** `age_mode="on"`, **When** I compare the same natal chart at different ages (e.g., 20y vs 40y) on the same injected time offset pattern, **Then** `params_final` differs and the difference is explained by `age_delta_32`.
2. **Given** bounds are configured, **When** `age_delta_32` is computed, **Then** `max_abs(age_delta_32) <= age_max_param_delta`.
3. **Given** two consecutive `compute()` calls (any time gap), **When** comparing outputs, **Then** for each component i: `abs(age_delta_32[i](next) - age_delta_32[i](prev)) <= age_daily_lipschitz` (default 0.001).

---

### User Story 3 — Astrological stage events show expected timing (P1)

As a researcher, I want "stage event intensity" signals to peak near well-known cycle landmarks, so calibration is interpretable.

**Acceptance Scenarios**
1. **Saturn cycle**: event intensity peaks near quarter-cycle landmarks: square/opposition/return-derived phases.
2. **Jupiter**: return intensity peaks near multiples of Jupiter orbital period.
3. **Nodal cycle**: return intensity peaks near multiples of the node precession cycle.
4. **Uranus**: opposition intensity peaks near half of Uranus orbital period (~42y).

*(Exact ages vary by ephemeris and chart; this spec uses deterministic approximations and windows.)*

---

### User Story 4 — Observability for calibration (P2)

As a researcher, I want enough decomposition to debug age effects and calibrate safely.

**Acceptance Scenarios**
1. With debug enabled, the output includes `age_years`, `age_stage_features`, and `age_delta_32_stats`.
2. With debug disabled, output remains backward compatible and minimal.

---

## Edge Cases

- Missing `birth_datetime_utc` when `age_mode="on"`: the system MUST **fail-fast** with an explicit error (e.g. `ValueError`). The implementation MUST document the error type and message. When `age_mode="off"`, missing birth_datetime_utc is not an error (age is not used).
- `injected_time_utc` < `birth_datetime_utc`: treat as `age_years = 0` (clamp to lower bound).
- Ages outside modeled range (default 0–120): clamp `age_years` to `[0, age_max_years]` for stage feature computation.
- Large date jumps: OK; must still be bounded.
- If transits are enabled, age deltas should remain an additive modifier and must not break the existing order of operations.

---

## Requirements *(mandatory)*

### Configuration

Introduce new config fields:

- `age_mode ∈ ('off', 'on')` (default `"off"`)
- `age_strength` (default **0.04**)
- `age_max_param_delta` (default **0.06**)  *(cap per-parameter)*
- `age_daily_lipschitz` (default **0.001**)  *(cap on change of each age_delta_32 component between consecutive compute() calls; not scaled by calendar days)*
- `age_profile = "v1"` (default)
- `age_max_years` (default **120**)

**Validation**: Invalid values (e.g. negative, zero where forbidden, or outside implementation-defined valid ranges) MUST cause **fail-fast**: the system MUST raise an explicit error when the config is used (e.g. at Agent or AgeEngine construction or at first `compute`). The implementation MUST document the valid ranges and the error type and message.

Timing constants (v1 defaults, deterministic):

- `TROPICAL_YEAR_DAYS = 365.2425`
- `SATURN_PERIOD_YEARS = 29.50`
- `JUPITER_PERIOD_YEARS = 11.86`
- `URANUS_PERIOD_YEARS = 84.00`
- `NODE_PERIOD_YEARS = 18.60`

---

### Data

- `birth_datetime_utc` MUST exist on Identity (or be derivable from existing birth fields) when `age_mode="on"`; otherwise the system MUST raise an explicit error (see Edge Cases).
- `injected_time_utc` is the canonical step time (already exists in 006/CLI).

---

### Age calculation

- **FR-010**: Compute:

  `age_years = clamp( (injected_time_utc - birth_datetime_utc).total_days / 365.2425 , 0, age_max_years )`

- **FR-011**: `age_years` MUST be included in debug output.

---

### Astrological life-stage feature set (v1)

Define a deterministic feature vector `age_stage_features_v1` (all values in [0,1]):

1. `maturity` (continuous, monotone):
   - `maturity = sigmoid((age_years - 25) / 7)`
2. `saturn_event` (pressure/structure landmark intensity)
3. `jupiter_return` (expansion landmark intensity)
4. `nodal_return` (direction landmark intensity)
5. `uranus_opposition` (midlife reorientation intensity)

**Event intensity function (triangular bump)**:

`bump(age, center, width) = max(0, 1 - abs(age-center)/width)`

For v1 all widths are positive constants; **width MUST be > 0** (implementation must enforce; avoids division by zero).

**Saturn landmarks** (phase-based, approximate):
- Let `p = age_years mod SATURN_PERIOD_YEARS`
- Landmark centers in years within the current Saturn cycle:
  - `C0 = 0.00` (return point)
  - `C1 = 0.25 * SATURN_PERIOD_YEARS` (square)
  - `C2 = 0.50 * SATURN_PERIOD_YEARS` (opposition)
  - `C3 = 0.75 * SATURN_PERIOD_YEARS` (square)
- Define:
  - `saturn_event = max( bump(p, C0, 1.5), bump(p, C1, 1.0), bump(p, C2, 1.0), bump(p, C3, 1.0) )`

**Jupiter return**:
- Let `pj = age_years mod JUPITER_PERIOD_YEARS`
- `jupiter_return = bump(pj, 0.0, 0.75)`

**Nodal return**:
- Let `pn = age_years mod NODE_PERIOD_YEARS`
- `nodal_return = max( bump(pn, 0.0, 1.0), bump(pn, 0.5*NODE_PERIOD_YEARS, 1.0) )`

**Uranus opposition**:
- Let `pu = age_years mod URANUS_PERIOD_YEARS`
- `uranus_opposition = bump(pu, 0.5*URANUS_PERIOD_YEARS, 2.0)`

> v1 uses simple deterministic approximations for interpretability and speed. Later versions may compute these from actual ephemeris aspects.

---

### Mapping age stages to 32 parameters (v1)

Age affects the 32D behavior vector through a bounded additive delta:

`age_delta_32[i] = clamp( age_strength * Σ_j ( feature[j] * W_age[j][i] ), -age_max_param_delta, +age_max_param_delta )`

Where:
- `feature[j] ∈ [0,1]` is one of the 5 age_stage_features_v1
- `W_age[j][i] ∈ [-1, +1]` is the v1 weight matrix

#### Parameter schema (canonical 32)

Axes and sub-parameters (canonical):

1. Emotional Tone: `warmth, empathy, patience, emotional_intensity`
2. Stability & Regulation: `stability, reactivity, resilience, stress_response`
3. Cognitive Style: `analytical_depth, abstraction_level, detail_orientation, big_picture_focus`
4. Structure & Discipline: `structure_preference, consistency, rule_adherence, planning_bias`
5. Communication Style: `verbosity, directness, questioning_frequency, explanation_bias`
6. Teaching Style: `correction_intensity, challenge_level, encouragement_level, pacing`
7. Power & Boundaries: `authority_presence, dominance, tolerance_for_errors, conflict_tolerance`
8. Motivation & Drive: `ambition, curiosity, initiative, persistence`

#### W_age v1 (compact definition)

Weights are specified per feature as a sparse mapping; unspecified params are 0.0.

**Feature: maturity**
- +patience, +resilience, +analytical_depth, +big_picture_focus
- +structure_preference, +consistency, +rule_adherence, +planning_bias
- +authority_presence, +pacing, +explanation_bias
- -reactivity, -emotional_intensity, -verbosity

```
maturity:
  patience:+0.6
  resilience:+0.5
  analytical_depth:+0.3
  big_picture_focus:+0.2
  structure_preference:+0.6
  consistency:+0.5
  rule_adherence:+0.5
  planning_bias:+0.4
  authority_presence:+0.3
  pacing:+0.3
  explanation_bias:+0.2
  reactivity:-0.4
  emotional_intensity:-0.4
  verbosity:-0.2
```

**Feature: saturn_event** (structure/limits emphasized)
- +rule_adherence, +planning_bias, +correction_intensity
- -tolerance_for_errors (stricter), -warmth (slightly)

```
saturn_event:
  rule_adherence:+0.6
  planning_bias:+0.4
  correction_intensity:+0.4
  tolerance_for_errors:-0.4
  warmth:-0.2
```

**Feature: jupiter_return** (expansion/opportunity)
- +warmth, +curiosity, +ambition, +initiative, +encouragement_level
- +big_picture_focus (slightly)

```
jupiter_return:
  warmth:+0.3
  curiosity:+0.6
  ambition:+0.4
  initiative:+0.4
  encouragement_level:+0.3
  big_picture_focus:+0.2
```

**Feature: nodal_return** (direction/purpose)
- +persistence, +initiative, +big_picture_focus, +abstraction_level
- +authority_presence (slightly)

```
nodal_return:
  persistence:+0.5
  initiative:+0.3
  big_picture_focus:+0.3
  abstraction_level:+0.2
  authority_presence:+0.1
```

**Feature: uranus_opposition** (reorientation/autonomy)
- +directness, +questioning_frequency, +conflict_tolerance
- -consistency, -rule_adherence
- +reactivity (slight), +initiative

```
uranus_opposition:
  directness:+0.4
  questioning_frequency:+0.5
  conflict_tolerance:+0.4
  consistency:-0.3
  rule_adherence:-0.4
  reactivity:+0.2
  initiative:+0.2
```

---

### Integration into Agent.step (layered architecture)

- **FR-199**: **Single place for assembly**: All computation of `params_final` and `axis_final` MUST happen inside `Agent.step()`. No caller (including `run_step_v2`) MAY call `assemble_state` or otherwise compute the agent's behavioral state outside `Agent.step()`. Callers that need a step result MUST call `Agent.step(date_or_dt, memory_delta=...)` and use the agent's resulting state. Any existing code that currently performs assembly outside `Agent.step()` MUST be refactored so that it delegates to `Agent.step()` with the appropriate inputs (e.g. `memory_delta`).
- **FR-199a**: `Agent.step()` MUST accept an optional argument `memory_delta: tuple[float, ...] | None = None`. When provided, it is passed through to the behavior assembly (together with transit effect and `age_delta_32`). When omitted, memory_delta is treated as zeros.
- **FR-200**: Introduce `AgeEngine` that outputs:
  - `age_years`
  - `age_stage_features_v1`
  - `age_delta_32`
- **FR-201**: In the behavior assembly pipeline, add `age_delta_32` as an additive modifier alongside memory/sex modifiers:

  `params_final = clamp01( params_base + bounded_delta*sensitivity + memory_delta + sex_delta + age_delta )`

- **FR-202**: Default ordering of modifiers for v1:
  1) bounded_delta*sensitivity
  2) memory_delta
  3) sex_delta (008)
  4) age_delta (010)
  5) final clamp01

  **Implementation note**: In the current codebase, 008 sex is already included in `params_base` (base_vector) at identity build time; there is no separate `sex_delta` argument to the assembly function. The assembly layer receives at most `transit_effect`, `memory_delta`, and `age_delta_32`; only `age_delta_32` is added by this spec.

- **FR-203**: `axis_final` MUST be recomputed from the final 32 vector as before.

---

### Output & Logging

- With debug enabled and `age_mode="on"`, the **object returned by `step()`** (e.g. `StepResult`) MUST include these fields on the same object:
  - `age_years` (float)
  - `age_stage_features` (tuple of 5 values)
  - `age_delta_32_stats` (dict: `max_abs`, `mean_abs`, `nonzero_count`)
  - (optional) the sparse feature contributions used to build `age_delta_32`

- With debug disabled, behavior MUST remain backward compatible unless `age_mode="on"` is explicitly set. The step() return type is extended (e.g. optional attributes on StepResult), not a separate debug container.

---

## Success Criteria *(mandatory)*

1. **Determinism**: Replay with same inputs yields identical output hashes.
2. **Bounds**:
   - `max_abs(age_delta_32) <= age_max_param_delta` (default 0.06)
   - `params_final` remains within `[0,1]`
3. **Smoothness**:
   - Between any two consecutive `compute()` calls, `max_abs(age_delta_32[i](t_next) - age_delta_32[i](t_prev)) <= age_daily_lipschitz` (default 0.001) for each component i. The cap is per call, not scaled by calendar days between calls.
4. **Calibratable stage signals**:
   - `saturn_event` shows peaks near quarter-cycle landmarks of the 29.5y cycle
   - `uranus_opposition` peaks near ~42y landmark
5. **Population guardrails** (N≥10k identities, ages 0–90 sampled) — *calibration/validation target*; an automated script or CI is **not required** for this feature; thresholds remain as targets for manual or future automated checks:
   - No axis mean shift > 0.05 solely due to age at any single age slice (unless explicitly configured)
   - Adjacent age slices (±1 year) have axis mean deltas < 0.02

---

## Notes & Future Work (non-blocking)

- Replace phase-based approximations with ephemeris-based aspects (true Saturn square/opposition/return, etc.).
- Add age-dependent modulation of transit sensitivity (analogous to 009), if needed, as a separate spec.
- Add culturally/astrologically distinct age-period systems (e.g., annual profections, Firdaria) as optional profiles.
