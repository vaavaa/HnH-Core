# Feature Specification: HnH 006 — Layered Agent Architecture

**Feature Branch**: `006-layered-agent-architecture`  
**Created**: 2025-02-20  
**Status**: Draft  
**Implementation plan**: [plan.md](plan.md) · **Tasks**: [tasks.md](tasks.md)  
**Input**: Переработка структуры ядра: слоёная модель через композицию и аккуратное наследование; явные слои абстракции (планеты → функции, знаки → стиль, дома → область, аспекты → взаимодействие, транзиты → динамика, натал → база, поведение 32D, lifecycle поверх).

---

## Clarifications

### Session 2025-02-20

- **Lifecycle — только композиция**: используется **LifecycleEngine** как отдельный компонент (`agent.lifecycle: LifecycleEngine | None`). Mixin при расширении (AgeEngine, MemoryDrift и т.д.) не применяем — ведёт к хаосу наследования; один `Agent` с опциональным `lifecycle=LifecycleEngine(...)`.
- **Глубина иерархии**: не более 2–3 уровней наследования; не делать Planet → Zodiac, Agent → NatalChart, не встраивать Lifecycle внутрь BehavioralCore.
- **Порядок в step(date)**: (1) stress вычисляется (transit_state); (2) lifecycle обновляется — учитывает **поведение прошлого шага** (current_vector до apply_transits в этом шаге); (3) behavior модифицируется (apply_transits). Lifecycle не видит уже обновлённое транзитами поведение текущего шага.
- **Обратная совместимость**: существующие API (replay_v2, assembler, modulation) остаются рабочими; новая структура — фасад/реорганизация и явные типы слоёв.
- Q: Что значит «Legacy APIs MUST delegate to Agent.step()»? → A: **Строгое делегирование**: replay_v2 и run_step_v2 внутри обязаны создавать Agent (или эквивалент) и вызывать его step(date); другая реализация не допускается.
- Q: identity_config должен быть обязательно IdentityCore или допустим любой объект с base_vector и sensitivity_vector? → A: **Протокол (структурная типизация)**: любой объект с атрибутами base_vector и sensitivity_vector (оба tuple[float, ...] длины 32); тип IdentityCore не обязателен.
- Q: Какой контракт у birth_data для NatalChart и Agent? → A: В спеке задаётся только общее («дата, время, место или готовые позиции»); точный формат (ключи, типы) фиксируется в plan.md или data-model/контракте.
- Q: Нужны ли в спеке 006 явные критерии приёмки? → A: Краткий блок Acceptance criteria в спеке (3–5 пунктов); детали тестов и чекпоинтов — в plan/tasks.
- Q: ZodiacExpression обязателен при создании Agent или по требованию? → A: **По требованию**: Agent может быть построен только из natal; ZodiacExpression создаётся при необходимости (lazy) или отдельным вызовом; не входит в обязательный конструктор Agent.

---

## 1. Objective

Ввести явную **слоёную архитектуру** с человекочитаемыми уровнями абстракции и переорганизовать код в виде Python-классов с чётким разделением ответственности:

| Слой (человеческий) | Сущность в коде        | Назначение                          |
|---------------------|------------------------|-------------------------------------|
| Планеты             | Функции                | Базовые астрономические позиции     |
| Знаки               | Стиль                  | Zodiac expression (read-only)       |
| Дома                | Область проявления     | Контекст (houses)                   |
| Аспекты             | Взаимодействие         | Напряжение / поток между планетами |
| Транзиты            | Динамика / погода      | Временная модуляция                 |
| Натал               | Базовая конфигурация  | Неизменяемая карта рождения         |
| Поведение           | 32D                    | Текущий вектор личности             |
| Lifecycle           | Поверх                 | Опциональная энтропия (research)    |

Цели:

- Чистая изоляция Research-режима без `if lifecycle_enabled` внутри ядра поведения.
- Один способ оркестрации — **Agent** (композиция: natal, behavior, transits, опционально lifecycle).
- Готовность к выносу конфигурации и коэффициентов (006 может пересекаться с рефакторингом конфига из отдельного плана).

---

## 2. Design Principles

1. **Композиция предпочтительнее наследования**  
   Agent владеет ссылками на NatalChart, BehavioralCore, TransitEngine, опционально LifecycleEngine. Не наследует NatalChart.

2. **Нет магических флагов**  
   Режим задаётся типом агента или наличием компонента (например `agent.lifecycle is not None`), а не глобальным флагом внутри логики.

3. **Неподвижная база**  
   NatalChart — неизменяемая после построения. ZodiacExpression — read-only view над наталом.

4. **Динамика в отдельном слое**  
   BehavioralCore хранит base_vector и current_vector; транзиты и lifecycle обновляют состояние через явные вызовы, не проникая внутрь формулы сборки 32D.

5. **Не делать**  
   - Planet не наследует Zodiac.  
   - Agent не наследует NatalChart.  
   - Lifecycle не встраивать внутрь BehavioralCore.  
   - Глубокую иерархию (5+ уровней наследования).

---

## 3. Invariants

Неизменяемые правила архитектуры; нарушение считается деградацией. Проверять при код-ревью и доработках.

| Invariant | Описание |
|-----------|----------|
| **NatalChart immutable** | После построения NatalChart не изменяется (никакие поля не мутируют). Replay и детерминизм опираются на неизменную базу. |
| **BehavioralCore never mutates base_vector** | BehavioralCore обновляет только `current_vector`. `base_vector` задаётся при создании (из identity_config) и далее не меняется. |
| **LifecycleEngine never mutates BehavioralCore directly** | LifecycleEngine не обращается к behavior и не меняет его поля. Влияние lifecycle на поведение — только через контракт (например activity suppression в формулах), не через прямую запись в BehavioralCore. |
| **Agent is the only orchestrator** | Единственная точка оркестрации шага — `Agent.step(date)`. Компоненты (transits, behavior, lifecycle) не вызывают друг друга напрямую; только Agent передаёт данные между ними. |
| **No circular dependencies** | Зависимости между слоями односторонние: например TransitEngine не зависит от BehavioralCore, LifecycleEngine не зависит от BehavioralCore, BehavioralCore не зависит от LifecycleEngine. Граф модулей/пакетов без циклов. |

---

## 4. Layer Definitions

### 4.1 Астрономический слой (Astronomical)

Чистые данные и вычисления позиций/углов.

**Planet**

- Поля: `name: str`, `longitude: float` (эклиптическая долгота).
- Вычисление знака из долготы: `sign = ZODIAC_SIGNS[int(longitude // 30)]`.
- Дом (`house`) задаётся позже при наличии системы домов (например Placidus).

**Aspect**

- Поля: две планеты (или пары долгот), угол между ними.
- Классификация типа аспекта (Conjunction, Opposition, Square, …).
- Метод напряжения/веса для hard aspects: например `tension_score() -> float` по контракту транзитного стресса (005).

**NatalChart**

- Вход: **birth_data** — данные рождения (дата, время, место или готовые позиции). Точный формат (ключи, типы) задаётся в plan.md или data-model/контракте, не в спеке.
- Содержит: список планет (Planet), список аспектов (Aspect), при необходимости дома.
- Методы: построение из birth_data, агрегация «базовой энергии» для передачи в следующий слой (например `compute_base_energy()` или экспорт позиций для BehavioralCore).
- Инвариант: после построения объект неизменяем (immutable) для целей replay.
- NatalChart fields MUST be stored as immutable containers (tuples). No lists in the final object.

### 4.2 Zodiac Layer (read-only)

**ZodiacExpression**

- Вход: `NatalChart` (или эквивалентные данные).
- Содержит: векторы по знакам, доминантный знак/элемент (по контракту 004 при необходимости).
- Методы: `dominant_sign()`, `dominant_element()`, при необходимости хеш зодиака для идентичности.
- Не мутирует натал; только представление (view).

### 4.3 Поведенческий слой (32D)

**BehavioralCore**

- Вход: `NatalChart` и **identity_config** — любой объект по **протоколу**: атрибуты `base_vector` и `sensitivity_vector` (оба `tuple[float, ...]` длины 32). Тип IdentityCore не обязателен (допустимы заглушки, обёртки). BehavioralCore не дублирует данные, а читает их через identity_config при вызовах.
- Конструктор: `BehavioralCore(natal, identity_config)` — base_vector и sensitivity_vector берутся как `identity_config.base_vector`, `identity_config.sensitivity_vector`.
- Поля: `base_vector` (32), `current_vector` (32); sensitivity для apply_transits берётся из identity_config при вызове.
- Методы:
  - Инициализация base_vector из identity (при необходимости построение Identity из натала через существующую логику 002: compute_sensitivity(natal_data), база из натала/зодиака).
  - `apply_transits(transit_state: TransitState)` — обновление current_vector по `transit_state.bounded_delta`, sensitivity из identity, memory (делегирование в assembler + boundaries).
- Не содержит логики fatigue/will/death; только 32-параметрическое состояние.
- Internal representation MAY be mutable for performance, but external snapshots/logs MUST be immutable.

### 4.4 Транзиты (динамика / погода)

**Контракт TransitEngine** (однозначный; без размытия слоя):

TransitEngine **возвращает один структурированный объект** на дату — не «либо stress, либо delta», а единый выход:

**TransitState** (dataclass или frozen):

- `stress: float` — нормализованный S_T(t) по контракту 005 (I_T/C_T, clip [0, 1]).
- `raw_delta: Vector32` — сырая дельта по аспектам (32 параметра); `Vector32 = tuple[float, ...]` длины 32.
- `bounded_delta: Vector32` — после применения границ и (при необходимости) shock из ReplayConfig.

**TransitEngine**

- Вход: `NatalChart` (для сравнения транзитов с наталом); при вызове — дата и конфиг (ReplayConfig для bounded_delta).
- Один метод: **`state(date, config) -> TransitState`** — возвращает `TransitState(stress, raw_delta, bounded_delta)`.
- Не владеет поведенческим состоянием; только «погода» на дату. Детерминирован: одинаковые (natal, date, config) → один и тот же TransitState.
- TransitEngine MUST be stateless. TransitState depends only on (natal, date, config).

### 4.5 Lifecycle (опционально) — только композиция

**LifecycleEngine** — отдельный объект, не Mixin. При расширении (AgeEngine, MemoryDrift и т.п.) Mixin-подход даёт хаос наследования; фиксируем единственный способ: композиция.

- `LifecycleEngine`: поля F, W, state (ALIVE | DISABLED | TRANSCENDED); метод `update_lifecycle(stress, resilience)`.
- `Agent(birth_data, lifecycle=False)`: при `lifecycle=True` создаётся `self.lifecycle = LifecycleEngine(...)`; иначе `self.lifecycle = None`.
- Порядок в `step(date)` фиксирован: **сначала** обновляется lifecycle (см. §3.6), **затем** модифицируется behavior. Lifecycle учитывает **поведение прошлого шага** (current_vector до apply_transits в этом шаге), не уже обновлённое транзитами.

### 4.6 Агент (оркестрация)

**Agent**

- Конструктор: `birth_data` (формат — в plan/data-model), опционально конфиг (replay_config, lifecycle_enabled и т.д.). **ZodiacExpression** не обязателен в конструкторе: создаётся по требованию (lazy) или отдельным вызовом, если нужен.
- Компоненты (композиция):
  - `self.natal = NatalChart(birth_data)`
  - `self.behavior = BehavioralCore(self.natal, identity_config)` (identity_config строит Agent из натала или принимает снаружи)
  - `self.transits = TransitEngine(self.natal)`
  - `self.lifecycle = LifecycleEngine(...) if lifecycle else None`
  - ZodiacExpression — по требованию (например `self._zodiac` или метод `zodiac_expression()`), не обязательное поле конструктора.
- Метод `step(date)` — **порядок жёстко зафиксирован**:
  1. **Stress вычисляется**: `transit_state = self.transits.state(date, config)` — получаем `TransitState(stress, raw_delta, bounded_delta)`.
  2. **Lifecycle обновляется** (если есть): `self.lifecycle.update_lifecycle(transit_state.stress, resilience)`. resilience MUST be computed from behavior.current_vector before apply_transits in this step. Lifecycle при этом опирается на **поведение прошлого шага** (current_vector до модификации в этом шаге), не на уже обновлённое транзитами.
  3. **Behavior модифицируется**: `self.behavior.apply_transits(transit_state)` — обновление current_vector по `transit_state.bounded_delta`.

**Product-mode**: Agent с `lifecycle=None` — только natal + behavior + transits.

**Research-mode**: Agent с `lifecycle=LifecycleEngine(...)` — плюс обновление F, W, проверка death/transcendence.

---

## 5. File / Package Layout (target)

Структура пакета после 006 (логическая группировка; точные пути — в plan.md):

- **Астрономический слой**: классы Planet, Aspect, NatalChart (модуль/пакет `hnh/astronomy/` или внутри `hnh/astrology/` с переименованием ролей).
- **Zodiac**: ZodiacExpression в `hnh/astrology/` (или отдельный подмодуль).
- **Поведение**: BehavioralCore в `hnh/behavior/` или `hnh/state/` (использует identity/schema, modulation, assembler).
- **Транзиты**: TransitEngine в `hnh/astrology/transits.py` или отдельный модуль.
- **Lifecycle**: существующий `hnh/lifecycle/`; LifecycleEngine — фасад над engine.py, fatigue, stress.
- **Агент**: новый модуль `hnh/agent.py` или `hnh/agent/` с классом Agent (lifecycle через композицию; без ResearchAgent/Mixin).

Существующие модули (identity, modulation, state.assembler, config, lifecycle.engine) остаются источниками логики; новые классы их композируют, не дублируя формулы.

---

## 6. Contracts and Compatibility

- **Determinism**: все слои остаются детерминированными; replay по (birth_data, config, dates) даёт тот же результат.
- **ReplayConfig**: без изменений контракта 002/005; Agent принимает конфиг и передаёт в BehavioralCore / TransitEngine / LifecycleEngine где нужно.
- **Контракты 004 (zodiac), 005 (transit-stress, lifecycle)**: сохраняются; новые классы вызывают существующие функции/модули.
- **Legacy APIs (replay_v2, run_step_v2) MUST delegate to Agent.step() without behavioral change.** Делегирование строгое: реализация replay_v2/run_step_v2 обязана создавать Agent (или эквивалент) и вызывать его step(date); дублирование логики вне Agent не допускается.

---

## 7. Acceptance Criteria

Feature complete when:

- Слои реализованы по контракту: Planet, Aspect, NatalChart (immutable), ZodiacExpression, BehavioralCore, TransitEngine (state → TransitState), LifecycleEngine (опционально), Agent.
- Agent.step(date) выполняет порядок: (1) transit_state, (2) lifecycle при наличии, (3) behavior.apply_transits; resilience из current_vector до apply_transits.
- replay_v2 и run_step_v2 делегируют в Agent.step() (строгое делегирование).
- Инварианты соблюдены: NatalChart immutable, BehavioralCore не мутирует base_vector, LifecycleEngine не мутирует BehavioralCore, Agent — единственный оркестратор, нет циклических зависимостей.
- Детерминизм и обратная совместимость с 002/005 сохранены; контракты TransitState и layer-responsibilities выполнены.

Детали тестов, чекпоинтов и скриптов — в plan.md и tasks.md.

---

## 8. Out of Scope for 006

- Перемещение конфигурации и коэффициентов в файлы (YAML/TOML) — отдельный план/спека.
- Изменение формул 002/005; только реорганизация в классы и композицию.
- Удаление старого API (replay_v2, run_step_v2 и т.д.) до явного решения о deprecation.

---

## References

- Plan: [plan.md](plan.md)
- Tasks: [tasks.md](tasks.md)
- Data model: [data-model.md](data-model.md)
- Contracts: [contracts/layer-responsibilities.md](contracts/layer-responsibilities.md), [contracts/transit-engine.md](contracts/transit-engine.md)
