# Research: 003 — Performance Optimization

Решения по инструментам и границам уже зафиксированы в [spec.md](spec.md) (Clarifications). Здесь — сводка и обоснование.

---

## 1. JSON: orjson

**Decision**: В пакете `hnh/` для сериализации/десериализации JSON использовать только **orjson**.

**Rationale**: orjson быстрее stdlib json на порядок в типичных сценариях; уже используется в 002 (state_logger_v2, replay_v2, identity). Единый контракт и предсказуемая производительность.

**Alternatives considered**: stdlib `json` — отказ в core path. ujson/simdjson — не выбраны; orjson уже в проекте и достаточен.

---

## 2. Хеширование: xxhash

**Decision**: Все хеши в `hnh/` (identity_hash, configuration_hash, memory_signature, transit_signature, replay signature) считать через **xxhash** (xxh3_128 или xxh64).

**Rationale**: xxhash быстрее hashlib (SHA-256) при достаточной криптостойкости не требуется; детерминизм сохраняется при каноническом вводе (orjson OPT_SORT_KEYS). Уже используется в identity.py.

**Alternatives considered**: hashlib — оставлен только для миграции; после 003 в core не используется. SHA-256 — избыточен для внутренних подписей/идентификации в данном контексте.

---

## 3. Циклы и NumPy

**Decision**: В горячих путях — вынос инвариантов, предвыделение, comprehensions; при наличии NumPy — векторизация где не ломает детерминизм. **NumPy — опциональная зависимость**.

**Rationale**: Спека 003 не обязывает добавлять NumPy в обязательные зависимости; окружения без NumPy должны работать (чистый Python). Где NumPy есть — используем для ускорения.

**Alternatives considered**: Обязательный NumPy — отклонён (расширяет обязательные зависимости). Только чистый Python без векторизации — принят как fallback.

---

## 4. Граница core / CLI (T004)

**Decision**: CLI тоже переводим на **orjson**. Вывод в stdout: `orjson.dumps(..., option=orjson.OPT_SORT_KEYS).decode("utf-8")` — единообразие в рамках пакета `hnh/`, без исключений.

**Rationale**: Спека 003 — orjson везде в `hnh/`; явных исключений не вводим; тесты проще (один контракт).

---

## 5. Аудит (файлы для миграции)

По текущему состоянию репозитория:

| Файл | json | hashlib | Действие |
|------|------|---------|----------|
| hnh/core/identity.py | — | — | Уже orjson+xxhash |
| hnh/logging/state_logger_v2.py | — | — | Уже orjson |
| hnh/state/replay_v2.py | — | да | Заменить hashlib → xxhash |
| hnh/cli.py | да | — | Заменить json → orjson (или исключение для stdout) |
| hnh/memory/relational.py | да | да | orjson + xxhash |
| hnh/config/replay_config.py | да | да | orjson + xxhash |
| hnh/identity/schema.py | да | да | orjson + xxhash |
| hnh/logging/state_logger.py | да | да | orjson + xxhash (или пометить legacy и не использовать в core path) |

Базовый прогон бенчмарка (T003/T023): из корня `PYTHONPATH=. python scripts/benchmark_002.py`. Референс после 003: T9.1 orjson ~7.9× быстрее json; T9.2 run_step_v2 ~35k steps/s. Критерий приёмки: при последующих изменениях T9.2 не должен замедляться (ручная проверка или CI).
