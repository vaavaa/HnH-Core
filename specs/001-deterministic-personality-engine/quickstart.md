# Quickstart: 001 Deterministic Personality Engine

**Feature**: 001-deterministic-personality-engine  
**Purpose**: Минимальный сценарий проверки движка без LLM и внешних API.  

---

## Prerequisites

- Python 3.12+
- Установленные зависимости (pydantic, pytest; опционально pyswisseph после реализации слоя astrology).

---

## Validation Scenarios (from spec)

После реализации выполнить по порядку:

### 1. Identity Core

- Создать Identity Core с фиксированными `identity_id`, `base_traits` (семь размерностей в [0, 1]).
- Получить `base_behavior_vector` и `identity_hash`.
- Создать второй Core с теми же входами — вектор должен совпадать; Core сериализуем и hashable.
- Попытка создать Core с тем же `identity_id` и другими полями → ошибка (already exists).
- Передать значение вне [0, 1] в base_traits → ошибка (reject).

### 2. Dynamic State

- Вызвать вычисление Dynamic State с заданными Identity Core, seed, временем (injected), опционально Relational Memory.
- Проверить: выход содержит modified behavioral vector, active modifiers, state snapshot; Identity Core не изменился.
- Два вызова с одинаковыми входами → идентичный вывод.

### 3. Logging

- Выполнить один шаг симуляции.
- Убедиться: одна запись в логе; поля seed, injected_time, identity_hash, active_modifiers, final_behavioral_vector присутствуют; формат одна строка — один JSON (JSON Lines); лог diffable.

### 4. Replay

- Запустить replay с теми же seed, time, identity, relational snapshot.
- Сравнить вывод с оригинальным запуском — должен совпадать.
- Убедиться, что в ядре не используется system clock.

### 5. Relational Memory (v0.1)

- Создать память для user_id; добавить события (sequence, type, payload) по детерминированным правилам.
- Передать снапшот в Dynamic State; проверить, что Identity Core не мутируется и результат детерминирован при том же снапшоте.

---

## Success Criteria (spec SC-001 – SC-007)

- [ ] Движок работает без LLM и внешних API.
- [ ] Одинаковые seed + time + identity + memory → одинаковое поведение (автотесты).
- [ ] Все переходы состояния логируются в структурированном, diffable формате.
- [ ] Replay воспроизводит идентичный вывод; без системных часов в ядре.
- [ ] Все тесты зелёные; покрытие ядра 90%+.
- [ ] Чеклист конституции (Identity immutable, Dynamic State deterministic, seed/time, logging, replay, no LLM, contracts documented) выполнен.
