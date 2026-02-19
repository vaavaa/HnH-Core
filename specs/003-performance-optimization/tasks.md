# Tasks: 003 — Performance Optimization

**Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

---

## Phase 0 — Аудит и базовый прогон

**Purpose**: Зафиксировать текущее состояние и референс для «без регрессии».

- [x] T001 Зафиксировать перечень вхождений `import json`, `json.dumps`, `json.loads` в `hnh/` (например, в research.md или отдельный чеклист).
- [x] T002 Зафиксировать перечень вхождений `import hashlib` и вызовов hashlib в `hnh/`.
- [x] T003 Прогнать `scripts/benchmark_002.py`, сохранить базовые метрики (время/итерации) как референс для критерия приёмки.
- [x] T004 Зафиксировать в research.md или задачах решение по CLI: orjson для stdout или исключение для human-readable вывода.

**Checkpoint**: Аудит готов; базовый бенчмарк зафиксирован.

---

## Phase 1 — User Story 1: orjson везде (P1)

**Goal**: Весь JSON в пакете `hnh/` сериализуется/парсится через orjson; stdlib json не используется в core path.

**Independent Test**: `rg 'import json' hnh/` и `rg 'json\.dumps|json\.loads' hnh/` — пусто (или только разрешённые исключения); тест на orjson в логгере и replay.

- [x] T005 [P] [US1] Заменить json на orjson в `hnh/cli.py` (или зафиксировать исключение для stdout).
- [x] T006 [P] [US1] Заменить json на orjson в `hnh/memory/relational.py`.
- [x] T007 [P] [US1] Заменить json на orjson в `hnh/config/replay_config.py`.
- [x] T008 [P] [US1] Заменить json на orjson в `hnh/identity/schema.py`.
- [x] T009 [US1] Заменить json на orjson в `hnh/logging/state_logger.py` (или пометить legacy и не использовать в core path).
- [x] T010 [US1] Добавить тест/скрипт: в `hnh/` нет запрещённых `import json` и вызовов `json.dumps`/`json.loads` в core path (например, в `tests/`).

**Checkpoint**: User Story 1 выполнена; orjson везде в hnh/ (с явными исключениями при необходимости).

---

## Phase 2 — User Story 2: xxhash везде (P1)

**Goal**: Все хеши в `hnh/` считаются через xxhash; hashlib не используется.

**Independent Test**: `rg 'import hashlib' hnh/` — пусто; тесты identity и replay проходят с новыми хешами.

- [x] T011 [P] [US2] Заменить hashlib на xxhash в `hnh/state/replay_v2.py` (transit_signature, replay signature).
- [x] T012 [P] [US2] Заменить hashlib на xxhash в `hnh/memory/relational.py` (memory_signature).
- [x] T013 [P] [US2] Заменить hashlib на xxhash в `hnh/config/replay_config.py` (configuration_hash).
- [x] T014 [P] [US2] Заменить hashlib на xxhash в `hnh/identity/schema.py` (если там есть хеш).
- [x] T015 [US2] Заменить hashlib на xxhash в `hnh/logging/state_logger.py` (если ещё используется для хешей).
- [x] T016 [US2] Убедиться, что тесты идентичности и replay проходят; при необходимости обновить фикстуры/ожидаемые значения (breaking change 002+).

**Checkpoint**: User Story 2 выполнена; все хеши в hnh/ через xxhash.

---

## Phase 3 — User Story 3: Оптимизация циклов (P2)

**Goal**: Горячие циклы в `hnh/` по правилам: вынос инвариантов, предвыделение/comprehensions; при наличии NumPy — векторизация; без orjson.dumps/hash внутри итерации.

**Independent Test**: Ревью/чеклист; детерминизм сохранён.

- [x] T017 [US3] Ревью циклов в `hnh/state/` (assembler, replay_v2): вынести инварианты, убрать тяжёлые вызовы из цикла.
- [x] T018 [US3] Ревью циклов в `hnh/modulation/` (delta, boundaries): то же.
- [x] T019 [US3] Ревью циклов в `hnh/memory/` и `hnh/logging/`: то же.
- [x] T020 [US3] При наличии NumPy: использовать векторизацию в hot path (state assembly, axis aggregation) без потери детерминизма; при отсутствии — оставить оптимизированный чистый Python.

**Checkpoint**: User Story 3 выполнена; циклы соответствуют правилам из Cursor rule.

---

## Phase 4 — Тесты и приёмка

**Purpose**: Постоянные проверки и обязательный критерий «нет регрессии на бенчмарке».

- [x] T021 Тест: в пакете `hnh/` нет запрещённых `import json` / `json.dumps` / `json.loads` в core path (расширить или добавить в `tests/`).
- [x] T022 Тест: ключевые хеши (identity_hash, configuration_hash, memory_signature) считаются через xxhash (проверка импортов и вызовов).
- [x] T023 Прогнать референсный бенчмарк (`scripts/benchmark_002.py`), убедиться в отсутствии регрессии относительно Phase 0.
- [x] T024 При необходимости обновить `.cursor/rules/performance-optimization.mdc` (например, исключение для CLI stdout).

**Checkpoint**: Все тесты проходят; бенчмарк без регрессии; приёмка 003 выполнена.

---

## Dependencies & Execution Order

- **Phase 0**: Выполнить первым (аудит и базовый бенчмарк).
- **Phase 1 (US1)**: После Phase 0; задачи T005–T009 можно частично параллелить по файлам.
- **Phase 2 (US2)**: После Phase 1 (orjson уже везде — вход для детерминированного хеша).
- **Phase 3 (US3)**: После Phase 2; можно частично параллелить с Phase 4 тестами.
- **Phase 4**: После Phase 1–3; T021–T022 можно добавить раньше (после M1–M2), T023 — после всех миграций.

---

## Definition of Done (003)

- orjson везде в `hnh/` (с явными исключениями при необходимости).
- xxhash везде для хешей в `hnh/`; тесты identity и replay проходят.
- Циклы по правилам (инварианты, предвыделение; при NumPy — векторизация).
- Тесты на запрет json/hashlib в core проходят.
- Нет регрессии на референсном бенчмарке.
