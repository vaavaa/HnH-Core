# Implementation Plan: Deterministic Personality Engine v0.1 (HnH Core)

**Branch**: `001-deterministic-personality-engine` | **Date**: 2025-02-17 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/001-deterministic-personality-engine/spec.md`

---

## Summary

Reference implementation движка HnH: Identity Core + Dynamic State с инжектируемыми seed и временем, детерминированный режим симуляции, логирование переходов состояния, replay без LLM и внешних API. Технологический выбор: Python 3.12+, pydantic, pytest; опционально — pyswisseph для натальной/транзитной астрологии как символического ввода в Identity Core. План согласован со спецификацией 001 и конституцией HnH.

---

## 1. Technology Stack

### Primary Language
**Python 3.12+**

Rationale: зрелая экосистема (в т.ч. биндинги Swiss Ephemeris), удобный контроль детерминизма, сильные тестовые фреймворки, типизация.

### Core Dependencies
- **pydantic (v2+)** — контракты данных (Identity, State, лог, векторы).
- **dataclasses** — где уместно, без дублирования с pydantic.

### Astrology (optional for v0.1 reference)
- **pyswisseph** — Swiss Ephemeris (натальная карта, позиции, транзиты, аспекты). Локальная библиотека, не внешний API; соответствует «optional symbolic_input» в спеке.

### Testing
- **pytest**, **pytest-cov** — цель 90%+ покрытия по ядру (spec FR-013).

### Logging
- **structlog** или стандартный logging со структурированным выводом (JSON-like). Один лог-рекорд на переход состояния по контракту из спеки. Без отладочного print.

### Optional (Phase 4+ / вне скоупа 001)
- OpenAI / Anthropic SDK (адаптер LLM).
- FastAPI (будущий API-слой).

---

## 2. Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: pydantic v2+, pytest, pytest-cov, structlog; опционально pyswisseph  
**Storage**: N/A (in-memory для v0.1)  
**Testing**: pytest, pytest-cov, 90%+ core  
**Target Platform**: Linux/macOS/Windows, CLI  
**Project Type**: single (пакет + CLI)  
**Performance Goals**: детерминированность и воспроизводимость важнее throughput  
**Constraints**: без random без seed, без datetime.now() в ядре; все времена и seed инжектируются  
**Scale/Scope**: один процесс, in-memory; референсная реализация

---

## 3. Constitution Check

*GATE: Must pass before Phase 0. Re-check after Phase 1.*

- [x] **Deterministic Mode**: Seed и time инжектируются; переходы логируются; replay пошаговый; в ядре нет недетерминированного кода.
- [x] **Identity/Core separation**: Identity Core неизменяем; Dynamic State не мутирует Core; Relational Memory user-scoped; Behavioral Interface без логики личности.
- [x] **Minimal Reference Implementation**: Реализация без LLM и внешних API; структурированный лог и детерминированный replay.
- [x] **Behavioral Parameterization**: Символический ввод (натальная карта и т.п.) маппится в измеримые параметры; вектор из семи размерностей по спеке.
- [x] **Logging & Observability**: Лог по контракту спеки; экспорт снапшотов, интроспекция состояния, diff параметров предусмотрены.
- [x] **Repository Standards**: Один язык (Python), Black, Ruff, один тест-фреймворк; контракты в коде и в contracts/.

---

## 4. Repository Structure

### Documentation (this feature)

```text
specs/001-deterministic-personality-engine/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md   # создаётся /speckit.tasks
```

### Source Code (repository root)

```text
hnh/
├── core/
│   ├── identity.py      # Identity Core
│   ├── natal.py         # optional: natal → base vector
│   ├── parameters.py    # behavioral vector (7 dims)
├── astrology/           # optional for 001
│   ├── ephemeris.py
│   ├── aspects.py
│   ├── transits.py
├── state/
│   ├── modulation.py
│   ├── dynamic_state.py
│   ├── replay.py
├── memory/
│   ├── relational.py
│   ├── update_rules.py
├── interface/
│   ├── behavioral_vector.py
│   └── llm_adapter.py   # Phase 4+, не для 001
├── logging/
│   ├── state_logger.py
│   └── contracts.py
├── tests/
└── cli.py
```

**Structure Decision**: Один пакет `hnh/` с модулями по слоям (core, state, memory, interface, logging). CLI в корне пакета. Тесты в корне репозитория: `tests/unit/`, `tests/integration/` (см. tasks.md).

---

## 5. Core Contracts

### 5.1 Identity Core Contract

- **identity_id** (str), уникальный; повторное создание с тем же id → ошибка (spec).
- **base_traits** / **base_behavior_vector**: ровно семь размерностей (spec): warmth, strictness, verbosity, correction_rate, humor_level, challenge_intensity, pacing; нормализованы 0.0–1.0; значения вне [0,1] → reject.
- **optional symbolic_input**: напр. birth_datetime (UTC), birth_location (lat, lon), natal_positions — для маппинга в base_behavior_vector (астрология опциональна).
- **identity_hash**: стабильный, детерминированный.
- Ограничения: неизменяем после создания, hashable, serializable, без мутации в рантайме.

### 5.2 Behavioral Vector Contract (spec-aligned)

Ровно семь полей, float [0.0–1.0]: warmth, strictness, verbosity, correction_rate, humor_level, challenge_intensity, pacing. Reject вне [0,1], без clamp, без NaN.

### 5.3 Transit Contract (optional, для Planetary Agent)

TransitSet: timestamp (UTC, инжектируется), planetary_positions, aspects_to_natal, aspect_weights. При одинаковом времени → одинаковый набор. Используется только если включён слой astrology.

### 5.4 Dynamic State Contract

- identity_hash, timestamp (injected), transit_signature (optional), relational_modifier (optional), final_behavior_vector.
- Воспроизводимость по: identity + time + relational memory snapshot. Без использования системных часов в ядре.

### 5.5 Relational Memory Contract (v0.1)

- **user_id** (str), один экземпляр на пользователя.
- Минимальная схема (spec): упорядоченный список событий; каждое событие: sequence index (step), type, payload.
- Допустимые производные/метрики в payload (на выбор реализации): interaction_count, error_rate_history, responsiveness_metric, derived_relationship_modifiers — при сохранении детерминированных правил обновления.
- Не мутирует Identity Core; сериализуемый снапшот; детерминированные update rules.

### 5.6 State Transition Log Contract (spec minimal + extended)

**Минимальный контракт (spec):** один рекорд на переход; обязательные поля: seed, injected_time, identity_hash, active_modifiers, final_behavioral_vector; текст, одна запись на строку (e.g. JSON Lines); diffable, пригоден для replay.

**Расширение в плане:** допускаются дополнительные поля, напр. transit_signature, relational_snapshot_hash, deterministic_seed — при сохранении минимального набора. Конкретные имена полей и кодировка задаются в реализации (см. logging/contracts.py).

---

## 6. Deterministic Replay Requirements

- Replay принимает: injected time, injected relational snapshot, identity.
- Выход идентичен при одинаковых входах.
- В ядре не используется system clock; всё время dependency-injected.

---

## 7. Configuration Strategy

- YAML или TOML: орбы, веса аспектов (если используется astrology), версионирование.
- Без хардкода магических констант.

---

## 8. Determinism Rules

В ядре запрещено:
- random без явного seed.
- datetime.now().
- Неявный float drift.

Все операции с float согласованы и при необходимости clamp только внутри допустимых границ; входные значения вне [0,1] — reject (spec).

---

## 9. MVP Milestones (alignment with spec 001)

| Milestone | Содержание | В scope 001 |
|-----------|------------|-------------|
| 1 | Движок астрологии (natal + transit) детерминированно | опционально (symbolic_input) |
| 2 | Слой маппинга → behavioral vector (7 dims) | да |
| 3 | Dynamic State + replay + лог | да |
| 4 | LLM adapter | нет (Future / Phase 4+) |
| 5 | Relational Memory (minimal schema) | да |
| 6 | Teacher MVP / deployment | нет (Future) |

Для фичи 001 обязательны: Identity Core, Dynamic State, seed/time injection, logging, replay, минимальная Relational Memory; без LLM и без внешних API.

---

## 10. Engineering Constraints

- Один язык: Python.
- **Black** — форматирование.
- **Ruff** — линтинг.
- Pre-commit hooks обязательны.
- Типизация (mypy strict рекомендуется).

---

## 11. Success Criteria (from spec + plan)

- Identity неизменяем; один Core на identity_id.
- Daily transit (если используется) даёт детерминированную модуляцию.
- Replay даёт идентичный вывод при тех же входах.
- Логи фиксируют полный переход состояния по минимальному контракту.
- Слой LLM опционален и не требуется для логики ядра (spec 001).
- Все тесты проходят; покрытие ядра 90%+.

---

## Complexity Tracking

Нет нарушений конституции; таблица пуста.
