# Quickstart: 006 — Layered Agent Architecture

Минимальный путь к использованию слоёной модели и Agent после реализации 006.

## Prerequisites

- Реализованы классы: Planet, Aspect, NatalChart, ZodiacExpression, BehavioralCore, TransitEngine, LifecycleEngine (опционально), Agent.
- Входные данные: birth_data (дата/время/место или готовые позиции), опционально конфиг (ReplayConfig), опционально флаг lifecycle.

## Product-mode (только поведение 32D + транзиты)

```python
from hnh.agent import Agent

birth_data = {...}  # по контракту NatalChart
config = ...         # ReplayConfig или None для дефолтов

agent = Agent(birth_data, config=config, lifecycle=False)

for date in date_range:
    agent.step(date)
    # agent.behavior.current_vector, agent.behavior.base_vector
    # agent.natal, agent.transits.state(date, config) → TransitState(stress, raw_delta, bounded_delta)
```

## Research-mode (с lifecycle)

```python
agent = Agent(birth_data, config=config, lifecycle=True)

for date in date_range:
    agent.step(date)
    # дополнительно: agent.lifecycle.F, agent.lifecycle.W, agent.lifecycle.state (stress берётся из TransitState внутри step)
    # при state DISABLED/TRANSCENDED цикл можно прервать
```

## Низкоуровневый доступ к слоям

- `agent.natal` — NatalChart (planets, aspects)
- `agent.behavior` — BehavioralCore (base_vector, current_vector)
- `agent.transits` — TransitEngine (state(date, config) → TransitState)
- `agent.lifecycle` — LifecycleEngine | None

## Проверка детерминизма

Один и тот же birth_data, config, список дат → одинаковые current_vector (и при lifecycle — F, W, state) после прогона. Интеграционный тест в tests/ сравнивает Agent.step() с replay_v2 на одних и тех же входах.

## References

- Spec: [spec.md](spec.md)
- Plan: [plan.md](plan.md)
- Data model: [data-model.md](data-model.md)
- Contracts: [contracts/layer-responsibilities.md](contracts/layer-responsibilities.md), [contracts/transit-engine.md](contracts/transit-engine.md)
