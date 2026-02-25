# Implementation Plan: 011 — Factorized Influence Stack (Mini-Rule) + Contribution Logging

**Branch**: `011-factorized-influence-stack` | **Date**: 2026-02-25 | **Spec**: [spec.md](spec.md)  
**Depends on**: 002 (32D, bounds), 006 (Agent.step), 009 (sex_transit_mode), 010 (age_delta_32).

---

## Summary

Ввести **протокол Factor** и **FactorStack** как единую точку оркестрации влияний в `Agent.step()`: каждый фактор — именованный producer или transform, выдающий/преобразующий Vector32. При `factor_stack_mode="off"` (по умолчанию) — legacy-путь без изменений (обратная совместимость). При `factor_stack_mode="on"` — сборка через стек с опциональным `delta_budget_mode` и структурированным `factor_breakdown` при `debug_factors=True`. Все новые ключи конфига входят в replay signature. Явные границы для baseline-diff тестов: `baseline_diff_max_abs_param` (0.08), `baseline_diff_max_abs_axis` (0.04).

---

## Technical Context

**Dependencies**: 002 (NUM_PARAMETERS, bounds, memory_delta), 006 (Agent, TransitEngine, step order), 009 (transit_delta_eff, scale_delta), 010 (age_delta_32, AgeEngine).  
**Integration**: FactorStack вызывается из `Agent.step()` после вычисления transit/age/memory deltas; оборачивает существующую математику, не заменяет её.  
**Config**: factor_stack_mode, debug_factors, delta_budget_mode, final_delta_cap, baseline_diff_max_abs_param, baseline_diff_max_abs_axis — все в replay signature.  
**Testing**: T-011-01..T-011-04 per spec; determinism, baseline-diff bounds, backward compatibility.

---

## Implementation Outline

1. **Protocols & types**: `Vector32`, `StepContext` (immutable), `Factor` protocol (name, kind, apply).
2. **FactorStack**: упорядоченный список факторов; run(ctx) → delta_total_32 + factor_breakdown (если debug).
3. **Concrete factors (v1)**: TransitDeltaFactor, SexTransitScaleFactor, AgeDeltaFactor, MemoryDeltaFactor, FinalBudgetCapFactor (optional).
4. **Agent.step()**: при factor_stack_mode=on — собирать StepContext, вызывать FactorStack, использовать delta_total_32 для params_final/axis_final; при off — legacy path unchanged.
5. **Config & hashes**: добавить ключи в ReplayConfig (или отдельный объект), включить в configuration_hash / factor_stack_hash.
6. **Tests**: T-011-01 (breakdown sums), T-011-02 (determinism), T-011-03 (baseline-diff bounds), T-011-04 (backward compat).

---

## Constitution Check (011)

- [ ] **Determinism**: Same inputs → same factor_breakdown and delta_total_32; no RNG in factors.
- [ ] **Single integration point**: All influences flow through FactorStack in Agent.step() when mode=on.
- [ ] **Backward compatibility**: factor_stack_mode=off → output identical to legacy (1e-9).
- [ ] **Replay signature**: New config keys in hash; factor list change updates factor_stack_hash or configuration_hash.
- [ ] **Explicit bounds**: baseline_diff_max_abs_param / baseline_diff_max_abs_axis with defaults 0.08 / 0.04.
