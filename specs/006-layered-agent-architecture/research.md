# Research: 006 — Layered Agent Architecture

**Phase 0**: Решения по слоям и композиции; альтернативы и ограничения.

## Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Композиция vs наследование | Композиция предпочтительна; Agent владеет natal, behavior, transits, lifecycle | Меньше связности; проще тестировать; нет глубокой иерархии. |
| Режим Research/Product | Задаётся наличием компонента lifecycle (lifecycle=True → self.lifecycle = LifecycleEngine()); только композиция, без Mixin | Нет магических флагов; при расширении (AgeEngine, MemoryDrift) Mixin ведёт к хаосу наследования. |
| NatalChart | Immutable после построения | Replay и детерминизм требуют стабильной базы. |
| ZodiacExpression | Read-only view над наталом | Знаки/стиль не мутируют астрономический слой. |
| Lifecycle внутри BehavioralCore | Не встраивать | Lifecycle — отдельный слой «поверх»; чистое разделение ответственности. |
| Глубина наследования | Не более 2–3 уровней | Избегать цепочек Planet→Zodiac→…; Agent не наследует NatalChart. |
| Обратная совместимость | replay_v2, run_step_v2, assembler, modulation остаются | Новые классы — фасад/оркестрация; старый API для скриптов и тестов. |

## Alternatives Considered

- **Mixin для Lifecycle (ResearchAgent, LifecycleMixin)**: отклонён. При расширении (AgeEngine, MemoryDrift и т.д.) наследование от миксинов даёт хаос. Фиксируем только композицию: Agent с опциональным `lifecycle: LifecycleEngine | None`.
- **Planet наследует Zodiac**: отклонено — планета не «является» знаком; знак вычисляется из долготы, отдельный слой ZodiacExpression.
- **Единый класс «Chart» с планетами + знаками + домами**: разбито на NatalChart (астрономия) и ZodiacExpression (интерпретация), чтобы сохранить read-only вид и одностороннюю зависимость.
- **Lifecycle как часть step() внутри BehavioralCore**: отклонено — смешивание ответственности; lifecycle остаётся отдельным компонентом, вызываемым из Agent.step().

## Open Points

- Окончательное размещение: отдельный пакет `hnh/astronomy/` для Planet/Aspect/NatalChart или всё в `hnh/astrology/` — решается в T001–T003 по минимальным изменениям импортов.
- Имя модуля BehavioralCore: `hnh/behavior/core.py` vs `hnh/state/behavioral_core.py` — по соглашению проекта (plan § Target Package Layout).
