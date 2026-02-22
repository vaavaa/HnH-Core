# Feature Specification: HnH 009 — Sex Affects Transit Response (Dynamic Modulation)

**Feature Branch**: `009-sex-transit-response`  
**Created**: 2026-02-22  
**Status**: Draft  
**Depends on**: **008** (sex, `E` sex_polarity scalar, W32 profile, deterministic resolver)

*Main language of this spec is English.*

---

## Summary

008 applies sex as a **static** shift to identity (`base_vector`). 009 adds **dynamic** modulation of the **transit response**: with `sex_transit_mode="scale_delta"`, the transit delta vector is scaled per-parameter by multipliers derived from `E` and a versioned weight profile, so that `d_*` (axis deltas over time) differ between male and female for the same natal and date range, while remaining bounded and deterministic. Default mode is `"off"` so production behavior is unchanged unless opted in.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Sex affects `d_*` (transit-driven deltas) (Priority: P1)

As a developer using `Agent.step()` with natal + transits, I want the agent's **response to transits** (the time-delta features like `d_emotional_tone`, etc.) to differ between `male` and `female`, **without** changing the base natal personality model or breaking determinism.

**Independent Test**: Compare `d_*` (or `d_params_32`) across sexes for the **same natal**, **same date range**, with `sex_transit_mode` enabled.

**Acceptance Scenarios**:
1. **Given** identical natal, identical date range (start/end), and `sex_transit_mode="scale_delta"`, **When** I run male vs female, **Then** at least one `d_*` differs (unless transit deltas are all zeros).
2. **Given** identical natal/date range/config, **When** I run `Agent.step()` twice, **Then** outputs are identical (determinism).
3. **Given** `sex_transit_mode="off"`, **When** I run male vs female, **Then** `d_*` is identical across sexes (sex effects on transit response are disabled; 008 static shift in base_vector still applies).

---

### User Story 2 — Bounded & symmetric modulation (Priority: P1)

As a maintainer, I want the sex-based transit modulation to be **bounded** and **approximately symmetric** (male effect ≈ negative female effect around multiplier 1), so changes are small and calibratable.

**Independent Test**: Verify bounds on multiplier `M_i`, and check symmetry on `transit_delta_eff` (or derived `d_params_32`).

**Acceptance Scenarios**:
1. **Given** `E_male` and `E_female` with opposite signs, **When** computing per-parameter multipliers `M_i`, **Then** `M_i(male) ≈ 2 - M_i(female)` (mirror around 1) up to clamp limits.
2. **Given** configured caps, **When** computing multipliers, **Then** `M_i` always lies within `[1 - mcap, 1 + mcap]`.
3. **Given** a non-zero transit delta range, **When** comparing male/female `d_*`, **Then** the magnitude difference stays within calibration guardrails (see Success Criteria).

---

### User Story 3 — Observability for debugging & calibration (Priority: P2)

As a researcher, I want to log enough decomposition to explain why `d_*` differs across sexes (E, multipliers, effective transit deltas), so I can calibrate safely.

**Independent Test**: Ensure debug/research output includes required fields and stays deterministic.

**Acceptance Scenarios**:
1. **Given** debug output enabled, **When** `Agent.step()` runs, **Then** output includes `E`, `sex_transit_multiplier_stats`, and (optionally) `transit_delta_eff` summaries.
2. **Given** debug output disabled, **When** `Agent.step()` runs, **Then** output remains minimal and stable (no perf regressions).

---

### Edge Cases

- Transit delta is zero (no movement): male/female `d_*` may remain equal — acceptable.
- Clamp saturation on `params_final` can reduce symmetry — acceptable, but must be bounded.
- Missing sex / `E=0`: modulation MUST be disabled (identity multipliers `M[i]=1`).
- Modulation MUST NOT flip signs unexpectedly: default design only scales magnitudes (multipliers around 1).
- If `sex_transit_mode="off"`, the pipeline MUST behave exactly as before 009 (no modulation layer).

---

## Requirements *(mandatory)*

### Functional Requirements

#### Mode & toggles
- **FR-001**: System MUST introduce `sex_transit_mode ∈ {'off', 'scale_delta', 'scale_sensitivity'}` with default `"off"`.
- **FR-002**: With `sex_transit_mode="off"`, the system MUST match baseline behavior (no change to transit response; 008 static base_vector shift still applies).
- **FR-003**: Sex transit modulation MUST use `E` computed in **008** (sex polarity scalar from identity).

#### Modulation strategy (default: scale transit delta)
- **FR-010 (default)**: With `sex_transit_mode="scale_delta"`, the system MUST scale the **transit delta vector** per-parameter before it is used to compute transit effect:

    `transit_delta_eff[i] = transit_delta[i] * M[i]`

  Here "transit delta" is the **bounded_delta** from `TransitState` (006/008 pipeline). The effective transit effect passed into state assembly remains `transit_delta_eff[i] * sensitivity[i]` (or equivalent), so modulation applies only to the transit component, not to natal/static components.

- **FR-011**: The per-parameter multiplier MUST be computed deterministically as:

    `M[i] = clamp( 1 + beta * E * Wdyn[i], 1 - mcap, 1 + mcap )`

  where:
  - `beta` is a small scalar (default **0.05**)
  - `mcap` caps deviation from 1 (default **0.10**, i.e. multipliers in [0.9, 1.1])
  - `Wdyn[i] ∈ [-1, +1]` is a versioned weight profile (default: reuse **W32_v1** from spec 008)

- **FR-012**: `Wdyn` MUST be versioned (e.g. `sex_transit_Wdyn_profile="v1"`), auditable, and deterministic. Parameter order MUST match the canonical 32D order (spec 002, 8 axes × 4 sub-parameters).
- **FR-013**: If `E=0` or `sex=None`, the system MUST use identity multipliers `M[i]=1` (no modulation).

#### Alternative strategy (optional): scale sensitivity
- **FR-020 (optional)**: With `sex_transit_mode="scale_sensitivity"`, the system MAY scale the effective sensitivity used to apply transit deltas:

    `sensitivity_eff[i] = sensitivity[i] * M[i]`

  using the same multiplier definition as FR-011.

> Recommendation: implement `scale_delta` first; it is easier to reason about and test.

#### Integration point
- **FR-030**: Transit modulation MUST be applied **only to the transit component**, not to natal/static components (base_vector from 008 is unchanged).
- **FR-031**: The modulation MUST be applied before final clamp01 of `params_final`, and MUST preserve the overall pipeline order (transit_state → bounded_delta → optional scaling → assemble_state).
- **FR-032**: The resulting `d_*` (axis deltas) MUST be computed from the same final params as before, ensuring consistent meaning.

#### Output / debug fields
- **FR-040**: `Agent.step()` output MUST remain backward compatible in default mode (`sex_transit_mode="off"`).
- **FR-041**: With debug enabled, output SHOULD include:
  - `sex`, `E`
  - `sex_transit_mode`, `beta`, `mcap`, `Wdyn_profile`
  - `multiplier_stats`: `min_M`, `max_M`, `mean_abs(M-1)`
  - (optional) `max_abs(transit_delta)`, `max_abs(transit_delta_eff)`

---

### Key Entities

- **SexTransitModulator**: Applies FR-010..FR-013 to compute `M[i]` and `transit_delta_eff` (or `sensitivity_eff` for scale_sensitivity).
- **Wdyn Profile**: Versioned vector `Wdyn[32]` (default: reuse W32_v1 from 008).
- **Calibration report**: Metrics for `d_*` differences across sexes on a fixed dataset.

---

## Integration with 006 and 008

### Pipeline order

1. **Identity** (008): `base_vector` includes `sex_delta_32`; `E` and `sex` are fixed at identity build.
2. **Step(date)** (006): (1) `transit_state` = TransitEngine.state(date) → `raw_delta`, `bounded_delta`; (2) lifecycle if present; (3) **009 (if enabled)**: compute `M[i]` from `E` and Wdyn; compute `bounded_delta_eff[i] = bounded_delta[i] * M[i]`; (4) `behavior.apply_transits(transit_state_with_eff)` or equivalent so that state assembly uses the modulated delta; (5) clamp01 → `params_final`, `d_*` derived as usual.

Modulation MUST NOT change the contract of `TransitEngine` or the meaning of `bounded_delta` outside the modulation layer; the modulator consumes `bounded_delta` and produces the effective delta passed into `assemble_state` (or equivalent).

### Data locations

- **Config**: `sex_transit_mode`, `beta`, `mcap`, `sex_transit_Wdyn_profile` (e.g. on ReplayConfig or Agent config). Defaults: `off`, 0.05, 0.10, `"v1"`.
- **Identity**: `E` (and optionally `sex`) from 008 identity_config; no new identity fields required.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 Determinism**: For fixed natal/date range/config/identity_hash, repeated runs produce identical outputs.
- **SC-002 Multiplier bounds**: `∀i: M[i] ∈ [1-mcap, 1+mcap]` (default [0.9, 1.1]).
- **SC-003 Sex affects transit response**:
  - For the same natal/date range with non-zero transit deltas and `sex_transit_mode="scale_delta"`, `d_axis_male` and `d_axis_female` differ for at least one axis.
  - With `sex_transit_mode="off"`, male/female `d_axis` MUST match (same transit response).

- **SC-004 Calibration guardrails** (balanced sexes, N≥10k natals, fixed date range):
  - For each axis k: `|mean(d_axis_k(male) - d_axis_k(female))| ≤ 0.01`
  - For each axis k: `p95(|d_axis_k(male) - d_axis_k(female)|) ≤ 0.05`
  - Distributions overlap substantially (no near-separation).

> Notes: Thresholds are tighter than 008 because `d_*` values are typically smaller than absolute axis values. Thresholds MAY be made configurable for calibration scripts.

---

## Notes / Implementation Constraints

- Default mode MUST be `"off"` to avoid silent behavior changes in production.
- Multipliers MUST be deterministic; no RNG.
- Prefer reusing W32 profile for Wdyn v1 to reduce degrees of freedom; later you can split if needed.
- Logging should be optional and lightweight: record multiplier stats, not full vectors unless explicitly enabled.
- **Privacy**: Same as 008 — by default do not log sex, E, or identity in plain form; opt-in debug only and documented.

---

## References

- **008**: [../008-sex-polarity-32d-shifts/spec.md](../008-sex-polarity-32d-shifts/spec.md) — E, W32_v1, sex_delta_32, base_vector, identity.
- **006**: [../006-layered-agent-architecture/spec.md](../006-layered-agent-architecture/spec.md) — Agent, BehavioralCore, apply_transits, TransitState.
- **002**: [../002-hierarchical-personality-model/spec.md](../002-hierarchical-personality-model/spec.md) — 32D parameter order for Wdyn alignment.
