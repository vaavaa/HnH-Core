# Руководство пользователя: HnH через CLI

Как установить движок и пользоваться им из командной строки.

---

## Что это такое

**HnH** — детерминированный движок «личности»: по заданной дате он выдаёт **поведенческий вектор** (32 параметра, 8 осей) и при необходимости — состояние **lifecycle** (F, W, state). Используется **слоёная архитектура** (спека 006): натал, поведение 32D, транзиты, опционально lifecycle. **Канонический путь** — один шаг через **Agent.step(date)**. Всё воспроизводимо; в ядре нет обращения к системному времени.

Через **CLI** вы запускаете симуляцию на одну дату: команда **`hnh agent step`** (006) — основной способ; **`run-v2`** (002) и **`run`** (001) сохранены для совместимости. Скрипты в **`scripts/006/`** и **`scripts/002/`** показывают использование Agent и replay.

---

## Установка

Нужен **Python 3.12+**.

```bash
# Клонируйте репозиторий и перейдите в каталог проекта
cd /path/to/core

# Создайте виртуальное окружение и установите пакет
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# или:  .venv\Scripts\activate   # Windows

pip install -e .
```

Команда `hnh` будет доступна в этом окружении.

**Опционально (астрологический слой — натал/транзиты):**

```bash
pip install -e ".[astrology]"
```

Без этой опции движок работает с одним фиксированным базовым вектором; с ней можно подставлять натальную карту и транзиты (если позже добавите их в CLI).

---

## Запуск CLI

### Обязательный аргумент: дата

Дата задаётся в формате **YYYY-MM-DD** (UTC noon). Она «впрыскивается»: движок не смотрит на системные часы.

**Команды:** **`hnh agent step`** (006 — канонический путь, 32 параметра), **`hnh run-v2`** (002), **`hnh run`** (001). Справка: `hnh --help`, `hnh agent step --help`.

### Каноническая команда 006: agent step

Один шаг через **Agent.step(date)** — слои натал, поведение, транзиты (и при `--lifecycle` — lifecycle).

```bash
hnh agent step --date 2024-06-15
```

**Пример вывода:**

```
params_final (32): [0.58, 0.51, ...]
axis_final (8): [0.53, 0.5, ...]
```

С **research-режимом** (lifecycle: усталость F, воля W, состояние ALIVE/DISABLED/TRANSCENDED):

```bash
hnh agent step --date 2024-06-15 --lifecycle
```

Дополнительно выводятся: `lifecycle F: ... W: ... state: ...`

- **params_final** (32) и **axis_final** (8) — поведенческий вектор и агрегаты по осям, все значения 0.0–1.0.
- **run-v2** делегирует в Agent при простом пути (без phase/history); **run** — модель 001 (7 параметров).

---

### Вывод одной строкой JSON

Удобно для скриптов и логов:

```bash
hnh agent step --date 2024-01-10 --json
```

Пример (без lifecycle):

```json
{"axis_final": [...], "injected_time_utc": "2024-01-10T12:00:00+00:00", "params_final": [...]}
```

С `--lifecycle` в JSON добавляются поля `lifecycle_F`, `lifecycle_W`, `lifecycle_state`.

---

### Seed (воспроизводимость)

По умолчанию используется seed **0**. Его можно задать явно:

```bash
hnh run --date 2024-03-20 --seed 42
```

Одинаковые `--date` и `--seed` всегда дают один и тот же результат.

---

### Проверка воспроизводимости (replay)

Флаг **--replay** запускает расчёт дважды с теми же параметрами и проверяет совпадение вывода:

```bash
hnh agent step --date 2024-05-01 --replay
```

При успехе: `Replay OK: identical output.` При расхождении — код выхода 1.

---

## Слои 006 и модель 32 параметра

В архитектуре **006** один шаг выполняется через **Agent**: натал (NatalChart) → поведение (BehavioralCore, 32D) → транзиты (TransitEngine) → опционально lifecycle (LifecycleEngine). Команда **`hnh agent step`** вызывает ровно это. Модель поведения — **иерархическая 8×4**: 8 осей, по 4 подпараметра (всего 32), значения **0.0–1.0**.

| Ось | Подпараметры |
|-----|----------------|
| **1 — Emotional Tone** | warmth, empathy, patience, emotional_intensity |
| **2 — Stability & Regulation** | stability, reactivity, resilience, stress_response |
| **3 — Cognitive Style** | analytical_depth, abstraction_level, detail_orientation, big_picture_focus |
| **4 — Structure & Discipline** | structure_preference, consistency, rule_adherence, planning_bias |
| **5 — Communication Style** | verbosity, directness, questioning_frequency, explanation_bias |
| **6 — Teaching Style** | correction_intensity, challenge_level, encouragement_level, pacing |
| **7 — Power & Boundaries** | authority_presence, dominance, tolerance_for_errors, conflict_tolerance |
| **8 — Motivation & Drive** | ambition, curiosity, initiative, persistence |

Итог по дате: **params_final** (32 числа) и **axis_final** (8 агрегатов — среднее по 4 подпараметрам оси). Демо — в `scripts/002/`, см. раздел ниже.

*(Режим 001: семь параметров — warmth, strictness, verbosity, correction_rate, humor_level, challenge_intensity, pacing; используется в CLI и в `scripts/01_*` … `05_*`.)*

---

## Примеры команд

```bash
# Канонический шаг 006 (рекомендуется)
hnh agent step --date 2024-06-15

# С lifecycle (research) и вывод в JSON
hnh agent step --date 2024-06-15 --lifecycle --json

# Проверка воспроизводимости
hnh agent step --date 2024-06-15 --replay

# Режим 002 (run-v2 делегирует в Agent при простом пути)
hnh run-v2 --date 2024-06-15

# Режим 001 (7 параметров)
hnh run --date 2024-06-15

# Неверная дата — ошибка
hnh agent step --date 2024-13-01
# Invalid --date: ... Use YYYY-MM-DD.
```

---

## Примеры в папке `scripts/`

В репозитории есть папка **`scripts/`** с готовыми примерами использования библиотеки. Запускать из **корня проекта** с активированным виртуальным окружением:

```bash
cd /path/to/core
source .venv/bin/activate
pip install -e .   # один раз
python scripts/01_basic_step.py
```

Если пакет не установлен в venv, можно запускать так: `PYTHONPATH=. python scripts/01_basic_step.py`.

| Скрипт | Что делает |
|--------|------------|
| **01_basic_step.py** | Один шаг симуляции на дату: создаётся Identity, вызывается `run_step`, печатаются вектор и модификаторы. Можно передать дату аргументом: `python scripts/01_basic_step.py 2024-09-01`. |
| **02_replay_and_log.py** | Один шаг → запись перехода в файл (JSON Lines) → повторный прогон (replay) → проверка, что результат совпадает. По умолчанию пишет в `state.log`; можно указать `--out other.log`, `--date 2024-07-01`, `--seed 42`. |
| **03_relational_memory.py** | Relational Memory: создаётся память пользователя, добавляются события (interaction, error), из них считается модификатор; шаг симуляции вызывается с `relational_snapshot=modifier`. Показывает производные метрики и итоговый вектор. |
| **04_teacher_pilot.py** | Planetary Teacher: создаётся «учитель» с датой рождения и координатами, затем `pilot_run` по диапазону дат (по умолчанию 7 дней). Опции: `--days 14`, `--start 2024-09-01`. |
| **05_multiple_dates_jsonl.py** | Симуляция по нескольким датам подряд; на каждую дату — одна строка JSON (JSON Lines). Запуск: `python scripts/05_multiple_dates_jsonl.py 2024-01-01 2024-01-07`. Вывод можно перенаправить в файл: `... > january.jsonl`. |

Краткое описание скриптов есть также в [scripts/README.md](scripts/README.md).

---

## Примеры 002 — иерархическая модель 8×4 (32 параметра)

В папке **`scripts/002/`** — восемь скриптов по спецификации 002: схема 8 осей × 4 подпараметра (32 параметра), чувствительность из натала, границы дельт, сборка состояния, память v2, логирование orjson, replay с допуском 1e-9.

```bash
python scripts/002/01_schema_and_identity.py
python scripts/002/08_full_step_v2.py --date 2025-03-01 --log
```

| Скрипт | Что делает |
|--------|------------|
| **01_schema_and_identity.py** | Реестр 8 осей и 32 параметров, маппинг индексов, IdentityCore v0.2 (base_vector, sensitivity_vector). |
| **02_sensitivity.py** | Вычисление чувствительности из натала (`compute_sensitivity`), гистограмма для отладки. |
| **03_raw_delta_and_bounds.py** | raw_delta из аспектов, ReplayConfig, apply_bounds (иерархия parameter > axis > global, шок). |
| **04_state_assembly.py** | Сборка состояния: base + bounded×sensitivity + memory → params_final (32), axis_final (8). |
| **05_memory_v2.py** | Relational Memory v2: get_memory_delta_32, memory_signature. |
| **06_logging_v2.py** | Лог v2 (orjson): build_record_v2, write_record_v2. Опции: `--out 002_demo.log`, `--date 2025-02-18`. |
| **07_replay_v2.py** | Replay v2: N прогонов с одинаковыми входами, replay_match (1e-9), replay_output_hash. |
| **08_full_step_v2.py** | Полный шаг: identity + config + время + память → ReplayResult. Опции: `--date`, `--log`. |

Подробнее — в [scripts/002/README.md](scripts/002/README.md) и в [specs/002-hierarchical-personality-model/](specs/002-hierarchical-personality-model/).

### Скрипты 006 — Agent и слои

В **`scripts/006/`** — демо слоёной архитектуры: построение Agent (product и research), вызов `step()` по датам, сравнение с replay_v2.

```bash
python scripts/006/run_agent_demo.py
```

См. [scripts/006/README.md](scripts/006/README.md).

---

## Использование как библиотеки

**Канонический путь (006)** — **Agent.step(date)**. CLI команда `hnh agent step` вызывает именно его.

Из Python:

- **Agent** — единственная точка оркестрации шага: натал, поведение 32D, транзиты, опционально lifecycle (`hnh.agent.Agent`);
- **run_step_v2** при простом пути делегирует в Agent.step(); для phase/history и memory_delta используется прежняя реализация;
- логи v2 — **state_logger_v2** (orjson); **Planetary Teacher** и **LLM-адаптер** — `hnh.interface`.

Минимальный пример (006):

```python
from datetime import date
from hnh.agent import Agent
from hnh.config.replay_config import ReplayConfig

birth_data = {"positions": [{"planet": "Sun", "longitude": 90.0}, {"planet": "Moon", "longitude": 120.0}]}
config = ReplayConfig(global_max_delta=0.08, shock_threshold=0.5, shock_multiplier=1.0)
agent = Agent(birth_data, config=config, lifecycle=False)
agent.step(date(2025, 2, 18))
print("params_final (32):", agent.behavior.current_vector[:8], "...")
# axis_final = aggregate_axis(agent.behavior.current_vector); TransitState = agent.transits.state(d, config)
```

С lifecycle (research): `Agent(..., lifecycle=True)`; после шага доступны `agent.lifecycle.F`, `agent.lifecycle.W`, `agent.lifecycle.state`. Подробнее — в **`scripts/006/`** и **`specs/006-layered-agent-architecture/`**.

---

## Дополнительно

- **English version of this guide:** [en-user-guide-readme.md](en-user-guide-readme.md)
- **Полное описание проекта:** [README.md](README.md)
- **Спека 006 (слоёная архитектура, Agent):** [specs/006-layered-agent-architecture/](specs/006-layered-agent-architecture/)
- **Спека 002 (8×4 модель):** [specs/002-hierarchical-personality-model/](specs/002-hierarchical-personality-model/)
- **Скрипты 006:** [scripts/006/README.md](scripts/006/README.md)
- **Контракт лога переходов:** [specs/001-deterministic-personality-engine/contracts/state-log-spec.md](specs/001-deterministic-personality-engine/contracts/state-log-spec.md)
