# Contract: 004 — Angular Strength (House-Based)

**Scope**: Spec 004, §3.3. Angular strength is derived **from house position only**. Houses 1, 4, 7, 10 = angular; ASC/MC are not used in 004.

---

## 1. House categories

| Category   | Houses    | Description        |
|-----------|-----------|--------------------|
| Angular   | 1, 4, 7, 10 | Strongest; cardinal cusps |
| Succedent | 2, 5, 8, 11 | Medium             |
| Cadent    | 3, 6, 9, 12 | Weakest            |

---

## 2. Scale (deterministic)

**Output**: `angular_strength` per planet is a float in **[0.0, 1.0]**.

| House (1–12) | angular_strength |
|--------------|-------------------|
| 1, 4, 7, 10  | **1.0**           |
| 2, 5, 8, 11  | **0.6**           |
| 3, 6, 9, 12  | **0.3**           |

Implementation MUST use this mapping so that replay and tests are deterministic. No other factors (e.g. ASC/MC aspects) affect angular_strength in 004.

---

## 3. Data contract (implementation)

- **Input**: house number (int, 1–12) for the planet.
- **Output**: float in [0.0, 1.0] as above.

Example constant (Python):

```python
# House 1..12 → angular strength [0, 1]
ANGULAR_STRENGTH_BY_HOUSE: tuple[float, ...] = (
    1.0, 0.6, 0.3, 1.0, 0.6, 0.3, 1.0, 0.6, 0.3, 1.0, 0.6, 0.3,
)
# Index 0 = house 1, index 11 = house 12
```

---

## 4. References

- Spec 004: §3.2, §3.3 (angular strength from house only; ASC/MC not in 004).
- Data model: [data-model.md](../data-model.md) — field `angular_strength`.
