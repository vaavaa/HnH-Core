# Tasks: 006 — Layered Agent Architecture

**Input**: Design documents from `specs/006-layered-agent-architecture/`  
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/layer-responsibilities.md, contracts/transit-engine.md

**Organization**: Phase 1 — астрономический слой; Phase 2 — Zodiac и поведение; Phase 3 — транзиты и lifecycle-фасад; Phase 4 — Agent; Phase 5 — совместимость и скрипты.

## Format: `[ID] [P?] Description`

- **[P]**: Можно выполнять параллельно (разные файлы, нет зависимостей).

## Path Conventions

- Новые классы: по plan.md (astronomy/ или astrology/, behavior/ или state/, agent.py или agent/).
- Существующие модули: hnh/identity, hnh/modulation, hnh/state, hnh/lifecycle, hnh/config — не ломать; только вызовы из фасадов.
- Тесты: `tests/unit/` для слоёв (planet, aspect, natal_chart, zodiac_expression, behavioral_core, transit_engine, lifecycle_engine, agent); `tests/integration/` для Agent vs replay_v2.

---

## Phase 1: Астрономический слой

- [ ] T001 [P] Ввести класс **Planet** с полями name, longitude; свойство/метод знака по ZODIAC_SIGNS[int(longitude // 30)]; опционально house. Размещение: hnh/astronomy/ или hnh/astrology/. Immutable (frozen dataclass или readonly).
- [ ] T002 Ввести класс **Aspect** с двумя планетами (или долготами), расчёт угла, классификация типа аспекта; метод tension_score() по контракту transit-stress (hard aspects, веса). Зависит от T001.
- [ ] T003 Ввести класс **NatalChart**: конструктор от birth_data; построение списка Planet и Aspect через существующие ephemeris/houses/aspects; метод compute_base_energy() или эквивалент для передачи в следующий слой. Инвариант: immutable после построения. Зависит от T001, T002.
- [ ] T004 Юнит-тесты: Planet (sign from longitude), Aspect (angle, type, tension_score), NatalChart (immutability, детерминизм при одинаковых birth_data).

---

## Phase 2: Zodiac и поведенческий слой

- [ ] T005 [P] Ввести класс **ZodiacExpression**: конструктор от NatalChart; sign_vectors, dominant_sign, dominant_element по логике 004; read-only. Размещение: hnh/astrology/zodiac_expression.py (обёртка над текущей логикой).
- [ ] T006 Ввести класс **BehavioralCore**: конструктор `BehavioralCore(natal, identity_config)`; identity_config — Identity (IdentityCore) или конфиг, дающий base_vector и sensitivity_vector. Метод `apply_transits(transit_state: TransitState)` — использует transit_state.bounded_delta и sensitivity из identity_config; делегирует в state.assembler. Не содержит F, W, state. Зависит от T003.
- [ ] T007 Юнит-тесты: ZodiacExpression (dominant_sign/element от натала), BehavioralCore (base_vector и sensitivity из identity_config, apply_transits обновляет current_vector детерминированно).

---

## Phase 3: Транзиты и Lifecycle-фасад

- [ ] T008 Ввести **TransitState** (stress, raw_delta, bounded_delta: Vector32) и класс **TransitEngine**: конструктор (NatalChart); единственный метод выхода **state(date, config) -> TransitState**. Контракт: [contracts/transit-engine.md](contracts/transit-engine.md). Фасад над hnh/lifecycle/stress и modulation (raw_delta, boundaries). Зависит от T003.
- [ ] T009 Ввести класс **LifecycleEngine**: состояние F, W, state; update_lifecycle(stress, resilience, ...); фасад над hnh/lifecycle (engine, fatigue, will). Не смешивать с BehavioralCore. Юнит-тесты: обновление F, W, переход DISABLED/TRANSCENDED по контракту 005.

---

## Phase 4: Agent

- [ ] T010 Ввести класс **Agent**: конструктор Agent(birth_data, config=None, lifecycle: bool = False). Композиция: self.natal, self.behavior, self.transits, self.lifecycle. Метод step(date) — порядок: (1) transit_state = transits.state(date, config); (2) при lifecycle — update_lifecycle(transit_state.stress, resilience), lifecycle видит поведение прошлого шага; (3) behavior.apply_transits(transit_state). Resilience из base_vector (Stability axis). Размещение: hnh/agent.py или hnh/agent/.
- [ ] T011 Юнит-тесты Agent: создание с lifecycle=False и lifecycle=True; step(date) не падает; при одинаковых входах одинаковый вывод (params_final / axis_final, при lifecycle — F, W, state).
- [ ] T012 Интеграционный тест: прогон по одним и тем же датам через replay_v2 и через Agent.step(); сравнение params_final, axis_final (допуск 1e-6); при lifecycle — сравнение F, W, state в конце.

---

## Phase 5: Обратная совместимость и скрипты

- [ ] T013 Проверить, что существующие вызовы replay_v2, run_step_v2, extract_replay_config, assemble_state, apply_bounds остаются рабочими без изменений кода вызова (регрессия).
- [ ] T014 Добавить папку scripts/006: README.md с описанием слоёв и примером использования Agent; скрипт построения Agent (product и research), вызов step() по диапазону дат, опционально сравнение с replay_v2.
- [ ] T015 Документировать в spec/plan или README: рекомендуемый путь — Agent; низкоуровневый API сохранён для скриптов и тестов.

---

## Optional (вне минимального scope)

- [ ] T016 ~~ResearchAgent/Mixin~~ — не делаем: только композиция (LifecycleEngine); Mixin при расширении (AgeEngine, MemoryDrift) ведёт к хаосу.
- [ ] T017 Вынести Planet/Aspect в отдельный пакет hnh/astronomy/ и обновить импорты (если выбран вариант с отдельным пакетом в plan).
