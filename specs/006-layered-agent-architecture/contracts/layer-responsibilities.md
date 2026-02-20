# Contract: 006 — Layer Responsibilities

Краткий контракт ответственности слоёв и запрещённых связей. См. также **Invariants** в [spec.md](../spec.md#3-invariants) — их нарушение считается деградацией архитектуры.

## 1. Слои и ответственность

| Слой | Класс(ы) | Ответственность | Не делает |
|------|----------|-----------------|-----------|
| Астрономия | Planet, Aspect, NatalChart | Позиции, углы, классификация аспектов; immutable база | Не интерпретирует знаки/дома как «стиль»; не хранит поведенческое состояние |
| Zodiac | ZodiacExpression | Read-only вид: знаки, элементы, доминанты | Не мутирует NatalChart; не вычисляет дельты для 32D |
| Поведение | BehavioralCore | Конструктор (natal, identity_config). base_vector, current_vector (32D); sensitivity из Identity (identity_config); apply_transits | Не содержит F, W, state; не хранит свой sensitivity_vector (берёт из Identity); не знает о транзитных аспектах напрямую (получает готовый delta/stress) |
| Транзиты | TransitEngine | state(date, config) -> TransitState(stress, raw_delta, bounded_delta); один выход на дату | Не хранит current_vector; не обновляет поведение; не предоставляет отдельно только stress или только delta |
| Lifecycle | LifecycleEngine | F, W, state; update_lifecycle(stress, resilience) | Не встроен в BehavioralCore; не знает о натале (только stress, resilience) |
| Оркестрация | Agent | step(date): (1) stress/deltas, (2) lifecycle (видит поведение прошлого шага), (3) behavior.apply_transits | Не наследует NatalChart; порядок шага жёстко зафиксирован |

## 2. Запрещённые связи

- **Planet** не наследует Zodiac; знак вычисляется по долготе в Planet или в ZodiacExpression.
- **Agent** не наследует NatalChart; Agent владеет экземпляром NatalChart.
- **Lifecycle** не встраивается внутрь BehavioralCore; отдельный компонент, вызываемый из Agent.
- **Lifecycle — только композиция**: не Mixin, не ResearchAgent-подкласс; Agent с полем `lifecycle: LifecycleEngine | None`. При расширении (AgeEngine, MemoryDrift) Mixin даёт хаос наследования.

**Invariants** (spec §3): NatalChart immutable; BehavioralCore never mutates base_vector; LifecycleEngine never mutates BehavioralCore directly; Agent is the only orchestrator; no circular dependencies.

## 3. Делегирование в существующий код

- **NatalChart**: построение планет/аспектов/домов — вызов hnh/astrology (ephemeris, houses, aspects).
- **BehavioralCore**: base_vector из Identity/натала по 002/004; apply_transits — hnh/modulation (delta, boundaries), hnh/state/assembler.
- **TransitEngine**: state(date, config) возвращает TransitState; внутренне — hnh/lifecycle/stress (stress), modulation (raw_delta, boundaries для bounded_delta). Контракт: [transit-engine.md](transit-engine.md).
- **LifecycleEngine**: update_lifecycle — hnh/lifecycle (engine, fatigue, will, death, transcendence).

Новые классы не дублируют формулы; они фасады и композиция.

## 4. Детерминизм и replay

Все слои детерминированы: одинаковые birth_data, config, dates → одинаковые выходы. Replay-подпись и configuration_hash по 002/005 не меняются при использовании Agent; Agent передаёт конфиг в нужные компоненты.
