# Implementation Plan: 009 — Sex Affects Transit Response (Dynamic Modulation)

**Branch**: `009-sex-transit-response` | **Date**: 2026-02-22 | **Spec**: [spec.md](spec.md)  
**Depends on**: 008 (E, W32, identity base_vector with sex_delta_32).  
**Clarifications** (spec § Clarifications): Agent config wins over ReplayConfig for 009 fields; debug reuses 008 opt-in mode; invalid sex_transit_mode or Wdyn_profile → fail-fast; SC-004 overlap criterion same as 008 (Cohen's d, overlap coefficient).

---

## Summary

Add optional **sex-based modulation of transit response** so that sex affects personality **over the whole span of life**, not only in the natal chart (008). Config: `sex_transit_mode ∈ {'off', 'scale_delta', 'scale_sensitivity'}` (default `off`). When `scale_delta`, compute per-parameter multipliers `M[i] = clamp(1 + beta*E*Wdyn[i], 1-mcap, 1+mcap)` and apply `transit_delta_eff[i] = bounded_delta[i] * M[i]` before state assembly. As a result, **transit-driven deltas (d_*) at every step of life** differ between male and female for the same natal/date range — the life-long expression of identity (response to transits day by day) becomes sex-dependent. Bounded, deterministic, no RNG. Implement **scale_delta** first; scale_sensitivity is optional later. Observability (multiplier_stats) via 008 debug/audit mode only. Config resolution: Agent config over ReplayConfig; invalid mode or Wdyn_profile → fail-fast. Calibration: same formal overlap criterion as 008; thresholds documented in script/config.

---

## Technical Context

**Language**: Python 3.12 (current HnH stack).  
**Dependencies**: 002 (32D schema), 006 (Agent, BehavioralCore, apply_transits, TransitState), 008 (E, identity_config, W32_v1).  
**Integration point**: In `Agent.step()`: after obtaining `transit_state` from TransitEngine, if `sex_transit_mode="scale_delta"` and E is available, compute M and `bounded_delta_eff`, then pass a TransitState-like object with `bounded_delta=bounded_delta_eff` into `behavior.apply_transits()`. No change to TransitEngine contract or to BehavioralCore signature; modulation is applied only to the delta before assembly. This applies **at every step** along the life trajectory, so identity expression over the full life span (not only natal) depends on sex.  
**Config**: `sex_transit_mode`, `beta`, `mcap`, `sex_transit_Wdyn_profile` on ReplayConfig and/or Agent config; **resolution order**: Agent config wins over ReplayConfig. Defaults: `off`, 0.05, 0.10, `"v1"`. Validate at use: invalid mode or unknown profile → fail-fast (document error type and message).  
**Testing**: pytest; unit tests for SexTransitModulator (M formula, bounds, symmetry, E=0 → M=1); integration tests for step() with scale_delta (male vs female d_* differ, mode=off d_* match, determinism); calibration script for SC-004 (mean, p95, Cohen's d / overlap as 008).  
**Constraints**: Default mode `off`; no RNG; 009 debug fields only when 008 debug/audit mode is on; no plain logging of sex/E by default (per 008).  
**Scale**: Single agent step(); calibration on N natals (e.g. ≥10k) with fixed date range and balanced sexes — script completes in reasonable time (e.g. &lt;5 min in CI).

---

## Constitution Check

- [x] **Determinism**: Same (natal, config, date, identity_hash) → same step() output; M[i] deterministic from E and Wdyn; no RNG.
- [x] **Identity/Core separation**: 008 base_vector and E remain unchanged at birth; 009 modulates only the **transit path** at each step (bounded_delta → bounded_delta_eff before assemble_state), so identity *expression* over the life span is sex-dependent while the Core snapshot is immutable.
- [x] **Behavioral parameterization**: Multipliers M[i] are numeric, versioned (Wdyn profile); no symbolic-only logic.
- [x] **Logging & observability**: multiplier_stats and 009 debug fields only when 008 debug/audit mode enabled; no separate 009 flag; no plain sex/E by default (per 008).
- [x] **Repository standards**: Python, type hints; Wdyn profile and constants auditable and versioned; fail-fast errors documented.

---

## Implementation Outline

### 1. Config and validation

- **Extend config**: Add to ReplayConfig (or a dedicated 009 config object used by Agent): `sex_transit_mode: str = "off"`, `sex_transit_beta: float = 0.05`, `sex_transit_mcap: float = 0.10`, `sex_transit_Wdyn_profile: str = "v1"`. If 009 fields live on both ReplayConfig and Agent config, **Agent config wins**; document resolution order in code and in data-model or plan.
- **Validation**: When reading 009 config (e.g. at Agent build or at first step):
  - `sex_transit_mode` MUST be in `{"off", "scale_delta", "scale_sensitivity"}`; else raise explicit error (e.g. `ValueError`). Document error type and message (FR-001).
  - `sex_transit_Wdyn_profile` MUST be a registered profile (e.g. `"v1"`); unknown or typo → raise explicit error. Document error type and message (FR-012).
- **E=0 / sex=None**: When E is 0 or sex is None, use identity multipliers M[i]=1 (no modulation); no error (FR-013).

### 2. SexTransitModulator and Wdyn profile

- **Wdyn v1**: Reuse **W32_v1** from 008 (`hnh/sex/delta_32.py` or equivalent). Register profile name `"v1"` → W32_V1. Parameter order MUST match canonical 32D order (002). Unknown profile name → fail-fast. The registry may live in `hnh/sex/transit_modulator.py` or in a separate `hnh/sex/profiles.py` module.
- **SexTransitModulator**: New component in `hnh/sex/transit_modulator.py`:
  - Input: E (float), profile name (str), beta (float), mcap (float).
  - Compute `M[i] = clamp(1 + beta * E * Wdyn[i], 1 - mcap, 1 + mcap)` for i in 0..31.
  - Output: tuple of 32 floats M; optionally also `bounded_delta_eff[i] = bounded_delta[i] * M[i]` given bounded_delta.
  - Pure function or small class; deterministic; no I/O.
- **Bounds**: Assert or test SC-002: ∀i M[i] ∈ [1-mcap, 1+mcap]. Symmetry: M(male) ≈ 2 - M(female) when E has opposite signs (test in unit tests).

### 3. Integration in Agent.step()

- **Where**: In `Agent.step(date_or_dt)` after computing `transit_state = self.transits.state(...)` and before calling `self.behavior.apply_transits(transit_state)`:
  - Resolve 009 config (Agent config over ReplayConfig).
  - If `sex_transit_mode == "off"`: pass `transit_state` unchanged to `apply_transits`.
  - If `sex_transit_mode == "scale_delta"`: get E from `self._identity_config.sex_polarity_E` (or 0 if missing). If E==0 or sex is None: pass `transit_state` unchanged. Else: compute M via SexTransitModulator; compute `bounded_delta_eff[i] = transit_state.bounded_delta[i] * M[i]`; build a new TransitState with same `stress` and `raw_delta` but `bounded_delta = bounded_delta_eff`; pass that to `self.behavior.apply_transits(...)`.
- **TransitState**: If TransitState is a dataclass or named tuple, create a copy with `bounded_delta` replaced; do not mutate TransitEngine output. Pipeline order preserved: transit_state → optional 009 scaling → assemble_state (inside BehavioralCore) → clamp01 → params_final, d_* unchanged in meaning (FR-030, FR-031, FR-032).

### 4. Debug output (008 reuse)

- When 008 debug/audit mode is enabled and 009 is active, extend step result (or the same debug payload as 008) with: `sex_transit_mode`, `beta`, `mcap`, `Wdyn_profile`, `multiplier_stats` (min_M, max_M, mean_abs(M-1)); optionally `max_abs(transit_delta)`, `max_abs(transit_delta_eff)`. No separate 009 debug flag (FR-041).

### 5. Calibration (SC-004)

- **Script**: Deterministic synthetic population (fixed seed, N≥10k natals, 50/50 sex), fixed date range; run male and female for each natal with `sex_transit_mode="scale_delta"`; compute per-axis `mean(d_axis_k(male) - d_axis_k(female))`, `p95(|d_axis_k(male) - d_axis_k(female)|)`, and **overlap** using the same formal criterion as 008 (Cohen's d ≤ threshold, e.g. 0.2; and/or overlap coefficient ≥ threshold, e.g. 0.9). Document thresholds in script or config. Fail if any axis violates SC-004.
- **CI**: Run calibration when 009 modulation params (beta, mcap, Wdyn) change, or on every PR to 009; document invocation and script path.

### 6. Tests

- **Unit**: SexTransitModulator: M formula for known E and Wdyn; bounds [1-mcap, 1+mcap]; symmetry M(male) ≈ 2 - M(female) for opposite E; E=0 or profile "v1" → M[i]=1 when E=0. Validation: invalid sex_transit_mode → fail-fast with documented error; unknown Wdyn_profile → fail-fast with documented error.
- **Integration**: Agent.step() with same natal/date range: (1) mode=off → male and female d_* identical; (2) mode=scale_delta with non-zero transit deltas → at least one d_* differs between male and female; (3) determinism: same inputs → same outputs. Step output backward compatible when mode=off (FR-040).
- **Calibration**: Run calibration script on fixed seed; assert SC-004 thresholds; document how to run locally and in CI.

---

## Target Package Layout (009 additions)

```text
hnh/
  agent.py                    # extend: resolve 009 config (Agent over ReplayConfig), validate mode/profile (fail-fast),
                              # in step(): optional 009 modulation → bounded_delta_eff → TransitState → apply_transits
  config/
    replay_config.py          # optional: add sex_transit_mode, sex_transit_beta, sex_transit_mcap, sex_transit_Wdyn_profile
                              # (or 009-specific config dataclass merged at Agent level)
  sex/
    delta_32.py               # already has W32_V1 (008); reuse for Wdyn v1
    transit_modulator.py       # NEW: SexTransitModulator — M[i] and optional bounded_delta_eff (Wdyn registry here or in profiles.py)
    # profiles.py              # optional: separate module for Wdyn profile registry if preferred
  state/
    behavioral_core.py         # no signature change: still apply_transits(transit_state); may receive TransitState with modulated bounded_delta

scripts/
  009/                         # optional
    calibration_sex_transit.py # SC-004: d_* male vs female, overlap (Cohen's d / overlap coeff), thresholds documented

tests/
  unit/
    test_009_transit_modulator.py
    test_009_config_validation.py   # invalid mode, unknown profile → fail-fast
  integration/
    test_009_sex_transit_response.py  # mode=off d_* match; scale_delta d_* differ; determinism
    test_009_calibration.py          # or under scripts/009 with pytest hook
```

If ReplayConfig is frozen (dataclass frozen=True), 009 fields may be added as optional fields with defaults, or a separate 009 config object may be passed into Agent and merged with ReplayConfig at read time (Agent config wins).

---

## Risks & Mitigations

- **Regression when mode=off**: Default `sex_transit_mode="off"` and no 009 config → pass transit_state unchanged; behavior identical to pre-009. Add integration test that mode=off yields same d_* for male/female and same as 008.
- **Config resolution**: Document clearly that Agent config overrides ReplayConfig for 009 fields; add test that verifies override.
- **TransitState copy**: Ensure creating a modified TransitState (new bounded_delta) does not break any consumer; use same type and field names so BehavioralCore sees no difference.
- **Calibration thresholds**: SC-004 thresholds (mean 0.01, p95 0.05, overlap as 008) may need tuning; make them configurable in calibration script/config so CI can enforce without code change.

---

## Out of Scope for 009

- **scale_sensitivity**: Implement scale_delta first; scale_sensitivity (FR-020) is optional and may be added later.
- Changing 008 identity or base_vector at birth; E and sex_delta_32 remain as in 008. (009 only adds sex-dependent **transit response** over the life span.)
- New UI or CLI beyond what is needed to set 009 config and run calibration.
- Separate 009 debug flag; reuse 008 debug/audit mode only.
