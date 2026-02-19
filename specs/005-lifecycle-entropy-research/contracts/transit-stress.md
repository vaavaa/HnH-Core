# Contract: Transit Stress (I_T, S_T) for Lifecycle 005

**Scope**: Definition of raw transit intensity I_T(t) and normalization to S_T(t) for the Lifecycle & Entropy layer. Deterministic; same aspects → same I_T, S_T.

---

## 1. Hard aspects (stress-contributing)

Only **hard aspects** contribute to I_T(t):

| Aspect      | Angle  | Included in I_T |
|-------------|--------|-----------------|
| Conjunction | 0°     | Yes             |
| Opposition  | 180°   | Yes             |
| Square      | 90°    | Yes             |
| Trine       | 120°   | No (soft)       |
| Sextile     | 60°    | No (soft)       |

**Canonical set**: `HARD_ASPECTS = { "Conjunction", "Opposition", "Square" }`. Any aspect not in this set MUST NOT be summed in I_T. Implementation MAY align with `hnh/astrology/zodiac_expression.HARD_ASPECTS` or define the same set in the lifecycle module.

---

## 2. Per-aspect weight (hard_aspect_weight)

Fixed weight per hard aspect type (stress magnitude, independent of orb):

| Aspect      | hard_aspect_weight (default) |
|-------------|------------------------------|
| Conjunction | 1.0                          |
| Opposition  | 1.0                          |
| Square      | 1.0                          |

All hard aspects contribute equally by type. Config MAY allow per-aspect overrides; if so, replay-relevant and MUST be part of configuration_hash when lifecycle enabled.

---

## 3. Orb decay (orb_decay)

**Definition**: intensity of the aspect as a function of how exact it is. Exact = 1.0; at orb edge = 0.0.

**Formula** (linear falloff):

```
dev = distance from exact angle (degrees)
orb = allowed orb for that aspect (degrees; from OrbConfig or config)
orb_decay = max(0, 1 - dev / orb)   if orb > 0
            1.0                      if orb <= 0
```

- **Conjunction**: dev = min(separation, 360 - separation); orb from config (e.g. 8°).
- **Opposition, Square, Trine, Sextile**: dev = |separation - angle|; orb per aspect from config.

Separation is the angular separation of the two bodies; angle is the nominal aspect angle (0, 180, 90, 120, 60). Implementation MAY reuse the same logic as `hnh/modulation/delta._intensity_factor` (which uses `1 - dev/orb`) so that orb_decay is consistent with existing intensity_factor for transits.

---

## 4. Raw intensity and normalization

```
I_T(t) = Σ (hard_aspect_weight × orb_decay)
```

Sum over all transit–natal aspects that are in HARD_ASPECTS. Each term is weight × orb_decay for that aspect.

```
S_T(t) = clip(I_T(t) / C_T, 0, 1)
```

**Default** `C_T = 3.0`. Calibration target: 95th percentile of S_T over a large set of daily transit snapshots should remain < 0.9. If validation fails, adjust C_T or per-aspect weights in config (replay-relevant).

---

## 5. Replay and determinism

- The list of aspects and their separation/angle MUST come from the same transit pipeline as Spec 002/004 (e.g. `compute_transit_signature` → aspects_to_natal).
- Orb values used for orb_decay MUST be from config (OrbConfig or equivalent); if config is fixed, same transit data → same I_T, S_T.
- configuration_hash when lifecycle enabled MUST include any constants used for I_T/S_T (C_T, hard_aspect_weights, orb source) so that replay is deterministic.
