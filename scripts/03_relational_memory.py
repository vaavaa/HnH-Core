#!/usr/bin/env python3
"""
Пример: Relational Memory — события по пользователю, модификатор из истории, шаг с учётом памяти.

Создаём память пользователя, добавляем события (взаимодействия, ошибки),
получаем поведенческий модификатор и передаём его в run_step как relational_snapshot.

Запуск из корня проекта:
  python scripts/03_relational_memory.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from hnh.core.identity import IdentityCore
from hnh.core.parameters import BehavioralVector
from hnh.memory.relational import RelationalMemory
from hnh.state.replay import run_step


def main() -> None:
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.4,
        verbosity=0.6,
        correction_rate=0.3,
        humor_level=0.5,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    identity = IdentityCore(
        identity_id="script-03-rel",
        base_traits=base,
        symbolic_input=None,
    )

    # Память пользователя: добавляем события
    memory = RelationalMemory("user-alice")
    memory.add_event(1, "interaction", {"topic": "math"})
    memory.add_event(2, "interaction", {"topic": "math"})
    memory.add_event(3, "error", {"type": "timeout"})

    modifier = memory.get_behavioral_modifier()
    print("Модификатор из истории (7 размерностей):", modifier)
    print("Производные метрики:", memory.derived_metrics())

    # Шаг симуляции с учётом relational snapshot
    dt = datetime(2024, 8, 10, 12, 0, 0, tzinfo=timezone.utc)
    state = run_step(identity, dt, seed=0, relational_snapshot=modifier)

    print("\nИтоговый вектор (база + транзит + relational):", state.final_behavior_vector.to_dict())
    print("Активные модификаторы (transit_delta + relational):", state.active_modifiers.keys())


if __name__ == "__main__":
    main()
