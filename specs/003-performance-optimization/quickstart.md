# Quickstart: 003 — Performance Optimization

Как проверить соблюдение спеки 003 и критерий приёмки (нет регрессии на бенчмарке).

---

## 1. Проверка: нет stdlib json в core path

Из корня репозитория:

```bash
# Запрещённые вхождения в hnh/ (должны быть пусто или только явные исключения, напр. CLI)
rg 'import json' --glob '*.py' hnh/
rg 'json\.dumps|json\.loads' --glob '*.py' hnh/
```

После миграции оба поиска не должны находить вхождений в core path (или только в разрешённых местах, перечисленных в тестах).

---

## 2. Проверка: хеши через xxhash

```bash
rg 'import hashlib' --glob '*.py' hnh/
```

После миграции не должно быть использований hashlib в `hnh/`. Ключевые хеши (identity_hash, configuration_hash, memory_signature) должны считаться через xxhash (см. тесты и `hnh/core/identity.py` как эталон).

---

## 3. Референсный бенчмарк (критерий приёмки)

```bash
python scripts/benchmark_002.py
```

Зафиксировать вывод (время, итерации). После изменений по 003 прогон повторять; регрессия не допускается (сравнение с базовым прогоном из Phase 0 плана).

При необходимости сохранить базовые метрики в `specs/003-performance-optimization/` или в CI артефактах.

---

## 4. Тесты

```bash
pytest tests/ -v
```

Должны проходить существующие тесты (в т.ч. identity, replay, state_logger_v2). После добавления тестов на запрет json/hashlib в core — они также должны проходить.

---

## 5. Cursor rule

Правила оптимизации: `.cursor/rules/performance-optimization.mdc` (orjson, xxhash, циклы). При изменении исключений (например, CLI) — обновить rule и спеку.
