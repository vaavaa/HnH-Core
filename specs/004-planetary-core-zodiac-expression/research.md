# Research: 004 — Planetary Core + Zodiac Expression Layer

**Phase 0**: No open NEEDS CLARIFICATION in Technical Context; all decisions captured in spec (Clarifications Session 2025-02-19) and plan.

## Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Default house system | Placidus | Spec fix for determinism and replay; widely supported (pyswisseph); other systems via config. |
| dominant_sign / dominant_element | Max intensity; element = max sum intensity over 3 signs | Unambiguous, testable; defined in spec §9. |
| Sign with no planets | Z[sign] = ruler + aspects to ruler only; else (0,0,0,0) | Deterministic edge case; spec §4.2. |
| Input–dimension mapping | Spec table (which inputs feed which dimension); weights in plan/contract | Testability without over-constraining formulas. |
| Angular strength | House position only (1,4,7,10 = angular); ASC/MC not in 004 | Simplifies contract; scale in plan. |

## Alternatives Considered

- **Equal House** as default: simpler (no latitude for cusps) but less common; Placidus chosen for alignment with common practice.
- **ASC/MC** for angular strength: deferred to keep 004 scope bounded; can be added later.
