# Data model (008 — Sex Polarity & 32D Shifts)

This document defines the data fields and sources used by spec 008. It extends or references the identity/birth_data notions from 006; exact integration with 006’s plan/data-model is implementation-defined.

---

## Input principle: sex is supplied from outside

The system receives **birth data** (date, time, place, etc.) and **sex of the person** as inputs. Sex is **not derived** inside the engine; it is passed in by the caller. So: **date of birth + sex of the person** are the relevant external inputs for identity. Inference (infer mode) is only an optional fallback when the caller does not provide sex (e.g. synthetic populations).

---

## birth_data (008-relevant fields)

| Field        | Type                     | Required | Description |
|-------------|---------------------------|----------|-------------|
| `sex`       | `"male" \| "female" \| None` | No       | **External input**: sex of the person, supplied with birth data. When provided, used as-is (explicit). When absent, behavior depends on `sex_mode` (baseline or infer). |
| `sex_mode`  | `"explicit" \| "infer"`   | No       | Default `"explicit"`. If `sex_mode` is not on `birth_data`, it MAY be taken from agent/replay config; the implementation MUST document the resolution order. |

**Priority when sex is provided in multiple places**: If both `birth_data.sex` and another source (e.g. agent config) specify sex, **`birth_data.sex` MUST take precedence**. The implementation MUST document the full resolution order (e.g. birth_data.sex > agent_config.sex > default None).

Other birth_data fields (date, time, place, positions, etc.) follow 006 / existing natal contracts.

---

## identity_hash (source for tie-break and determinism)

- **Purpose**: Deterministic tie-break in infer mode (FR-015) and reproducible step output. Same agent ⇒ same `identity_hash` ⇒ same inferred sex when S in [-T,+T].
- **Source**: MUST be a value that is part of identity and stable for the same agent across runs. Permissible sources (implementation chooses one and documents it):
  - A digest of `birth_data` (e.g. canonical JSON or sorted key-value hash).
  - A field on `identity_config` (e.g. `identity_config.identity_hash`) set when building identity from birth_data.
  - A dedicated identifier provided at Agent construction and stored in identity.
- **Type**: Implementation-defined (bytes, int, or string). Tie-break uses a deterministic function of this value (e.g. `male` if `hash_deterministic(identity_hash) % 2 == 1` else `female`). The hash function MUST be deterministic across process runs (e.g. SHA-256 then low bit), not Python’s built-in `hash()`.

---

## Infer mode: insufficient natal data

- **Config**: **`infer_on_insufficient_data`** (or equivalent name): `"fail"` | `"none"`. Default MUST be documented (recommended: `"fail"`). When `"fail"`, the system MUST raise a clear error if polarity score cannot be computed. When `"none"`, the system MUST set `sex=None` and E=0, and MAY set `sex_inference_skipped: true` in output.
- **Minimal required for inference**: At least **Sun** MUST have a known sign. Implementations MAY require additional planets (e.g. Moon) and MUST document the minimal set. If that set is not available and `infer_on_insufficient_data="none"`, output is `sex=None`; if `"fail"`, error.

---

## Pipeline summary

- **Identity assembly**: `birth_data` (+ config) → resolve `sex` (from `birth_data.sex` or infer) → compute E and `sex_delta_32` → add `sex_delta_32` into the 32D base used by BehavioralCore. This is the identity-level state; **sex_delta_32 is applied before any transit**.
- **Step(date)**: Uses that base (already including sex shift); transit delta is applied on top per 006.

See [spec.md](spec.md) § Integration with 006.
