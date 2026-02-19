# Implementation Plan: 003 — Performance Optimization

**Branch**: `003-performance-optimization` | **Date**: 2025-02-19 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/003-performance-optimization/spec.md`

---

## Summary

Унификация производительности в пакете `hnh/`: (1) замена всех использований stdlib `json` на **orjson**; (2) замена всех использований **hashlib** на **xxhash** (одномоментный breaking change, контракт 002+); (3) применение правил оптимизации циклов (векторизация при наличии NumPy, вынос инвариантов, предвыделение). Обязательный критерий приёмки — отсутствие регрессии на референсном бенчмарке (например, `scripts/benchmark_002.py`). Cursor rule уже создан; новые сущности и API не вводятся.

---

## Technical Context

**Language/Version**: Python 3.12 (pyproject.toml)  
**Primary Dependencies**: orjson, xxhash, pydantic, structlog (уже в проекте); NumPy опционален  
**Storage**: N/A (только локальные файлы для логов/реплея)  
**Testing**: pytest, pytest-cov; референсный бенчмарк — `scripts/benchmark_002.py`  
**Target Platform**: Linux (текущий CI/разработка)  
**Project Type**: single (пакет `hnh/`, CLI, тесты)  
**Performance Goals**: orjson/xxhash везде в `hnh/`; один измеримый критерий — нет регрессии на benchmark_002  
**Constraints**: Детерминизм сохраняется; формат логов orjson (OPT_SORT_KEYS) не меняется; значения хешей меняются (breaking, версия 002+)  
**Scale/Scope**: Весь пакет `hnh/` (core, state, modulation, logging, memory, config, identity, interface, cli)

---

## Constitution Check

*GATE: Must pass before Phase 0. Re-check after Phase 1.*

- [x] **Deterministic Mode**: Оптимизация не вносит недетерминизма; seed/time инъекция и логирование без изменений; replay остаётся детерминированным (хеши считаются по xxhash детерминированно).
- [x] **Identity/Core separation**: Без изменений; замена hashlib→xxhash не меняет инварианты Identity/Dynamic State/Memory.
- [x] **Minimal Reference Implementation**: Не блокируется; логирование и replay по-прежнему через orjson и структурированный лог.
- [x] **Behavioral Parameterization**: Без изменений.
- [x] **Logging & Observability**: orjson и обязательные поля лога сохраняются; хеши переходят на xxhash (новые значения).
- [x] **Repository Standards**: Один язык, один форматтер/линтер/тесты; контракт «hnh/ без json/hashlib» проверяется тестами.

---

## Project Structure

### Documentation (this feature)

```text
specs/003-performance-optimization/
├── plan.md              # Этот файл
├── research.md          # Решения по инструментам (orjson, xxhash)
├── data-model.md        # Без новых сущностей (миграция только)
├── quickstart.md        # Как проверить соблюдение и бенчмарк
└── tasks.md             # Создаётся /speckit.tasks
```

### Source Code (repository root)

Существующая структура без изменений:

```text
hnh/
├── core/           # identity.py — уже orjson+xxhash
├── state/          # replay_v2.py — orjson есть, hashlib заменить на xxhash
├── modulation/
├── logging/        # state_logger_v2.py — orjson; state_logger.py — мигрировать или пометить legacy
├── memory/         # relational.py — json+hashlib → orjson+xxhash
├── config/         # replay_config.py — json+hashlib → orjson+xxhash
├── identity/       # schema.py — json+hashlib → orjson+xxhash
├── interface/
└── cli.py          # json.dumps для вывода → orjson (или оставить json только для CLI вывода — уточнить в задачах)
```

**Уточнение по CLI**: В спеке core = весь `hnh/`, значит `cli.py` входит. Вывод в stdout для человека (pretty-print) можно оставить через stdlib json для читаемости либо перевести на orjson с `.decode()`. Решение — в задачах (единообразие vs удобство отладки).

---

## Phases & Milestones

---

### Phase 0 — Аудит и базовый прогон

**Цель**: Зафиксировать текущее состояние и референсный бенчмарк.

- Перечень всех вхождений `import json`, `json.dumps`, `json.loads` в `hnh/`.
- Перечень всех вхождений `import hashlib` и вызовов hashlib в `hnh/`.
- Прогон `scripts/benchmark_002.py` (или аналога), сохранение базовых метрик (время/итерации) как референс для «без регрессии».
- **Выход**: `research.md` с перечнем файлов для миграции и решением по CLI; запись базовых метрик бенчмарка.

---

### Milestone 1 — orjson везде в hnh/

**Deliverables**

- Замена `json` на `orjson` во всех модулях пакета `hnh/`, где выполняется сериализация/десериализация в core path.
- Кандидаты (по текущему grep): `hnh/cli.py`, `hnh/memory/relational.py`, `hnh/config/replay_config.py`, `hnh/identity/schema.py`, `hnh/logging/state_logger.py` (если ещё используется).
- Для детерминизма везде, где нужен стабильный вывод: `orjson.dumps(..., option=orjson.OPT_SORT_KEYS)`.

**Requirements**

- В `hnh/` не остаётся `import json` и вызовов `json.dumps`/`json.loads` в путях, влияющих на логи/replay/хеши (допустимое исключение: только CLI human-readable вывод, если зафиксировано в задачах).
- Формат логов и replay (OPT_SORT_KEYS) сохраняется.

**Tests**

- Автотест или скрипт: в коде под `hnh/` нет `import json` (или только в разрешённых местах); нет вызовов `json.dumps`/`json.loads` в core path.

---

### Milestone 2 — xxhash везде в hnh/

**Deliverables**

- Замена hashlib на xxhash для всех хешей в `hnh/`: identity_hash (уже xxhash в identity.py), configuration_hash, memory_signature, transit_signature, replay signature и т.д.
- Кандидаты: `hnh/state/replay_v2.py`, `hnh/memory/relational.py`, `hnh/config/replay_config.py`, `hnh/identity/schema.py`, `hnh/logging/state_logger.py`.
- Вход для детерминированного хеша от структуры: `orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)` затем `xxhash.xxh3_128(blob, seed=...).hexdigest()` (или xxh64 по необходимости).

**Requirements**

- Одномоментный breaking change: старые значения хешей не поддерживаются; контракт 002+.
- Все хеши в `hnh/` считаются через xxhash.

**Tests**

- Тесты идентичности и replay проходят с новыми хешами.
- В `hnh/` нет `import hashlib` (или явно помечены исключения, если останутся).

---

### Milestone 3 — Оптимизация циклов

**Deliverables**

- Ревью горячих циклов в `hnh/` (state, modulation, memory, assembler и т.д.): вынос инвариантов за цикл, предвыделение/comprehensions, отсутствие orjson.dumps/hash внутри итерации.
- При наличии NumPy в окружении — использование векторизации там, где это не ломает детерминизм; при отсутствии NumPy — оптимизированный чистый Python.

**Requirements**

- FR-P3, FR-P4: циклы по правилам из Cursor rule; NumPy опционален.

**Tests**

- Ревью/чеклист; при необходимости — точечные тесты на детерминизм после рефакторинга.

---

### Milestone 4 — Тесты и приёмка

**Deliverables**

- Постоянный тест: в пакете `hnh/` нет запрещённых `import json` / `json.dumps` / `json.loads` в core path.
- Постоянный тест: ключевые хеши (identity_hash, configuration_hash, memory_signature) считаются через xxhash.
- Прогон референсного бенчмарка: отсутствие регрессии относительно базового прогона (Phase 0).

**Requirements**

- Обязательный критерий приёмки из спеки выполнен (нет регрессии на benchmark_002).
- Cursor rule уже есть (`.cursor/rules/performance-optimization.mdc`); при необходимости обновить под итоговые исключения (например, CLI).

**Tests**

- pytest для запрета json/hashlib в core; интеграционные тесты replay/identity; бенчмарк в CI или ручной прогон с фиксацией результата.

---

## Complexity Tracking

Не требуется: нарушений Constitution нет, план не вводит новых архитектурных решений, только миграция реализации.

---

## Order of Execution

1. Phase 0 — аудит, research.md, базовый бенчмарк.  
2. Milestone 1 — orjson.  
3. Milestone 2 — xxhash.  
4. Milestone 3 — циклы (можно частично параллельно с тестами после M1–M2).  
5. Milestone 4 — тесты и приёмка, обновление rule при необходимости.

После плана: разбить на конкретные задачи через `/speckit.tasks`.
