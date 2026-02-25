# Feature Specification: HnH 011 — Factorized Influence Stack (Mini-Rule) + Contribution Logging

**Feature Branch**: `011-factorized-influence-stack`  
**Created**: 2026-02-25  
**Status**: Draft  
**Depends on**: 002 (8×4 / 32D), 006 (Agent layers), 009 (sex_transit_mode), 010 (age_delta_32)

---

## Why this spec exists (problem statement)

HnH now has **32 parameters** with multiple interacting modifiers (natal base, transit deltas, memory, sex modulation, age stage deltas, optional research layers).  
As the number of influences grows, it becomes:

- difficult to **explain** why `params_final` changed,
- difficult to **calibrate** coefficients safely,
- easy to introduce "hidden" coupling (math scattered across modules),
- harder to keep **bounds** and **replay** stable.

This spec introduces a **minimal framework** (still pure Python) to systematize how influences are added and observed, without rewriting the whole model.

---

## The "mini-rule" (core idea)

> Every influence MUST be represented as an explicit, named **Factor** that produces a 32D delta (or a deterministic transform of another delta), with:
> 1) a **single integration point** in `Agent.step()`,  
> 2) **explicit bounds**, and  
> 3) **structured contribution logging** suitable for calibration.

This gives immediate leverage:
- you can see which factor moved which axis/parameter,
- you can add new influences without scattering math,
- you can cap/scale contributions consistently.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Explainability by design (P1)

As a developer, when I run `Agent.step(date)` in debug mode, I want to see a deterministic breakdown of contributions per factor, so that I can attribute changes in `params_final` to concrete inputs and coefficients.

**Acceptance scenario**
- **Given** identical inputs (natal, injected time, config, memory snapshot, sex, age_mode),  
- **When** I run `Agent.step()` twice,  
- **Then** `params_final`, `axis_final`, and `factor_breakdown` MUST match (tolerance 1e-9 for floats).

### User Story 2 — Controlled bounds for "baseline differences" (P1)

As a maintainer, I want tests that compare "baseline vs modified" runs to have **explicit numeric bounds** (no ambiguity), so that changes stay within safe limits.

**Scenario (replaces ambiguous A1 wording used across prior specs)**
- **Given** a baseline run and a modified run that differ only in one feature toggle (e.g. `age_mode=off` vs `age_mode=on`),  
- **Then** the difference MUST satisfy:
  - `max_abs_param_diff <= baseline_diff_max_abs_param` (default **0.08**)
  - `max_abs_axis_diff  <= baseline_diff_max_abs_axis`  (default **0.04**)

These defaults are aligned with existing delta conventions (`global_max_delta≈0.08` in 002 demos) and can be tightened later.

### User Story 3 — Backward compatibility (P1)

As a user of existing CLI/scripts, I want the default path to remain compatible, so that introducing the factor stack does not break existing tests unexpectedly.

**Acceptance scenario**
- **Given** `factor_stack_mode="off"` (default),  
- **When** I run the same step as before this change,  
- **Then** output MUST be identical to the legacy implementation (tolerance 1e-9).

---

## Edge Cases

- Missing `sex` while `sex_transit_mode="scale_delta"`:
  - behavior MUST match spec 009 (strict: identity multipliers; optional: deterministic default).
- Missing ephemeris files:
  - should not affect factor framework; only transit computation changes.
- `age_mode="on"` but birth date missing:
  - MUST fail fast (clear error), no silent default age.
- Factor list changes:
  - MUST change `configuration_hash` or dedicated `factor_stack_hash` so replay signatures detect it.

---

## Requirements *(mandatory)*

### Functional Requirements

#### FR-001 — Factor interface (protocol)

Introduce a deterministic interface:

- `Vector32 = tuple[float, ...]` length 32  
- `StepContext` (immutable snapshot used by factors)
- `Factor` protocol:

```python
class Factor(Protocol):
    name: str
    kind: Literal["producer", "transform"]

    def apply(self, ctx: StepContext, delta_in: Vector32 | None) -> Vector32:
        ...
```

Rules:
- **Producer** ignores `delta_in` and returns its own delta (e.g. `age_delta_32`, `memory_delta_32`).
- **Transform** takes `delta_in` and returns transformed delta (e.g. sex scaling of transit delta, final caps).

#### FR-002 — Single integration point in Agent.step()

The factor stack MUST be executed in `Agent.step(date)` as the canonical orchestration point (consistent with spec 006).

Target sequencing (conceptual):

1) `transit_state = TransitEngine.state(date, config)`  
2) compute `transit_delta_eff` (per spec 009, if enabled)  
3) compute `age_delta_32` (per spec 010, if enabled)  
4) compute `memory_delta_32` (per spec 002)  
5) compose all deltas via `FactorStack` into `delta_total_32`  
6) assemble `params_final` and `axis_final` (existing assembler rules)  

**Important**: The factor framework is about *organization + observability*.  
It MUST NOT force a redesign of existing natal/transit math; it wraps and standardizes it.

#### FR-003 — Budgeting / final safety cap (optional but recommended)

Introduce an optional "budgeted accumulation" mode to prevent runaway sums when many producers are active:

- config: `delta_budget_mode ∈ ("off", "scale_to_cap")`, default `"off"`
- if `"scale_to_cap"`:
  - compute `delta_sum[i] = Σ delta_factor[i]`
  - if `abs(delta_sum[i]) > final_delta_cap` then scale all factor contributions for that parameter by  
    `s_i = final_delta_cap / abs(delta_sum[i])` (so final hits cap exactly)
  - `final_delta_cap` defaults to `global_max_delta` from ReplayConfig (or a dedicated `final_delta_cap`, default **0.08**)

This is a "game-engine style" accumulator cap: many forces can apply, but the final impulse is limited.

#### FR-004 — Structured factor breakdown output

When debug is enabled (`debug_factors=True`), `Agent.step()` output MUST include:

- `factor_stack_mode`
- `delta_budget_mode`
- `factor_breakdown`: ordered list of objects:
  - `name`
  - `kind`
  - `mean_abs_delta`
  - `max_abs_delta`
  - `axis_mean_abs_delta[8]` (mean abs per axis; 4 params per axis)
- `delta_total_stats`: `mean_abs`, `max_abs`

#### FR-005 — Logging contract extension

If state logging is enabled (or test log capture is on), records SHOULD include `factor_breakdown` and `delta_total_stats` in addition to existing fields from 002 logging requirements.

The breakdown MUST be deterministic and diffable (JSON-compatible, stable ordering).

### Configuration

Add config keys (names may live in `ReplayConfig` or a dedicated config object, but MUST be included in replay signature):

- `factor_stack_mode` default `"off"`
- `debug_factors` default `False`
- `delta_budget_mode` default `"off"`
- `final_delta_cap` default **0.08** (or reuse `global_max_delta` if present)
- `baseline_diff_max_abs_param` default **0.08**
- `baseline_diff_max_abs_axis` default **0.04**

---

## Suggested FactorStack (v1)

A minimal recommended stack (order matters; deterministic):

1) `TransitDeltaFactor` (producer) → produces transit delta after standard bounding (002)  
2) `SexTransitScaleFactor` (transform) → applies 009 `scale_delta` to transit delta  
3) `AgeDeltaFactor` (producer) → produces 010 `age_delta_32`  
4) `MemoryDeltaFactor` (producer) → produces memory delta (002)  
5) `FinalBudgetCapFactor` (transform; optional) → applies `delta_budget_mode` / final cap

Notes:
- "Sex affects transit" stays a **transform** of transit delta (matches 009 intent).
- Age stays a **producer** (absolute shift in 32D; matches 010 intent).

---

## Tests (must be added)

### T-011-01 — Breakdown sums to total delta

- Build a deterministic `StepContext`
- Compute each factor delta
- Assert `delta_total_32[i] == Σ contributions[i]` within 1e-9 (taking transforms into account)

### T-011-02 — Determinism

- Run `Agent.step()` twice with identical inputs and `debug_factors=True`
- Assert `factor_breakdown` and `delta_total_stats` identical (tolerance 1e-9)

### T-011-03 — Baseline-diff bounds are explicit

- For a set of sample lives/dates:
  - run `age_mode=off` vs `age_mode=on` (same natal/sex/config)
  - compute diffs:
    - `max_abs_param_diff`
    - `max_abs_axis_diff`
  - assert they satisfy config bounds:
    - `<= baseline_diff_max_abs_param` (default 0.08)
    - `<= baseline_diff_max_abs_axis`  (default 0.04)

### T-011-04 — Backward compatible default

- With `factor_stack_mode="off"`:
  - assert outputs match legacy path (golden tests or replay logs)

---

## Success Criteria *(mandatory)*

- **SC-011-01**: FactorStack implementation exists with deterministic ordering and stable output schema.
- **SC-011-02**: Debug factor breakdown enables quick attribution (per-factor and per-axis deltas).
- **SC-011-03**: The ambiguous "within configured bounds" acceptance wording is replaced by explicit defaults:
  - max abs param diff ≤ **0.08**
  - max abs axis diff ≤ **0.04**
- **SC-011-04**: Default behavior (`factor_stack_mode="off"`) remains backward compatible (tolerance 1e-9).
- **SC-011-05**: All new config fields are included in replay signature / hashes, preventing silent drift.

---

## Notes / Future Work (non-blocking)

- Later, the FactorStack can become a basis for:
  - automated coefficient calibration (grid / Bayesian optimization),
  - "sensitivity audits" (which factors dominate which axes),
  - compiling factors into faster paths (NumPy / Numba) without changing semantics.
