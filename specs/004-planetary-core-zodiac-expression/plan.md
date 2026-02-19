# Implementation Plan: 004 — Planetary Core + Zodiac Expression Layer

**Branch**: `004-planetary-core-zodiac-expression` | **Date**: 2025-02-19 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/004-planetary-core-zodiac-expression/spec.md` (post-clarify).

---

## Summary

Extend HnH with (1) **10-planet ephemeris** (Uranus, Neptune, Pluto) and **house calculation** (default Placidus), and (2) a **Zodiac Expression Layer**: 12 signs × 4 dimensions (intensity, stability, expressiveness, adaptability), derived from planets, aspects, rulers, angular strength; read-only, deterministic, no impact on 32 behavioral parameters. Logging may include dominant_sign, dominant_element, sign_energy_vector, zodiac_summary_hash (xxhash). Implementation follows existing Python/pyswisseph stack; formulas and weights in plan/contracts.

---

## Technical Context

**Language/Version**: Python 3.12 (existing HnH stack)  
**Primary Dependencies**: pyswisseph (ephemeris + houses), orjson, xxhash (Spec 003)  
**Storage**: N/A (in-memory; logging to structured orjson)  
**Testing**: pytest; 99% coverage target for zodiac modules  
**Target Platform**: Same as 002/003 (CLI, scripts, replay)  
**Project Type**: Single package (`hnh/`)  
**Performance Goals**: Zodiac layer O(1) per day (one zodiac computation per injected day; no per-step blow-up); no repeated natal recalculation; cached planetary strengths  
**Constraints**: Deterministic; no stochastic elements; zodiac MUST NOT influence behavioral computation  
**Scale/Scope**: 10 planets, 12×4 = 48 zodiac components, optional log fields

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify against `.specify/memory/constitution.md` (HnH Constitution):

- [x] **Deterministic Mode**: Zodiac output deterministic; time/seed injected; zodiac_summary_hash in log for replay; no non-deterministic code.
- [x] **Identity/Core separation**: Zodiac layer does not mutate Identity Core or Dynamic State; read-only interpretative output.
- [x] **Minimal Reference Implementation**: No LLM/external APIs for 004; structured logging (orjson); replay consistency via zodiac_summary_hash.
- [x] **Behavioral Parameterization**: Zodiac is narrative only; 32 parameters remain the measurable layer; no symbolic-only behavior in core.
- [x] **Logging & Observability**: Optional zodiac fields (dominant_sign, dominant_element, sign_energy_vector, zodiac_summary_hash); observability preserved.
- [x] **Repository Standards**: Python, orjson, xxhash, pytest; contracts (sign-rulers) documented; tests required.

No violations. Zodiac is additive (interpretation only) and does not alter existing constitution compliance.

---

## Project Structure

### Documentation (this feature)

```text
specs/004-planetary-core-zodiac-expression/
├── plan.md              # This file
├── research.md          # Phase 0 (if needed)
├── data-model.md        # Phase 1 (entities: positions, houses, Z 12×4)
├── quickstart.md        # Phase 1 (how to run zodiac pipeline)
├── contracts/
│   └── sign-rulers.md   # Sign index 0–11 → ruler; Classical/Modern
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

Existing `hnh/` layout; 004 adds or extends:

```text
hnh/
├── astrology/
│   ├── ephemeris.py     # Extend to 10 planets; add houses (Placidus default)
│   ├── zodiac_expression.py  # Zodiac layer 12×4, dominant_*, read-only
│   └── ...
├── core/
│   ├── natal.py         # Use 10 planets + house per planet
│   └── ...
```

No new top-level projects. All under `hnh/`.

**Structure Decision**: Single package; zodiac module at `hnh/astrology/zodiac_expression.py`.

---

## Dependencies (current codebase)

- **10 planets**: Спека 004: расширение эфемерид до 10 планет входит в объём. В `hnh/astrology/ephemeris.py` сейчас 7 планет (Sun–Saturn); добавить Uranus, Neptune, Pluto; natal и транзиты используют все 10.
- **Дома**: Спека 004: расчёт домов входит в объём. **Дефолт системы домов: Placidus** (зафиксировано в спеке); остальные системы — опция конфига. Каждая планета — house position 1–12; куспиды от JD + lat/lon. **Angular strength** — только от положения в доме (дома 1, 4, 7, 10 = угловые); шкала зафиксирована в [contracts/angular-strength.md](contracts/angular-strength.md); ASC/MC в 004 не используются.
- **Правители знаков**: Контракт [contracts/sign-rulers.md](contracts/sign-rulers.md): sign index 0–11, Classical (7) / Modern (10); по умолчанию Modern.
- **Clarify (Session 2025-02-19)**: dominant_sign = знак с макс. intensity; dominant_element = элемент с макс. суммой intensity по 3 знакам; знак без планет — только вклад правителя/аспектов к нему, иначе (0,0,0,0); привязка входов к 4 измерениям — в спеке (таблица), веса — в плане/контракте.

---

## Logic Review

### Сильные стороны

- Чёткое разделение: 32 параметра — механика; зодиак — интерпретация. Иерархия планет → аспекты → 32 params → zodiac (read-only).
- Детерминизм и совместимость с 001–003; orjson, xxhash, O(1) per day.
- Lifecycle: смерть/перерождение не зависят от зодиака; усталость — только через существующую планетарную модуляцию.

### Что закрыто clarify

- Четыре измерения: привязка входов к intensity/stability/expressiveness/adaptability в спеке (§4.2); веса и формулы — в плане/контракте.
- dominant_sign / dominant_element: правила зафиксированы в спеке (§9).
- Пустой знак, angular strength, дефолт домов — в спеке.

### Риски

- Объём: 10 планет + дома + Z 12×4 + логи + тесты. Разбить на фазы в tasks (например фаза 1: эфемериды + дома; фаза 2: Z, логи, тесты).
- Replay: zodiac_summary_hash в логе и в тестах сравнение между прогонами — зафиксировано в спеке.

---

## Implementation Outline (for tasks)

1. **Ephemeris**: 10 планет (Uranus, Neptune, Pluto); один список; обновить natal/transits.
2. **Houses**: Расчёт куспидов (JD, lat, lon); **дефолт Placidus**; конфиг для других систем. Для каждой планеты: sign 0..11 из longitude; house 1..12 из куспидов. **Angular strength**: только по дому; шкала в [contracts/angular-strength.md](contracts/angular-strength.md) (Angular=1.0, Succedent=0.6, Cadent=0.3).
3. **Rulers**: Константа SIGN_RULER (Modern default) из [contracts/sign-rulers.md](contracts/sign-rulers.md); strength of ruler из позиции и аспектов планеты-правителя.
4. **Z computation**: Модуль zodiac expression: вход — позиции (знак, дом), аспекты, правители, angular strength; выход — 12×4 в [0,1]. Привязка входов к измерениям по спеке §4.2; веса в контракте. Знак без планет: только правитель/аспекты к нему; иначе (0,0,0,0). Без обращения к params_final/base.
5. **dominant_sign / dominant_element**: По спеке §9 (max intensity; element = max sum of intensity over 3 signs).
6. **Logging**: Опциональные поля dominant_sign, dominant_element, sign_energy_vector, zodiac_summary_hash (orjson; xxhash от sign_energy_vector по §9.1).
7. **Tests**: 99% по модулю зодиака; детерминизм; границы [0,1]; независимость от behavioral state; replay consistency (zodiac_summary_hash).

---

## Complexity Tracking

No constitution violations. This section is empty.
