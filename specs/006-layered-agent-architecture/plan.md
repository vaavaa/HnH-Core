# Implementation Plan: 006 — Layered Agent Architecture

**Branch**: `006-layered-agent-architecture` | **Date**: 2025-02-20 | **Spec**: [spec.md](spec.md)  
**Input**: Слоёная модель с явными абстракциями (планеты → функции, знаки → стиль, дома → область, аспекты → взаимодействие, транзиты → динамика, натал → база, поведение 32D, lifecycle поверх). Композиция предпочтительнее наследования; Agent оркестрирует компоненты.  
**Clarifications** (spec § Clarifications): строгое делегирование (replay_v2/run_step_v2 обязаны вызывать Agent.step()); identity_config — протокол (base_vector, sensitivity_vector); birth_data — формат в plan/data-model; ZodiacExpression по требованию, не в конструкторе Agent; acceptance criteria — кратко в спеке §7.

---

## Summary

Ввести в ядре HnH явные классы слоёв: **Planet**, **Aspect**, **NatalChart** (астрономический слой), **ZodiacExpression** (read-only вид), **BehavioralCore** (32D), **TransitEngine** (погода), **LifecycleEngine** (опционально), **Agent** (оркестрация через композицию). Существующую логику (modulation, assembler, identity, lifecycle.engine) не переписывать, а вызывать из новых фасадов. Product-mode = Agent без lifecycle; Research-mode = Agent с lifecycle. Детерминизм и replay сохраняются.

---

## Technical Context

**Language**: Python 3.12 (текущий стек HnH)  
**Dependencies**: 002, 004, 005 (identity, modulation, state, astrology, lifecycle, config)  
**Testing**: pytest; юнит-тесты на новые классы; интеграционные тесты Agent.step() с/без lifecycle  
**Constraints**: replay_v2 и run_step_v2 **обязаны делегировать** в Agent.step() (строгое делегирование, spec §6); не более 2–3 уровней наследования; без магических флагов внутри логики

---

## Constitution Check

- [ ] **Determinism**: Agent.step(date) с одинаковыми birth_data, config, dates даёт тот же результат; replay-подпись не меняется.
- [ ] **Composition**: Agent владеет natal, behavior, transits, lifecycle (optional); не наследует NatalChart.
- [ ] **Mode isolation**: Research vs Product задаётся наличием lifecycle-компонента, не флагом внутри BehavioralCore.
- [ ] **Legacy delegation**: replay_v2 и run_step_v2 реализованы через создание Agent и вызов step(date); дублирование логики вне Agent не допускается (spec §6).
- [ ] **Existing API**: extract_replay_config, assembler, modulation остаются источниками логики; новые классы — фасад/оркестрация.
- [ ] **Invariants** (spec §3): NatalChart immutable; BehavioralCore never mutates base_vector; LifecycleEngine never mutates BehavioralCore directly; Agent is the only orchestrator; no circular dependencies.
- [ ] **Repository standards**: Python, type hints, orjson/xxhash где применимо; структура папок по spec §4.
- [ ] **Logging validation**: вывод state_logger и replay-подпись соответствуют контракту (структура записи, configuration_hash, transit_signature и т.д.); логирование не нарушает детерминизм.

---

## Implementation Outline

### 1. Астрономический слой

- **Planet**: класс с `name: str`, `longitude: float`; метод/свойство знака из долготы (ZODIAC_SIGNS[int(longitude // 30)]). При необходимости `house: int | None` для последующего заполнения.
- **Aspect**: класс с двумя планетами (или долготами), расчёт угла, классификация типа (Conjunction, Opposition, Square, …); метод `tension_score() -> float` по контракту transit-stress (005).
- **NatalChart**: конструктор от **birth_data**; точный формат (ключи, типы) задаётся в data-model.md или контракте (spec: «дата, время, место или готовые позиции»). Внутренне вызывает существующую логику ephemeris/houses; хранит **immutable** контейнеры (tuples), не списки; список Planet и список Aspect. Метод `compute_base_energy()` или эквивалент. Инвариант: после построения объект immutable для replay.
- Размещение: новый пакет `hnh/astronomy/` или расширение `hnh/astrology/` с чётким разделением (астрономия vs интерпретация). Контракт: [contracts/layer-responsibilities.md](contracts/layer-responsibilities.md).

### 2. Zodiac Layer

- **ZodiacExpression**: конструктор принимает NatalChart (или данные для построения view); вычисляет sign_vectors, dominant_sign, dominant_element по логике 004; read-only, не мутирует натал. **Не обязателен в конструкторе Agent** (spec clarification): создаётся по требованию (lazy) или отдельным вызовом.
- Размещение: `hnh/astrology/zodiac_expression.py` (уже есть) — обернуть в класс ZodiacExpression с явным конструктором от NatalChart.

### 3. Поведенческий слой (32D)

- **BehavioralCore**: конструктор `BehavioralCore(natal, identity_config)`. **identity_config** — любой объект по **протоколу**: атрибуты `base_vector` и `sensitivity_vector` (оба `tuple[float, ...]` длины 32); тип IdentityCore не обязателен (spec clarification). Метод `apply_transits(transit_state: TransitState)` принимает выход TransitEngine; использует `transit_state.bounded_delta` и sensitivity из identity_config; делегирует в state.assembler (границы уже в TransitState). Не содержит fatigue/will/death.
- Размещение: новый модуль `hnh/behavior/core.py` или `hnh/state/behavioral_core.py` (на выбор по минимальному расхождению с текущей структурой).

### 4. Транзиты

- **TransitEngine** и **TransitState**: контракт зафиксирован — один выход на дату. TransitState(stress, raw_delta, bounded_delta); TransitEngine имеет единственный метод **state(date, config) -> TransitState**. Не «либо stress, либо delta» — всегда структурированный объект. Конфиг нужен для bounded_delta (ReplayConfig). См. [contracts/transit-engine.md](contracts/transit-engine.md). Не хранит состояние поведения.
- Размещение: `hnh/astrology/transits.py` (или отдельный модуль) — TransitEngine и TransitState.

### 5. Lifecycle

- **LifecycleEngine**: фасад над `hnh/lifecycle/engine`: состояние F, W, state (ALIVE | DISABLED | TRANSCENDED); метод `update_lifecycle(stress: float, resilience: float)` (и при необходимости S_g, конфиг). Не смешивать с BehavioralCore.
- Размещение: в `hnh/lifecycle/` добавить класс LifecycleEngine (или переименовать/рефакторить текущий run/engine в класс).

### 6. Agent

- **Agent**: конструктор `Agent(birth_data, config=None, lifecycle: bool = False)`; birth_data по контракту из data-model/план. Опционально принимает identity_config (иначе строит из натала по логике 002).
  - Создаёт `self.natal = NatalChart(birth_data)`.
  - Создаёт identity_config (объект с .base_vector и .sensitivity_vector по протоколу, например IdentityCore или из натала/конфига), затем `self.behavior = BehavioralCore(self.natal, identity_config)`.
  - Создаёт `self.transits = TransitEngine(self.natal)`.
  - При `lifecycle=True`: `self.lifecycle = LifecycleEngine(...)`; иначе `self.lifecycle = None`.
  - **ZodiacExpression** не в конструкторе: по требованию (lazy, например метод `zodiac_expression()` или свойство), если нужен (spec clarification).
  - Метод `step(date)` — порядок: (1) transit_state = self.transits.state(date, config); (2) resilience из behavior.current_vector до apply_transits; (3) при self.lifecycle — update_lifecycle(transit_state.stress, resilience); (4) self.behavior.apply_transits(transit_state).
- Размещение: `hnh/agent.py` (один модуль) или `hnh/agent/__init__.py` с классом Agent.
- **Без ResearchAgent/Mixin**: только один класс Agent с параметром `lifecycle=True/False`; при расширении (AgeEngine, MemoryDrift) Mixin вёл бы к хаосу наследования.

### 7. Обратная совместимость и делегирование Legacy

- **Строгое делегирование** (spec §6): реализации `replay_v2` и `run_step_v2` **обязаны** создавать Agent (или эквивалент) и вызывать его `step(date)`; дублирование логики шага вне Agent не допускается. Рефакторинг: внутри replay_v2/run_step_v2 — построение Agent из тех же входов и вызов step() по датам.
- Не удалять и не ломать контракты `extract_replay_config`, `assemble_state`, `apply_bounds`, логику в modulation/delta — они вызываются из фасадов (BehavioralCore, TransitEngine, LifecycleEngine) и из Agent.
- Документация: «канонический путь — Agent.step(); replay_v2/run_step_v2 делегируют в Agent».

### 8. Скрипты и тесты

- **Scripts**: папка `scripts/006/` с демо: построение Agent (product и research), вызов step() по дням, сравнение с replay_v2 по детерминизму.
- **Tests**: unit — Planet, Aspect, NatalChart (immutability), ZodiacExpression, BehavioralCore, TransitEngine, LifecycleEngine, Agent.step(); integration — полный прогон Agent с lifecycle и без, проверка совпадения с replay_v2 при тех же входах.

---

## Target Package Layout (after 006)

```
hnh/
  agent.py           # или hnh/agent/ — Agent (lifecycle только композиция)
  astrology/         # ephemeris, houses, aspects, transits, zodiac_expression
    transits.py      # TransitEngine фасад
  astronomy/         # (опционально) Planet, Aspect, NatalChart если выносим в отдельный пакет
  behavior/          # (опционально) BehavioralCore
  config/            # без изменений
  identity/          # без изменений
  lifecycle/         # + LifecycleEngine фасад
  modulation/        # без изменений
  state/             # без изменений (assembler, replay_v2)
```

Альтернатива без новых папок: Planet/Aspect/NatalChart в `hnh/astrology/`, BehavioralCore в `hnh/state/behavioral_core.py`, LifecycleEngine в `hnh/lifecycle/engine.py` (класс), Agent в `hnh/agent.py`. Итоговый выбор — в tasks (T001–T002).

**Контракт birth_data** (spec clarification): точный формат (ключи, типы) для NatalChart и Agent задаётся в [data-model.md](data-model.md) или в отдельном контракте; в спеке — только общее описание («дата, время, место или готовые позиции»). Задача T003 или data-model должна зафиксировать схему (например datetime, lat, lon или эквивалент по 002/004).

---

## Risks & Mitigations

- **Дублирование логики**: строго делегировать в существующие модули (modulation, assembler, lifecycle); новые классы только фасад и композиция.
- **Регрессия replay**: после рефакторинга replay_v2 вызывает Agent.step(); интеграционные тесты проверяют, что результат (params_final, axis_final, при lifecycle — F, W, state) совпадает с эталоном при одинаковых входах.
- **Перегруз структуры**: ограничить глубину наследования 2–3 уровнями; предпочесть композицию (Agent с полями natal, behavior, transits, lifecycle).
