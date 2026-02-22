# Feature Specification: HnH 008 — Sex Polarity & 32D Shifts

**Feature Branch**: `008-sex-polarity-32d-shifts`  
**Created**: 2026-02-22  
**Status**: Draft  
**Input**: User description: "Add binary sex (male/female) with deterministic computation option and introduce calibrated sex-based shifts in 32D (8 axes ×4). Age is postponed to spec 009."

*Main language of this spec is English; key principles are duplicated in Russian where noted.*

---

## Input contract: sex is external

- **Пол задаётся снаружи**: в систему передаются **дата рождения** (и прочие натальные данные) и **пол личности**. Пол не выводится внутри функций движка; это входной параметр личности.
- **Режим explicit (по умолчанию)**: если вызывающая сторона передала `sex` в `birth_data`, он используется как есть. Если не передала — пол считается отсутствующим (`sex=None`), сдвиги по полу не применяются (E=0, `sex_delta_32=0`).
- **Режим infer**: опциональный fallback только когда пол **не передан** снаружи (например, синтетические популяции); тогда система может вычислить его детерминированно по наталу. В нормальном (production) сценарии пол всегда приходит извне вместе с датой рождения.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Explicit sex in production (Priority: P1)

As a developer building an HnH agent for product use, I want to set `sex` explicitly (`male|female`) so that the agent's 32D behavior includes small, controlled sex-based shifts, while keeping legacy behavior unchanged when `sex` is not provided.

**Why this priority**: This is the safest production path: explicit, auditable, and avoids "hidden physics changes".

**Independent Test**: Can be fully tested by running `Agent.step()` with the same natal inputs twice (determinism), and comparing outputs for `sex=None` vs `sex=male/female`.

**Acceptance Scenarios**:
1. **Given** `sex_mode="explicit"` and `birth_data.sex` is missing, **When** `Agent.step()` runs, **Then** `sex=None`, `E=0`, and `sex_delta_32` is all zeros (baseline preserved).
2. **Given** `sex_mode="explicit"` and `birth_data.sex="male"`, **When** `Agent.step()` runs, **Then** output includes `sex="male"`, `E!=0` (unless configured otherwise), and `params_final` differs from baseline within configured bounds.
3. **Given** `sex_mode="explicit"` and `birth_data.sex="female"`, **When** `Agent.step()` runs, **Then** `sex="female"` and resulting `sex_delta_32` is approximately the negative of the male delta (up to clamp saturation).
4. **Given** identical inputs (same natal, same config, same date), **When** `Agent.step()` runs twice, **Then** outputs are byte-for-byte identical (determinism).

---

### User Story 2 — Deterministic sex inference for synthetic agents (Priority: P2)

As a researcher or simulation user, I want the system to infer `sex` deterministically from natal polarity (+ optional sect), so that large synthetic populations have reproducible sex assignment without RNG.

**Why this priority**: Simulation needs deterministic labeling; inference must be optional and explicit to prevent regressions.

**Independent Test**: Can be tested by running sex inference twice on the same natal + identity_hash and verifying identical inferred sex.

**Acceptance Scenarios**:
1. **Given** `sex_mode="infer"` and `birth_data.sex` is missing, **When** `SexResolver` runs, **Then** sex is chosen using the inference algorithm (below) deterministically.
2. **Given** the computed score `S` falls within the tie zone `[-T, +T]`, **When** resolving sex, **Then** a deterministic tie-break is used (identity_hash parity) and is stable across runs.
3. **Given** insufficient natal data to compute polarity score (missing required planet signs), **When** resolving sex in infer mode, **Then** the system MUST fail fast with a clear error OR fall back to `sex=None` according to config (must be specified and tested).

---

### User Story 3 — Calibration guardrails & distribution sanity (Priority: P3)

As a maintainer, I want calibration guardrails and automated checks so that sex shifts remain small, symmetric, and do not create non-overlapping male/female populations.

**Why this priority**: Without guardrails, tuning can drift toward unrealistic separation or unintended bias.

**Independent Test**: Can be tested by running a calibration script on a fixed dataset of natals and verifying metric thresholds.

**Acceptance Scenarios**:
1. **Given** a balanced dataset of natals (50/50 male/female), **When** calibration metrics are computed, **Then** mean axis differences are near zero and distributions overlap (per thresholds below).
2. **Given** `sex_strength` or `W32` is changed, **When** CI runs calibration sanity checks, **Then** guardrails must fail if thresholds are violated.

---

### Edge Cases

- What happens when `sex_mode="explicit"` but `sex` is absent? (Must default to baseline / no effect.)
- What happens when `sex_mode="infer"` but natal lacks some planet signs? (Configurable: fail-fast or no-effect; must be explicit.)
- What happens when Sun altitude equals exactly 0 (horizon)? (Sect becomes `unknown`, `sect_score=0`.)
- What happens when `E*strength*W32[i]` would push `params_final[i]` outside [0,1]? (Clamp01 must handle it deterministically.)
- What happens when clamp saturation breaks perfect symmetry? (Expected; tests should allow it.)
- What happens when dates/timezones are ambiguous in natal? (Spec 008 does not change natal parsing rules; uses existing natal outputs.)
- What happens when `birth_data.sex` is an invalid value (e.g. typo, empty string, wrong type)? (MUST either fail-fast or be treated as `None`; implementation MUST document which. See FR-001.)

---

## Requirements *(mandatory)*

### Functional Requirements

#### Sex field and modes
- **FR-001**: System MUST support `sex ∈ {"male","female"}` and allow `None` for backward compatibility. Any other value (typo, empty string, wrong type) MUST be rejected: either fail-fast with a clear error or be treated as `None`; the implementation MUST document which behavior is used.
- **FR-002**: System MUST support `sex_mode ∈ {"explicit","infer"}` with default `"explicit"`.
- **FR-003**: In `"explicit"` mode, if `sex` is not provided, system MUST produce `E=0` and `sex_delta_32=0` (no behavioral change).
- **FR-004**: In `"infer"` mode, if `sex` is not provided, system MUST infer sex deterministically using the algorithm in **FR-010..FR-015**.

#### Astro-derived signals
- **FR-005**: System MUST compute `sign_polarity(sign) ∈ {+1,-1}` using the mapping in **FR-011**.
- **FR-006**: System MUST compute `sign_polarity_score ∈ [-1,+1]` as a planet-weighted average. Formula: `sign_polarity_score = (Σ weight_p × sign_polarity(sign_p)) / (Σ weight_p)` where the sum is over **only planets with a known sign** (weights from **FR-012**). Planets without a known sign are excluded; if no planet has a sign, the score is undefined and infer mode MUST use the insufficient-data rule (see **Infer mode: insufficient natal data** below).
- **FR-007**: System MUST compute `sect_score ∈ {-1,0,+1}` using Sun altitude when available, otherwise use the fallback rule in **FR-013** (configurable).

#### Sex polarity scalar E
- **FR-008**: System MUST compute `sex_score = +1 (male), -1 (female), 0 (None)`.
- **FR-009**: System MUST compute `E = clamp(a*sex_score + b*sign_polarity_score + c*sect_score, -1, +1)` with configurable coefficients and defaults **a=0.70, b=0.20, c=0.10**. In explicit mode, the default thus includes astro terms (b, c ≠ 0), so the same explicit sex can yield slightly different E for different natals. To have E depend only on sex, set **b=0, c=0** in config (optional “E from sex only” mode).

#### Inference algorithm (deterministic)
- **FR-010**: In infer mode, system MUST compute `S = k1*sign_polarity_score + k2*sect_score + bias` with defaults `k1=1.0, k2=0.2, bias=0.0`.
- **FR-011**: Polarity mapping MUST be fixed and auditable:
  - +1 for: Aries, Gemini, Leo, Libra, Sagittarius, Aquarius
  - -1 for: Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces
- **FR-012**: Default planet weights MUST be:
  - Sun=2.0, Moon=2.0
  - Mercury=1.5, Venus=1.5, Mars=1.5
  - Jupiter=1.0, Saturn=1.0
  - Uranus=0.5, Neptune=0.5, Pluto=0.5
- **FR-013**: Sect rules:
  - Preferred: if `sun_altitude_deg > 0` => day (+1), `< 0` => night (-1), `== 0` => unknown (0).
  - Fallback (if altitude unavailable): use Sun house number. **Day sect** (+1): Sun in houses **7, 8, 9, 10, 11, 12** (inclusive). **Night sect** (-1): Sun in houses **1, 2, 3, 4, 5, 6** (inclusive). Boundary 6/7 is exclusive (house 6 → night, house 7 → day). House numbering and system (e.g. Placidus) follow the same convention as the rest of the natal pipeline. Missing house or Sun => unknown (0).
- **FR-014**: Default inference threshold MUST be `T=0.10`:
  - if `S > +T` => sex=male
  - if `S < -T` => sex=female
  - else => tie-break
- **FR-015**: Tie-break MUST be deterministic, default: `identity_hash_parity`:
  - `male` if the low bit of a **deterministic** hash of `identity_hash` is 1, else `female`. The hash function MUST be stable across process runs (e.g. SHA-256); not Python’s built-in `hash()`. Source of `identity_hash` and exact algorithm: [data-model.md](data-model.md).

#### Infer mode: insufficient natal data

When natal data are insufficient to compute `sign_polarity_score` (e.g. no planets with known sign, or required planets missing), behavior in infer mode MUST be configurable and explicit:

- **Config option**: Implementation MUST support a setting such as **`infer_on_insufficient_data`** (or equivalent) with values **`"fail"`** (fail-fast with a clear error) or **`"none"`** (fall back to `sex=None`). Default MUST be documented (recommended: `"fail"` for reproducibility).
- **Required for inference**: At least **Sun** MUST have a known sign to compute a valid polarity score for inference; implementations MAY require more planets and MUST document the minimal set. See [data-model.md](data-model.md).
- **Output when fallback to `sex=None`**: When fallback is used, `Agent.step()` output MUST report `sex=None` and MUST NOT apply sex_delta_32 (E=0). Optionally the output MAY include a flag such as `sex_inference_skipped: true` for logging; if present, it MUST be documented.

#### 32D shifts (sex_delta_32)
- **FR-016**: System MUST define a versioned `W32` profile (default `v1`) mapping E to 32D deltas.
- **FR-017**: System MUST compute `sex_delta[i] = clamp(strength * E * W32[i], -max_param_delta, +max_param_delta)` with defaults `strength=0.03`, `max_param_delta=0.04`.
- **FR-018**: System MUST apply `sex_delta_32` when assembling **identity** (base_vector). Sex is given at birth and is part of identity; therefore `sex_delta_32` is applied **before** transit application. Concretely: `base_vector` (or the identity-level 32D state supplied to BehavioralCore) MUST already include `sex_delta_32`; then `apply_transits(transit_state)` adds the transit delta on top. Final per-step clamp to [0,1] remains after all deltas.
- **FR-019**: System MUST clamp final parameters to [0,1] deterministically.

#### Output / observability
- **FR-020**: `Agent.step()` output MUST include `sex` and `sex_polarity_E` (E).
- **FR-021**: In debug/research output mode, the system SHOULD also include `sign_polarity_score`, `sect`, `sect_score`, and `sex_delta_32`.

#### 32D schema alignment

- **FR-022a**: The order of the 32 parameters in W32 and in `sex_delta_32` MUST match the **canonical 32D parameter order** of the project (8 axes × 4 sub-parameters). That order is defined by the hierarchical personality model; see [spec 002](../002-hierarchical-personality-model/spec.md) and any contract or schema that fixes the axis and parameter indices (e.g. axis 1 = Emotional Tone, indices 0–3; axis 2 = Stability & Regulation, indices 4–7; etc.). Implementations MUST NOT reorder or assume a different mapping.

#### Default W32 profile (v1)
- **FR-022**: Default `W32` profile `v1` MUST be exactly:

Axis 1 — Emotional Tone (warmth, empathy, patience, emotional_intensity):  
`[-1, -1, -1, +1]`

Axis 2 — Stability & Regulation (stability, reactivity, resilience, stress_response):  
`[+1, +1, -1, +1]`

Axis 3 — Cognitive Style (analytical_depth, abstraction_level, detail_orientation, big_picture_focus):  
`[-1, +1, -1, +1]`

Axis 4 — Structure & Discipline (structure_preference, consistency, rule_adherence, planning_bias):  
`[+1, -1, -1, +1]`

Axis 5 — Communication Style (verbosity, directness, questioning_frequency, explanation_bias):  
`[-1, +1, -1, -1]`

Axis 6 — Teaching Style (correction_intensity, challenge_level, encouragement_level, pacing):  
`[+1, +1, -1, -1]`

Axis 7 — Power & Boundaries (authority_presence, dominance, tolerance_for_errors, conflict_tolerance):  
`[+1, +1, -1, +1]`

Axis 8 — Motivation & Drive (ambition, curiosity, initiative, persistence):  
`[+1, -1, +1, -1]`

---

### Key Entities *(include if feature involves data)*

- **SexResolver**: Pure component that returns `sex` based on config mode and inputs (explicit/infer).
- **SignPolarityEngine**: Computes `sign_polarity_score` from natal planet signs and planet weights.
- **SectEngine**: Computes `sect` and `sect_score` from Sun altitude (preferred) or Sun house (fallback).
- **SexPolarityEngine**: Computes `E` from `sex_score`, `sign_polarity_score`, `sect_score`.
- **SexDelta32Engine**: Computes `sex_delta_32` from `E`, `W32`, and clamps.
- **W32 Profile**: Versioned vector of 32 weights used for mapping `E → sex_delta_32`.
- **Calibration Profile**: Thresholds/metrics (mean diff, mean abs diff, p95 abs diff) used to guard tuning.

---

## Integration with 006

Sex is given at birth and belongs to **identity**; the 32D pipeline MUST apply sex shift before transit.

### Data locations

- **`birth_data.sex`**: Optional `"male" | "female"`. **Внешний вход**: пол личности передаётся в систему вместе с датой рождения и не выводится внутри. Явный источник пола при передаче — см. [data-model.md](data-model.md).
- **`sex_mode`**: `"explicit" | "infer"`, default `"explicit"`. May live on `birth_data`, agent config, or a dedicated sex config; the implementation MUST document where it is read. See [data-model.md](data-model.md).
- **`identity_hash`**: Used for deterministic tie-break in infer mode (FR-015). Source MUST be a value that is part of identity and stable for the same agent (e.g. derived from `birth_data` or from `identity_config`). Exact field and derivation are defined in [data-model.md](data-model.md); implementations MUST use the same source for tie-break and for step output so that determinism holds.

### Pipeline order (006 step vs 008)

1. **Identity assembly** (before any `step(date)` or at Agent build): From natal (and optionally memory) the system builds the identity-level 32D state. **Sex is part of identity**: resolve `sex` (explicit or infer), compute `E` and `sex_delta_32`, and add `sex_delta_32` into the **base_vector** (or equivalent) that BehavioralCore receives. So `base_vector` = natal_base + sex_delta_32 (+ any other identity-level terms). No transit is applied yet.
2. **Step(date)** (006 order unchanged): (1) Compute `transit_state`; (2) Update lifecycle if present; (3) `behavior.apply_transits(transit_state)` — i.e. add transit delta to `current_vector`. The vector that transits modify already includes the sex shift.

Thus **sex_delta_32 is applied before transit**; it is fixed at identity level and does not change with date.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Determinism — for fixed inputs (natal, config, date, identity_hash), repeated `Agent.step()` runs produce identical outputs.
- **SC-002**: Symmetry — for same natal/date, `sex_delta_32(male) ≈ -sex_delta_32(female)` (differences only due to clamp01 saturation).
- **SC-003**: Bounds — `params_final` always lies in [0,1], and `max(|sex_delta[i]|) <= max_param_delta`.
- **SC-004**: Calibration sanity (balanced sexes, N=10k natals):
  - For each axis k: `|mean(axis_male - axis_female)| <= 0.01`
  - `p95(|axis_male - axis_female|) <= 0.10`
  - Distributions overlap substantially (no near-separation)

---

## Calibration (source, metrics, CI)

- **Data source**: Calibration checks MUST use a well-defined dataset: either a **fixed regression dataset** committed in the repo (e.g. a fixed list of natals with assigned sex and expected bounds) or a **deterministic synthetic population** (fixed seed, N natals, 50/50 sex assignment). The implementation MUST document which source is used and where it is stored (path or artifact).
- **Overlap criterion**: “Distributions overlap substantially” MUST be made testable. Recommended formal criterion: for each axis, **Cohen’s d** (male vs female) MUST be below a threshold (e.g. 0.2), and/or **overlap coefficient** (or equivalent) MUST be above a threshold (e.g. 0.9). Exact thresholds and formula MUST be documented in the calibration script or config.
- **CI**: When `sex_strength` or W32 is changed, CI MUST run the calibration sanity check (e.g. a script that loads the fixed dataset, runs step for each natal, computes mean diff, p95, and overlap metric, and fails if any threshold is violated). The script and its invocation (e.g. in GitHub Actions) MUST be documented; the dataset or seed MUST be fixed so that runs are reproducible.

---

## Rationale & Semantics

- **Human context**: The project is *Human Needs Human* — agents model human-like needs and behavior. In real life, a person perceiving another person deterministically attributes sex (male or female) as part of social perception; the system is intended to reflect this.
- **Biological baseline**: At birth humans have two sexes (male/female), with rare exceptions. The model uses a binary `sex` for compatibility with this baseline and with deterministic, auditable behavior; it does not claim to cover all biological or identity edge cases.
- **Design consequence**: Supporting explicit `sex` and optional deterministic inference allows the engine to apply small, calibrated 32D shifts that match how humans are perceived along these dimensions, while keeping legacy behavior when `sex` is not provided.

---

## Notes / Implementation Constraints

- Inference MUST be opt-in. Default behavior MUST preserve baseline for legacy data (no silent physics changes).
- All tie-breaks MUST be deterministic (no RNG).
- All weights and constants MUST be versioned and auditable (W32 profile names).

---

## References

- **Data model (008)**: [data-model.md](data-model.md) — `birth_data.sex`, `sex_mode`, source of `identity_hash`, infer_on_insufficient_data, sex source priority, pipeline summary.
- **006 (layered agent)**: [../006-layered-agent-architecture/spec.md](../006-layered-agent-architecture/spec.md) — Agent, BehavioralCore, identity_config, step order.
- **002 (32D schema)**: [../002-hierarchical-personality-model/spec.md](../002-hierarchical-personality-model/spec.md) — 8 axes × 4 parameters, canonical parameter order for W32 alignment.
