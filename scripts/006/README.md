# Scripts 006 — Layered Agent Architecture

Слоёная модель и канонический путь оркестрации через **Agent.step()**.

## Слои

| Слой        | Класс / сущность   | Назначение                          |
|------------|---------------------|-------------------------------------|
| Астрономия | Planet, Aspect, NatalChart | Позиции, аспекты, неизменяемая база |
| Zodiac     | ZodiacExpression    | Read-only вид (знаки, элементы)     |
| Поведение  | BehavioralCore      | 32D: base_vector, current_vector    |
| Транзиты   | TransitEngine       | state(date, config) → TransitState  |
| Lifecycle  | LifecycleEngine     | F, W, state (опционально)            |
| Оркестрация| Agent               | step(date): transit → lifecycle → behavior |

## Канонический путь

**Единственная точка оркестрации шага — `Agent.step(date)`.**  
`replay_v2` и `run_step_v2` делегируют в Agent (при простом пути: без phase/history и без memory_delta).

## Использование

- **Product-mode**: `Agent(birth_data, config=..., lifecycle=False)` — только natal + behavior + transits.
- **Research-mode**: `Agent(birth_data, config=..., lifecycle=True)` — плюс LifecycleEngine (F, W, state).

См. пример: `run_agent_demo.py`.

## Ссылки

- Spec: [specs/006-layered-agent-architecture/spec.md](../../specs/006-layered-agent-architecture/spec.md)
- Plan: [specs/006-layered-agent-architecture/plan.md](../../specs/006-layered-agent-architecture/plan.md)
- Quickstart: [specs/006-layered-agent-architecture/quickstart.md](../../specs/006-layered-agent-architecture/quickstart.md)
