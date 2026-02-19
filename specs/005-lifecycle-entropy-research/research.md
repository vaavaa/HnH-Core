# Research: 005 — Lifecycle & Entropy Model (Research Mode Only)

**Phase 0**: Initial capture; no open NEEDS CLARIFICATION yet. Decisions below align with spec.

## Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Mode gating | Lifecycle only when mode=research and lifecycle_enabled=true | Product Mode must be unaffected; explicit flag for research features. |
| Time step | 1 day | Aligns with existing replay step; O(1) per day. |
| Death rarity | L scaled by R and S_g; lambda_up/lambda_down tuned so median lifespan > 800y | Design constraint: death rare under normal conditions. |
| Will update | Only at death; delta_W clamped [-0.03, +0.02] | Growth slow and rare; no daily W accumulation. |
| Transcendence | W >= 0.995; < 1% in 10k agents | Extremely rare; exceptional natal/config only. |
| Activity suppression | A_g = 1 - q^rho, rho=2.5; effective_delta = A_g × raw_delta | Smooth scaling; minimal when q<0.4, strong when q>0.8. |
| Behavioral degradation | Fixed set of 6 params; cap 0.1 absolute reduction | Spec §7.2; avoid over-dampening. |
| Running averages | Use O(1) running sum/count for mean(v), mean(burn) over lifetime | Performance constraint; no full history scan. |

## Alternatives Considered

- **Daily will update**: Rejected; would make W growth too frequent. Will only at death keeps transcendence rare.
- **Fatigue from memory/relational**: Spec keeps fatigue driven by transit stress + R + S_g; memory/relational affect behavior via existing 002 pipeline; optional extension deferred.
- **Rebirth**: Not in current spec; state DISABLED is terminal unless a future spec adds rebirth logic.

## Open Points (if any)

- ~~Exact orb_decay formula for I_T(t)~~ → Fixed in [contracts/transit-stress.md](contracts/transit-stress.md): linear orb_decay = max(0, 1 − dev/orb); hard aspects = Conjunction, Opposition, Square.
- Whether Psychological age is exposed in API or log-only: spec leaves it optional in log; API exposure is implementation-defined.
