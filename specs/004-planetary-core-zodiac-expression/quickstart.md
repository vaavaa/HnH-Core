# Quickstart: 004 — Zodiac Expression Layer

Minimal path to compute zodiac output (after 004 is implemented).

## Prerequisites

- Birth data: datetime (UTC), latitude, longitude.
- Injected time (for transits) and config (or defaults).
- Optional: natal_positions and transit_signature from 002 pipeline.

## Steps

1. **Natal (10 planets + houses)**  
   Call natal pipeline with birth data and location. Output must include positions for all 10 planets and house (1–12) per planet. Default house system: Placidus.

2. **Transits (optional)**  
   For a given injected time, compute transit positions (10 planets). Houses for transits may use same JD + location if “event” chart is desired.

3. **Zodiac expression**  
   Input: natal (and optionally transit) positions + aspects. Output: `sign_energy_vector` (12×4), `dominant_sign`, `dominant_element`. Normalization: all dimensions in [0, 1].

4. **Hash (for replay)**  
   Compute `zodiac_summary_hash` from `sign_energy_vector` (orjson + xxhash per spec §9.1). Include in log if zodiac is logged.

## Verification

- Same inputs → same sign_energy_vector and zodiac_summary_hash.
- Zodiac output is not fed back into 32 behavioral parameters.

## References

- Spec: [spec.md](spec.md)  
- Contract sign rulers: [contracts/sign-rulers.md](contracts/sign-rulers.md)  
- Plan: [plan.md](plan.md)
