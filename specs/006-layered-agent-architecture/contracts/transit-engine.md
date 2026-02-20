# Contract: 006 — TransitEngine and TransitState

Однозначный контракт слоя транзитов: один выход на дату, без размытия «либо stress, либо delta».

---

## 1. TransitState (структурированный выход)

Единственный тип возвращаемого значения TransitEngine на один вызов.

| Поле           | Тип        | Описание |
|----------------|------------|----------|
| stress         | float      | Нормализованный транзитный стресс S_T(t) по контракту 005: I_T(t)/C_T, clip [0, 1]. |
| raw_delta      | Vector32   | Сырая дельта по аспектам для 32 параметров (до границ и shock). |
| bounded_delta  | Vector32   | Дельта после применения границ (ReplayConfig: global_max_delta, axis/parameter overrides) и при необходимости shock_multiplier. |

**Vector32** = `tuple[float, ...]` длины 32 (NUM_PARAMETERS по Spec 002).

Инварианты: все значения конечные; bounded_delta — результат применения той же логики, что в `hnh/modulation/boundaries.apply_bounds` к raw_delta с данным config.

---

## 2. TransitEngine

**Конструктор**: принимает `NatalChart` (и при необходимости конфиг по умолчанию). Не хранит поведенческое состояние.

**Единственный метод выхода на дату**:

- **`state(date, config) -> TransitState`**
  - `date`: дата (тип по реализации: date, datetime или эквивалент).
  - `config`: ReplayConfig (или эквивалент) — нужен для вычисления bounded_delta (границы, shock).
  - Возвращает: `TransitState(stress=..., raw_delta=..., bounded_delta=...)`.

**Не предоставляет**:

- Отдельного метода `compute_stress(date)` как единственного выхода (stress входит в TransitState).
- Отдельного метода только для raw_delta или только для bounded_delta — всё в одном вызове `state(date, config)`.

Детерминизм: при одинаковых (natal, date, config) результат `state(date, config)` идентичен.

---

## 3. Использование выше по стеку

- **BehavioralCore.apply_transits(transit_state: TransitState)**  
  Использует `transit_state.bounded_delta` (и при необходимости raw_delta внутри, если логика фасада это требует). Не вызывает TransitEngine сам.

- **LifecycleEngine.update_lifecycle(stress, ...)**  
  Получает `stress = transit_state.stress` от вызывающего (Agent).

- **Agent.step(date)** — порядок: (1) transit_state = self.transits.state(date, config); (2) при lifecycle — update_lifecycle(transit_state.stress, resilience), lifecycle видит поведение прошлого шага; (3) behavior.apply_transits(transit_state).
