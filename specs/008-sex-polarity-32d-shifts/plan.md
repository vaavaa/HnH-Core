# Implementation Plan: 008 — Sex Polarity & 32D Shifts

**Branch**: `008-sex-polarity-32d-shifts` | **Date**: 2026-02-22 | **Spec**: [spec.md](spec.md)  
**Input**: Binary sex (male/female) as external input; optional deterministic inference from natal polarity + sect; calibrated 32D shifts applied at identity level (before transit). Age deferred to spec 009.  
**Clarifications** (spec § Clarifications): invalid sex → fail-fast; insufficient natal data in infer → only fail-fast (no fallback to sex=None); no plain logging of sex/birth_data by default; sex_mode resolution birth_data first then config; calibration recommended synthetic (fixed seed).

---

## Summary

Implement sex as an external input to identity: **birth_data.sex** and **sex_mode** (explicit / infer). Add pure components **SignPolarityEngine**, **SectEngine**, **SexResolver**, **SexPolarityEngine**, **SexDelta32Engine** and a versioned **W32** profile (v1). Apply **sex_delta_32** when building **base_vector** (identity assembly), before BehavioralCore and before any transit — so sex is part of identity and does not change with date. Agent.step() output includes `sex` and `sex_polarity_E`; invalid sex causes fail-fast; infer defaults to fail on insufficient natal data; logging of sex/birth_data only opt-in and documented. Calibration: deterministic synthetic population (fixed seed) with documented thresholds; CI runs sanity checks when W32/sex_strength change.

---

## Technical Context

**Language**: Python 3.12 (current HnH stack)  
**Dependencies**: 002 (32D schema, parameter order), 006 (Agent, BehavioralCore, identity assembly, NatalChart), natal/astrology (planet signs, houses, Sun altitude when available)  
**Testing**: pytest; unit tests for each engine (SignPolarity, Sect, SexResolver, SexPolarity, SexDelta32); integration tests for identity assembly with sex, Agent.step() output, determinism, symmetry male/female; calibration script + CI gate  
**Constraints**: Sex is external (never derived in production path when explicit); sex_delta_32 applied only at identity build, not in step(); deterministic hash for tie-break (e.g. xxhash per project rules); no RNG; FR-021a: no plain logging of sex/birth_data by default  
**Scale**: Single agent identity build; calibration run on N natals (e.g. 10k) with fixed seed — script must complete in reasonable time (e.g. <5 min in CI)

---

## Constitution Check

- [ ] **Determinism**: Same (birth_data, config, date, identity_hash) → same step() output; sex inference and E use only deterministic logic; tie-break via deterministic hash (e.g. xxhash).
- [ ] **Identity/Core separation**: Sex is part of identity; base_vector = natal_base + sex_delta_32 is built once at identity assembly; BehavioralCore never mutates base_vector; Dynamic State (step) does not recompute sex.
- [ ] **Behavioral parameterization**: Sex maps to scalar E and to 32D deltas (W32); no symbolic-only logic; weights and W32 versioned.
- [ ] **Logging & observability**: step() output includes sex and sex_polarity_E; debug/research may expose sign_polarity_score, sect, sex_delta_32; FR-021a: by default do not log sex/birth_data in plain form; opt-in audit mode documented.
- [ ] **Repository standards**: Python, type hints, orjson/xxhash where applicable; W32 and constants auditable and versioned.

---

## Implementation Outline

### 1. Data and contracts

- **birth_data**: Extend accepted shape to include optional `sex: "male" | "female" | None` and optional `sex_mode: "explicit" | "infer"`. Validate sex: if present and not in `{"male","female"}`, **fail-fast** with explicit error (e.g. `ValueError`); document error type and message (FR-001).
- **sex_mode resolution**: Implement order **birth_data.sex_mode first, then agent/replay config**; default `"explicit"`. Document in code and in data-model.
- **identity_hash**: Define single source for tie-break (e.g. digest of birth_data or identity_config field); use deterministic hash (e.g. xxhash.xxh3_128) for parity; document in data-model.

### 2. SignPolarityEngine

- Input: natal (planet → sign mapping), planet weights (FR-012 default).
- Formula: `sign_polarity_score = (Σ weight_p × sign_polarity(sign_p)) / (Σ weight_p)` over planets with known sign only. Polarity mapping FR-011 (fixed +1/-1 per sign). Return value in [-1, 1]. If no planet has sign, infer path MUST raise (no fallback).
- Placement: e.g. `hnh/sex/sign_polarity.py` or `hnh/astrology/sex_polarity.py`. Pure function or small class; no I/O.

### 3. SectEngine

- Input: Sun altitude (preferred) or Sun house number.
- Rules: altitude > 0 → day (+1), < 0 → night (-1), == 0 → unknown (0). Fallback: houses 7–12 → day, 1–6 → night; boundary 6/7 exclusive; missing → unknown.
- Output: sect_score in {-1, 0, +1}. Placement: same module as SignPolarity or `hnh/astrology/sect.py`. Use same house numbering as rest of natal pipeline.

### 4. SexResolver

- Input: birth_data (sex, sex_mode), natal, config (identity_hash source).
- Logic: If sex_mode from birth_data then config (resolution order). If explicit: use birth_data.sex (validate or fail-fast). If infer: compute sign_polarity_score (if insufficient data → raise; no fallback to sex=None). Compute S = k1*sign_polarity_score + k2*sect_score + bias; if S > T → male, S < -T → female, else tie-break via deterministic hash(identity_hash) parity. Default T=0.10, k1=1.0, k2=0.2, bias=0.0.
- Output: `"male" | "female" | None`. Placement: `hnh/sex/resolver.py` or under identity.

### 5. SexPolarityEngine

- Input: sex (resolved), sign_polarity_score, sect_score; config (a, b, c defaults 0.70, 0.20, 0.10).
- E = clamp(a*sex_score + b*sign_polarity_score + c*sect_score, -1, 1). sex_score: male +1, female -1, None 0.
- Output: float E. Placement: `hnh/sex/polarity.py` or same module as resolver.

### 6. SexDelta32Engine and W32 profile

- **W32 v1**: 32-element vector per spec FR-022 (8 axes × 4), exact values listed in spec. Store as versioned constant (e.g. `W32_V1`).
- Input: E, sex_strength (default 0.03), sex_max_param_delta (default 0.04). sex_delta[i] = clamp(sex_strength * E * W32[i], -sex_max_param_delta, +sex_max_param_delta). Bounds: BOUND-32-1/2/3, BOUND-AXIS-1, BOUND-VEC-1 (see spec).
- Output: tuple of 32 floats. Placement: `hnh/sex/delta_32.py` or `hnh/sex/profiles.py` + `delta_32.py`. Order of W32 MUST match canonical 32D parameter order (002).

### 7. Identity assembly integration (006 + 008)

- **Where**: Identity is built when constructing the object that provides `base_vector` and `sensitivity_vector` to BehavioralCore. Currently `_build_identity_config_from_natal` in `hnh/agent.py` builds base_vector = (0.5,*32) and sensitivity from natal. For 008:
  - Read birth_data.sex and sex_mode (resolution order); validate sex (fail-fast if invalid).
  - Resolve sex (SexResolver) → get resolved_sex.
  - If resolved_sex is None: E = 0, sex_delta_32 = (0,*32). Else: compute E (SexPolarityEngine), compute sex_delta_32 (SexDelta32Engine).
  - base_vector = natal_base + sex_delta_32 (element-wise), then clamp to [0,1] if needed (or ensure natal_base + sex_delta_32 stays in [0,1] by construction; spec says final params clamped at step level, identity base should already be valid range).
  - Pass this base_vector (and sensitivity_vector) to BehavioralCore. BehavioralCore and step() unchanged except that they receive the sex-adjusted base.
- **Natal base**: If current code uses (0.5,*32), then natal_base remains that and we add sex_delta_32; result may need clamp to [0,1] for base_vector (spec FR-019: final params in [0,1]; identity base is pre-transit so same constraint).
- **Agent.__init__**: Ensure birth_data is passed to identity builder; config (ReplayConfig or extended) carries sex_mode if not on birth_data; insufficient data in infer → fail only. identity_hash source: e.g. from birth_data digest or from identity_config if provided.

### 8. Agent.step() output

- step() currently may return void or internal state. Spec FR-020: output MUST include `sex` and `sex_polarity_E`. Extend return value or side-channel (e.g. last_step_output) to include `sex`, `sex_polarity_E`; in debug/research mode also `sign_polarity_score`, `sect`, `sect_score`, `sex_delta_32` (FR-021). Ensure no plain logging of sex/birth_data by default (FR-021a).

### 9. Calibration

- Script: build deterministic synthetic population (fixed seed, e.g. N=10k natals, 50/50 sex assignment); run step for each; compute per-axis mean difference, p95, and overlap metric (e.g. Cohen’s d ≤ 0.2 or overlap coefficient ≥ 0.9). Fail if thresholds violated. Document seed and thresholds in script or config.
- CI: Run calibration when sex_strength or W32 changes (or on every PR to 008); document invocation and location of script.

### 10. Tests

- **Unit**: SignPolarityEngine (formula, weights, missing planets); SectEngine (altitude and house fallback); SexResolver (explicit/infer, tie-break determinism, insufficient data → fail only); SexPolarityEngine (E formula); SexDelta32Engine (W32 v1, clamp). Invalid sex → fail-fast (type/message). sex_mode resolution order.
- **Integration**: Identity assembly with sex=male/female/None; base_vector includes sex_delta_32; same inputs → same step() output (determinism); symmetry sex_delta_32(male) ≈ -sex_delta_32(female) for same natal. Agent.step() output fields sex, sex_polarity_E.
- **Calibration**: Run script on fixed seed; assert thresholds (mean diff, p95, overlap); document how to run locally and in CI.

---

## Target Package Layout (008 additions)

```
hnh/
  agent.py              # extend: birth_data.sex/sex_mode, identity build with sex_delta_32
  identity/             # optional: identity_hash derivation for tie-break
  sex/                  # NEW: 008 components
    __init__.py
    sign_polarity.py    # SignPolarityEngine
    sect.py             # SectEngine (or under astrology if preferred)
    resolver.py         # SexResolver
    polarity.py         # SexPolarityEngine (E)
    delta_32.py         # SexDelta32Engine + W32_V1 constant
    # or profiles.py for W32_V1
  astrology/            # natal_chart, transits, houses — provide planet signs / Sun house or altitude to sex/
  state/
    behavioral_core.py  # no change: receives base_vector already including sex_delta_32
  ...
scripts/
  008/                  # optional: calibration script, demo
    calibration_sanity.py
    run_calibration.py
tests/
  unit/
    test_008_sign_polarity.py
    test_008_sect.py
    test_008_sex_resolver.py
    test_008_polarity.py
    test_008_delta_32.py
    test_008_agent_sex.py    # тесты уровня Agent: step() output (sex, sex_polarity_E), Agent с birth_data.sex, детерминизм
  integration/
    test_008_identity_sex.py
    test_008_calibration.py  # or under scripts/008 with pytest hook
```

If preferred, `hnh/sex/` can be named `hnh/sex_polarity/` to avoid ambiguity with the field name. SectEngine may live in `hnh/astrology/sect.py` if it fits better with houses/altitude.

---

## Risks & Mitigations

- **Regression for callers without sex**: When birth_data has no sex and sex_mode is explicit, E=0 and sex_delta_32=0 → base_vector unchanged from current behavior. Preserve this path and add tests.
- **Order of 32 params**: W32 and sex_delta_32 must match 002 axis/parameter order; add a contract test (e.g. axis names or indices vs schema) to avoid silent misalignment.
- **Infer and natal completeness**: Sect and sign_polarity need Sun sign (and optionally house/altitude). If natal does not provide them, infer path must fail (default) or return None per config; document minimal required natal fields.
- **Logging**: Ensure state_logger and any replay logs do not emit sex/birth_data in plain form by default; add checklist item or test that sensitive fields are not present unless audit mode enabled and documented.

---

## Out of Scope for 008

- Age (spec 009).
- Changing natal parsing or house system; use existing natal outputs.
- New UI or CLI flags beyond what is needed to pass sex/sex_mode and run calibration script.
