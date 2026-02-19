# Quickstart: 005 — Lifecycle & Entropy (Research Mode)

Minimal path to run lifecycle (after 005 is implemented).

## Prerequisites

- **Mode**: `mode = "research"` and `lifecycle_enabled = true` in config.
- **Inputs**: Natal data, transit data (for S_T), Identity (base, sensitivity for R and S_g), initial F=0, W=0 (or configurable).

## Steps

1. **Config**  
   Set replay (or lifecycle) config: `mode="research"`, `lifecycle_enabled=true`. All lifecycle constants may use spec defaults or overrides.

2. **Per-day pipeline**  
   For each time step (day):
   - Compute transit stress S_T(t) from aspects (I_T / C_T, clip to [0,1]).
   - Get R from Stability axis, S_g from mean(sensitivity).
   - Run fatigue update: load(t), recovery(t), F(t+1), L, q(t).
   - Compute A_g(t) = clip(1 - q^rho, 0, 1).
   - Apply activity suppression to transit_delta and memory_delta.
   - Optionally apply behavioral degradation to activity-sensitive params.
   - Optional: compute Age_psy(t) for log.

3. **Death**  
   If F(t) >= L: set state = DISABLED; freeze params; stop updates; compute delta_W from lifetime v/burn; update W; log final snapshot.

4. **Transcendence**  
   If W >= 0.995: set state = TRANSCENDED; disable fatigue and further modulation; freeze personality.

## Verification

- Same natal, transit, config, initial W → same F(t), W(t), state over time.
- Product Mode or lifecycle_enabled=false → no F, W, death, transcendence; behavior as 002 only.

## References

- Spec: [spec.md](spec.md)  
- Plan: [plan.md](plan.md)  
- Data model: [data-model.md](data-model.md)
