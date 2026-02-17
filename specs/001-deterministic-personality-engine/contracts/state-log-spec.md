# State Transition Log Contract

**Feature**: 001-deterministic-personality-engine  
**Spec reference**: spec.md § State Transition Log (Minimal Contract), FR-010  

---

## Format

- **Encoding**: Text; one record per state transition.
- **Line format**: One JSON object per line (JSON Lines). No pretty-print; one line = one record.

---

## Required Fields (minimal contract from spec)

| Field | Type | Description |
|-------|------|-------------|
| seed | (implementation-defined: int/str) | Injected seed for this step. |
| injected_time | (implementation-defined: ISO8601 or numeric) | Injected timestamp; no system clock. |
| identity_hash | string | Stable hash of Identity Core. |
| active_modifiers | array or serialized structure | List of active modifiers affecting this step. |
| final_behavioral_vector | object | Seven keys: warmth, strictness, verbosity, correction_rate, humor_level, challenge_intensity, pacing; values float [0.0, 1.0]. |

---

## Optional Fields (plan extension)

| Field | Type | Description |
|-------|------|-------------|
| transit_signature | string | If astrology layer used. |
| relational_snapshot_hash | string | Hash of relational memory snapshot. |
| deterministic_seed | (same as seed) | Explicit if needed for replay. |

---

## Behavioral Vector Schema (inline in log)

```json
{
  "warmth": 0.0,
  "strictness": 0.0,
  "verbosity": 0.0,
  "correction_rate": 0.0,
  "humor_level": 0.0,
  "challenge_intensity": 0.0,
  "pacing": 0.0
}
```

All values MUST be in [0.0, 1.0]. Out-of-range MUST be rejected at source (no clamping in log).

---

## Replay & Diff

- Log MUST be diffable (e.g. line-by-line comparison).
- Replay MUST consume the same fields to reproduce state; implementation MAY add optional fields that are ignored when not present.
