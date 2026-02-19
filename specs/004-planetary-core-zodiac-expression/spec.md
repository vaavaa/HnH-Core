# Feature Specification: Planetary Core + Zodiac Expression Layer

**Feature Branch**: `004-planetary-core-zodiac-expression`  
**Created**: 2025-02-19  
**Status**: Draft  
**Input**: Extend HnH with a Zodiac Expression Layer derived from the 10-planet planetary model. Interpretation/marketing only; no change to behavioral physics.

---

## Clarifications

### Session 2025-02-19

- Q: Дефолтная система домов — фиксировать в спеке или только в плане? → A: Зафиксировать в спеке дефолт: Placidus; остальные системы — опция конфига.
- Q: Как вычисляются dominant_sign и dominant_element? → A: dominant_sign — знак с максимальным intensity; dominant_element — элемент (Fire/Earth/Air/Water) с максимальной суммой intensity по своим трём знакам.
- Q: Знак без планет — как считать Z[sign]? → A: Допускается только вклад правителя и аспектов к нему; если и его нет — вектор (0,0,0,0). Зафиксировать в спеке.
- Q: Фиксировать ли в спеке привязку входов к четырём измерениям Z? → A: В спеке зафиксировать привязку входов к измерениям (без весов); веса и формулы — в плане/контракте.
- Q: От чего считается angular strength — только дом или ещё ASC/MC? → A: Только от положения в доме (дома 1,4,7,10 = угловые; шкала в плане). ASC/MC не входят в определение в 004.

---

## 1. Objective

Extend HnH architecture with a **Zodiac Expression Layer** derived from the 10-planet planetary model.

This layer must:

- Be fully derived from planetary positions and aspects
- Not replace the 32 behavioral parameter model
- Serve as interpretative / marketing projection
- Remain deterministic
- Not alter core behavioral physics
- Be compatible with Lifecycle & Entropy (Research Mode)

---

## 2. Planetary Primacy Rule

HnH calculations MUST follow this hierarchy:

1. **10 Planets** (primary physical model)
2. Aspects & Transits
3. Energetic Aggregation
4. **32 Behavioral Parameters**
5. Lifecycle (optional, Research Mode)
6. **Zodiac Expression Layer** (interpretation only)

Zodiac layer MUST NOT directly influence behavioral computation.

---

## 3. Primary Planetary Model (10 Planets) & Houses

**Scope of 004**: This specification includes (1) **extension of the ephemeris to 10 planets** and (2) **introduction of house calculation**. Both are part of the 004 deliverable; natal and transit pipelines MUST use the extended model.

### 3.1 Ten Planets

The system uses:

- Sun, Moon, Mercury, Venus, Mars  
- Jupiter, Saturn  
- Uranus, Neptune, Pluto  

The ephemeris layer MUST compute positions for all 10 planets (natal and transits). Deterministic; same JD + location → same positions.

### 3.2 Houses

Each planet MUST have a **house position** (1–12). House calculation is **in scope** for 004: the engine MUST compute house cusps from birth (or event) time and location, and assign each planet to a house. The **default** house system is **Placidus**; other systems (e.g. Equal, Whole Sign) MAY be selectable via configuration. Angular strength MAY be derived from house position (e.g. angular houses 1, 4, 7, 10).

### 3.3 Per-Planet Outputs

Each planet provides:

- Sign position (0–11 or equivalent)
- House position (1–12)
- Aspect structure
- Orb strength
- **Angular strength** — derived from house position only: angular houses (1, 4, 7, 10) are stronger; the exact scale is defined in the implementation plan. ASC/MC are not used in 004.
- Aspect tension score

All planetary calculations MUST be deterministic.

---

## 4. Zodiac Expression Layer

### 4.1 Definition

For each of the 12 zodiac signs:

Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra,  
Scorpio, Sagittarius, Capricorn, Aquarius, Pisces  

the engine computes a **4-dimensional expression vector**:

```
Z[sign] = {
  intensity,
  stability,
  expressiveness,
  adaptability
}
```

Total: **12 × 4 = 48** derived components.

---

### 4.2 Computation Rules

Zodiac expression MUST be derived from:

- Number of planets in sign
- Strength of sign ruler (sign → ruler planet defined in [contract: sign-rulers](contracts/sign-rulers.md))
- Aspects to planets in that sign
- Angular weighting
- Tension vs harmony balance

**Input-to-dimension mapping** (MUST be defined in the implementation contract; weights and exact formulas are in plan/contract):

| Dimension      | Inputs that MAY contribute (minimal binding) |
|----------------|-----------------------------------------------|
| intensity      | planetary_presence, hard_aspects_weight      |
| stability      | ruler_strength, tension_vs_harmony balance   |
| expressiveness | planetary_presence, angular_weighting        |
| adaptability   | tension_vs_harmony balance                    |

Each dimension MUST be normalized to **[0, 1]**.

**Sign with no planets:** Z[sign] MAY receive contribution from the sign ruler and aspects to that ruler only; if there is no such contribution, Z[sign] = (0, 0, 0, 0). This case MUST be defined so that tests and replay are deterministic.

---

## 5. Relationship to 32 Behavioral Parameters

The Zodiac Expression Layer DOES NOT replace the 32 behavioral parameter model.

**Default behavior:**

- Zodiac output is read-only interpretative data.
- It MUST NOT influence behavioral computation.

**Optional future work (NOT part of this specification):**

- A deterministic projection may map `Z_48 → behavior_32` via either:
  - a fixed aggregation scheme (by signs/elements/axes), or
  - a projection matrix `P` with shape (32 × 48)

This projection is explicitly deferred to a future specification and MUST NOT be implemented as part of 004.

---

## 6. Marketing & Interface Use

The Zodiac Expression Layer may be used to:

- Display dominant sign energies
- Generate zodiac-based summaries
- Show “current dominant element”
- Visualize planetary emphasis
- Communicate personality in zodiac language

This layer MUST NOT alter deterministic behavior.

---

## 7. Lifecycle Compatibility

In Research Mode:

- Fatigue MAY indirectly affect Zodiac output via reduced planetary modulation.
- Zodiac values remain derived from current planetary state.
- Death, Rebirth, Transcendence do NOT depend on zodiac layer.

Zodiac is narrative, not ontological.

---

## 8. Determinism Requirements

Given identical:

- birth data
- time input
- transit input
- configuration  

Zodiac Expression output MUST be identical.

No stochastic elements allowed.

---

## 9. Logging Additions & Zodiac Hash

Lifecycle logs MAY include:

- `dominant_sign` — the sign with **maximum intensity** (among the 4 dimensions of Z[sign]).
- `dominant_element` — the element (Fire, Earth, Air, Water) whose **sum of intensity** over its three signs is greatest (e.g. Fire = Aries + Leo + Sagittarius).
- `sign_energy_vector` (12×4)
- `zodiac_summary_hash`

Serialization MUST use **orjson** (per Spec 003).

### 9.1 Computation of zodiac_summary_hash

For replay consistency and tests, the engine MUST compute **zodiac_summary_hash** whenever zodiac output is produced:

- **Input**: the full zodiac expression output used for the step — at minimum the **sign_energy_vector** (12×4, all values in [0, 1]). The exact structure (e.g. flattened 48 floats, or canonical dict) MUST be fixed in the implementation contract so the hash is deterministic.
- **Algorithm**: **xxhash** (xxh3_128 or xxh64), per Spec 003. No other hash function is allowed in core.
- **Determinism**: Same sign_energy_vector (and any other included fields) MUST yield the same zodiac_summary_hash. Serialization before hashing MUST be deterministic (e.g. orjson with OPT_SORT_KEYS).
- **Replay**: When zodiac layer is logged, **zodiac_summary_hash** MUST be included in the log record. Replay signature MAY include zodiac_summary_hash so that “consistency across replay” is verifiable: identical inputs MUST produce the same zodiac_summary_hash on re-run.

Implementations MUST document the exact bytes used as hash input (e.g. orjson.dumps(sign_energy_vector, option=orjson.OPT_SORT_KEYS)).

---

## 10. Performance Constraints

- Zodiac layer computation must be **O(1) per day** (no per-step blow-up).
- No repeated recalculation of natal constants.
- Use cached planetary strengths where possible.

---

## 11. Test Requirements

Coverage target: **99%** for zodiac computation modules.

Must test:

- Deterministic sign vector computation
- Correct ruler influence
- Normalization bounds [0, 1]
- Independence from behavioral state mutation
- **Consistency across replay**: For identical inputs (birth data, time, transit, config), multiple runs MUST produce the same zodiac output. Tests MUST compare **zodiac_summary_hash** (or the full sign_energy_vector 12×4) between runs; equality is required. The hash MUST be included in the logged payload when zodiac is enabled so that replay and tests can assert identity without storing the full 12×4 vector.

---

## 12. Acceptance Criteria

Feature complete when:

- **Ephemeris extended to 10 planets** (Uranus, Neptune, Pluto); natal and transits use them.
- **Houses computed** for birth/event; each planet has house position 1–12; house system documented.
- 12 zodiac sign vectors computed deterministically
- Each sign has 4 normalized dimensions
- No behavioral feedback loop from zodiac layer
- Logs include optional zodiac output; when included, **zodiac_summary_hash** is computed (xxhash from sign_energy_vector) and written for replay consistency
- Replay and tests verify consistency by comparing zodiac_summary_hash (or 12×4) between runs
- Research and Product modes both compatible
- 99% coverage maintained for zodiac modules

---

## 13. References

- Spec 001: Deterministic engine, state logging, replay.
- Spec 002: 32 parameters, natal sensitivity, transits, orjson logging.
- Spec 003: orjson, xxhash, loop optimization; no stdlib json in core.
- **Contract**: [004 — Sign Rulers](contracts/sign-rulers.md): sign index 0–11 → ruler planet; Classical vs Modern; default Modern.
- Project: `hnh/core/natal.py`, `hnh/astrology/ephemeris.py`, `hnh/astrology/aspects.py`, `hnh/modulation/delta.py`, `hnh/identity/sensitivity.py`.
