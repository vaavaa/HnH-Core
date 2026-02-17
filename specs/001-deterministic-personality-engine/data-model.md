# Data Model: 001 Deterministic Personality Engine

**Feature**: 001-deterministic-personality-engine  
**Date**: 2025-02-17  

---

## 1. Identity Core

| Field | Type | Constraints |
|-------|------|-------------|
| identity_id | string | Unique; at most one Core per id (spec). Creation with existing id → error. |
| base_behavior_vector | BehavioralVector | Exactly 7 dimensions, each [0.0, 1.0]; reject out-of-range. |
| symbolic_input | optional | e.g. birth_datetime (UTC), birth_location (lat, lon), natal_positions; maps to base_behavior_vector. |
| identity_hash | string | Stable, deterministic (e.g. hash of identity_id + base_behavior_vector + symbolic_input). |

**Invariants**: Immutable after creation; hashable; serializable; no runtime mutation.

---

## 2. Behavioral Vector (7 dimensions, fixed in v0.1)

| Dimension | Type | Range |
|-----------|------|-------|
| warmth | float | [0.0, 1.0] |
| strictness | float | [0.0, 1.0] |
| verbosity | float | [0.0, 1.0] |
| correction_rate | float | [0.0, 1.0] |
| humor_level | float | [0.0, 1.0] |
| challenge_intensity | float | [0.0, 1.0] |
| pacing | float | [0.0, 1.0] |

Reject any value outside [0, 1] at Identity creation and at Dynamic State input; no clamping. No NaN.

---

## 3. Dynamic State (output per step)

| Field | Type | Notes |
|-------|------|-------|
| identity_hash | string | From Identity Core. |
| timestamp | injected | No system clock in core. |
| transit_signature | optional | If astrology layer used. |
| relational_modifier | optional | From Relational Memory mapping. |
| final_behavior_vector | BehavioralVector | Modified by modifiers; still [0, 1]. |
| active_modifiers | list | For logging and replay. |

Must be replayable given: identity + time + relational memory snapshot.

---

## 4. Relational Memory (v0.1)

| Concept | Description |
|---------|-------------|
| user_id | string; one memory instance per user. |
| events | Ordered list. Each event: sequence index (step), type, payload (key-value or opaque). |
| Update rules | Deterministic; append-only or otherwise defined for replay. |
| Snapshot | Serializable; used as input to Dynamic State and replay. |

Derived metrics (e.g. interaction_count, error_rate_history, responsiveness_metric) may live in payload or derived structures; no mutation of Identity Core.

---

## 5. State Transition Log Record (minimal contract)

| Field | Required | Notes |
|-------|----------|-------|
| seed | yes | Injected seed for this step. |
| injected_time | yes | Injected timestamp. |
| identity_hash | yes | |
| active_modifiers | yes | List/serialized form. |
| final_behavioral_vector | yes | 7 dims. |

Extended (plan): transit_signature, relational_snapshot_hash, deterministic_seed — optional. One record per line (e.g. JSON Lines); diffable; replay-validatable.

---

## 6. Transit (optional, Planetary Agent)

Used only when astrology layer is enabled.

| Field | Type | Notes |
|-------|------|-------|
| timestamp | UTC, injected | |
| planetary_positions | | |
| aspects_to_natal | | |
| aspect_weights | | |

Deterministic: same time → same TransitSet.
