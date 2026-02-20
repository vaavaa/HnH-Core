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

Примеры:

- **run_agent_demo.py** — построение Agent (product/research), шаги по датам, сравнение с replay_v2.
- **life_simulation_102y.py** — симуляция многих жизней: случайные даты рождения (от Р.Х. до сегодня), Лондон, 70–108 лет на жизнь, два расчёта в день (утро/вечер UTC); вывод дельт осей и натального/транзитного зодиака (аналог scripts/004/09_life_simulation_102y.py на логике 006).

  ```bash
  python scripts/006/life_simulation_102y.py
  python scripts/006/life_simulation_102y.py --lives 50 --seed 42
  python scripts/006/life_simulation_102y.py --lives 5 --days 365   # быстрый тест
  ```

## Ссылки

- Spec: [specs/006-layered-agent-architecture/spec.md](../../specs/006-layered-agent-architecture/spec.md)
- Plan: [specs/006-layered-agent-architecture/plan.md](../../specs/006-layered-agent-architecture/plan.md)
- Quickstart: [specs/006-layered-agent-architecture/quickstart.md](../../specs/006-layered-agent-architecture/quickstart.md)
