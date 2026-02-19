# Data Model: 004 — Planetary Core + Zodiac Expression Layer

Entities and structures introduced or extended by 004.

## 1. Planetary position (extended)

**Source**: `hnh/astrology/ephemeris.py`, natal/transits.

| Field | Type | Notes |
|-------|------|--------|
| planet | string | One of 10: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto |
| longitude | float | Ecliptic longitude [0, 360) |
| sign | int | 0–11 (derived: longitude / 30) |
| house | int | 1–12 (from house cusps; default system Placidus) |
| angular_strength | float | From house only; scale in [0, 1]: Angular (1,4,7,10)=1.0, Succedent (2,5,8,11)=0.6, Cadent (3,6,9,12)=0.3 — see [contracts/angular-strength.md](contracts/angular-strength.md) |

Orb strength, aspect tension: existing (aspects module).

## 2. House cusps

| Field | Type | Notes |
|-------|------|--------|
| cusps | tuple[float, ...] | 12 cusp longitudes (order 1..12) |
| ascendant | float | ASC longitude (if exposed) |
| mc | float | MC longitude (if exposed) |
| system | string | "P" (Placidus) default; configurable |

## 3. Zodiac expression (12×4)

**Output of Zodiac Expression Layer.**

| Field | Type | Notes |
|-------|------|--------|
| sign_energy_vector | list or tuple of 12 × (intensity, stability, expressiveness, adaptability) | All values in [0, 1]; order by sign index 0..11 |
| dominant_sign | int or string | Sign index or name with max intensity |
| dominant_element | string | "Fire" | "Earth" | "Air" | "Water" (element with max sum of intensity over its 3 signs) |
| zodiac_summary_hash | string | xxhash of canonical serialization of sign_energy_vector (e.g. orjson OPT_SORT_KEYS) |

## 4. Sign rulers

See [contracts/sign-rulers.md](contracts/sign-rulers.md): sign index 0..11 → ruler planet name (Modern default).

## 5. Log payload (optional fields)

When zodiac is logged: dominant_sign, dominant_element, sign_energy_vector, zodiac_summary_hash. Serialization: orjson. Hash input: deterministic (spec §9.1).
