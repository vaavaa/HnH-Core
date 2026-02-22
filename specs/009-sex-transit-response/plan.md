# Implementation Plan: 009 — Sex Affects Transit Response (Dynamic Modulation)

**Branch**: `009-sex-transit-response` | **Date**: 2026-02-22 | **Spec**: [spec.md](spec.md)  
**Depends on**: 008 (E, W32, identity base_vector with sex_delta_32).

---

## Summary

Add optional **sex-based modulation of transit response**: config `sex_transit_mode ∈ {'off', 'scale_delta', 'scale_sensitivity'}` (default `off`). When `scale_delta`, compute per-parameter multipliers `M[i] = clamp(1 + beta*E*Wdyn[i], 1-mcap, 1+mcap)` and apply `transit_delta_eff[i] = bounded_delta[i] * M[i]` before state assembly, so that `d_*` differ between male and female for the same natal/date range. Bounded, deterministic, no RNG. Implement `scale_delta` first; observability (multiplier_stats) opt-in.

---

## Technical Context

- **Integration point**: Between `TransitState.bounded_delta` and `assemble_state` (or inside `BehavioralCore.apply_transits`): compute M from E (identity_config), scale bounded_delta, then pass scaled delta into existing assembly. No change to TransitEngine contract.
- **Config**: ReplayConfig or Agent config: `sex_transit_mode`, `beta`, `mcap`, `sex_transit_Wdyn_profile`; defaults 0.05, 0.10, "v1" (Wdyn = W32_v1).
- **Tests**: Determinism; with mode=scale_delta, same natal/date range → different d_* for male vs female; with mode=off, d_* identical; multiplier bounds; calibration script for SC-004.

---

## Constitution Check

- [ ] Determinism: same inputs → same outputs; M[i] deterministic from E and Wdyn.
- [ ] Identity unchanged: 008 base_vector and E remain as-is; modulation only affects transit path.
- [ ] Default off: no silent behavior change.
- [ ] Logging: multiplier_stats and E only in opt-in debug; no plain sex/birth_data by default (per 008).

---

## Phases (outline)

1. **Config & modulator**: Add `sex_transit_mode`, `beta`, `mcap`, Wdyn profile (v1 = W32); `SexTransitModulator` computing M and scaled delta.
2. **Integration**: In BehavioralCore or caller, when mode=scale_delta and E available, use modulator output as bounded_delta input to assemble_state; preserve pipeline order and clamp01.
3. **Observability**: Extend step result (or debug payload) with multiplier_stats when debug enabled; keep default output minimal.
4. **Tests & calibration**: Unit tests for M bounds and symmetry; integration test male vs female d_* with scale_delta; calibration script and SC-004 thresholds (configurable).
