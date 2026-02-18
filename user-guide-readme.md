# Руководство пользователя: HnH через CLI

Как установить движок и пользоваться им из командной строки.

---

## Что это такое

**HnH** — детерминированный движок «личности»: по заданной дате и сиду он выдаёт **поведенческий вектор** и **активные модификаторы**. В этой ветке (спека 002) используется **иерархическая модель 8×4**: **32 параметра** (8 осей по 4 подпараметра), все значения от 0 до 1, плюс агрегаты по осям (`axis_final`). Всё воспроизводимо: одни и те же входы дают один и тот же результат. В ядре нет обращения к системному времени и случайности без явного seed.

Через **CLI** (режим 001) или скрипты в **`scripts/002/`** вы запускаете симуляцию на одну дату и смотрите результат в консоли или в виде одной строки JSON.

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

Дата задаётся в формате **YYYY-MM-DD**. Она считается «впрыснутой»: движок не смотрит на системные часы.

```bash
hnh --date 2024-06-15
```

**Пример вывода (CLI, режим 001 — 7 параметров):**

```
final_behavioral_vector: {'warmth': 0.5, 'strictness': 0.4, 'verbosity': 0.6, 'correction_rate': 0.3, 'humor_level': 0.5, 'challenge_intensity': 0.4, 'pacing': 0.5}
active_modifiers: {'transit_delta': {'warmth': 0.0, 'strictness': 0.0, ...}, ...}
```

Для вывода **32 параметров** (params_final, axis_final) используйте скрипты в `scripts/002/`.

- **final_behavioral_vector** (режим 001) — семь параметров; в модели 002 вывод — **params_final** (32) и **axis_final** (8), все в диапазоне 0.0–1.0.
- **active_modifiers** — чем «подправлен» базовый вектор (transit_delta, relational и т.д.).

---

### Вывод одной строкой JSON

Удобно для скриптов и логов:

```bash
hnh --date 2024-01-10 --json
```

Пример:

```json
{"active_modifiers": {...}, "final_behavioral_vector": {...}, "identity_hash": "...", "injected_time": "2024-01-10T12:00:00+00:00"}
```

---

### Seed (воспроизводимость)

По умолчанию используется seed **0**. Его можно задать явно:

```bash
hnh --date 2024-03-20 --seed 42
```

Одинаковые `--date` и `--seed` всегда дают один и тот же результат.

---

### Проверка воспроизводимости (replay)

Флаг **--replay** запускает расчёт дважды с теми же параметрами и проверяет, что вывод совпадает:

```bash
hnh --date 2024-05-01 --replay
```

Если всё ок, вы увидите: `Replay OK: identical output.`  
Если вывод различается, команда завершится с ошибкой (код выхода 1).

С JSON:

```bash
hnh --date 2024-05-01 --replay --json
```

При успехе выведется та же одна строка JSON (дважды не печатается, только проверка).

---

## 32 параметра (8 осей × 4) — модель 002

В этой ветке основная модель — **иерархическая 8×4**: 8 осей, у каждой по 4 подпараметра (всего 32), значения от **0.0** до **1.0**.

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
# Симуляция на 15 июня 2024, вывод в консоль
hnh --date 2024-06-15

# То же, но одна строка JSON
hnh --date 2024-06-15 --json

# Другой seed
hnh --date 2024-06-15 --seed 123

# Проверить, что два прогона дают одинаковый результат
hnh --date 2024-06-15 --replay

# Неверная дата — ошибка и подсказка
hnh --date 2024-13-01
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

---

## Использование как библиотеки

CLI — обёртка над движком. Из Python можно:

- создавать **Identity Core** (v0.2: 32 параметра — `hnh.identity.IdentityCore` с `base_vector`, `sensitivity_vector`);
- вызывать **run_step_v2(identity, config, injected_time, memory_delta=..., memory_signature=...)** и получать **ReplayResult** (params_final, axis_final и подпись replay);
- писать логи v2 через **state_logger_v2** (orjson);
- использовать **Planetary Teacher** и **LLM-адаптер** (см. `hnh.interface`).

Пример минимального шага по модели 002 (32 параметра):

```python
from datetime import datetime, timezone
from hnh.identity import IdentityCore
from hnh.config.replay_config import ReplayConfig
from hnh.state.replay_v2 import run_step_v2

identity = IdentityCore(
    identity_id="my-id",
    base_vector=(0.5,) * 32,
    sensitivity_vector=(0.5,) * 32,
)
config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)
result = run_step_v2(identity, config, datetime(2025, 2, 18, 12, 0, 0, tzinfo=timezone.utc))
print("params_final (32):", result.params_final[:8], "...")
print("axis_final (8):", result.axis_final)
```

Подробнее — в `scripts/002/` и в `specs/002-hierarchical-personality-model/`. Режим 001 (7 параметров): `hnh.core.identity`, `hnh.state.replay.run_step`.

---

## Дополнительно

- **English version of this guide:** [en-user-guide-readme.md](en-user-guide-readme.md)
- **Полное описание проекта и идеи:** [README.md](README.md)
- **Спека и план движка (001):** [specs/001-deterministic-personality-engine/](specs/001-deterministic-personality-engine/)
- **Спека 002 (8×4 модель):** [specs/002-hierarchical-personality-model/](specs/002-hierarchical-personality-model/)
- **Контракт лога переходов:** [specs/001-deterministic-personality-engine/contracts/state-log-spec.md](specs/001-deterministic-personality-engine/contracts/state-log-spec.md)

Если что-то из CLI непонятно или хочется расширить сценарии (например, свой identity из файла, запись лога в файл) — можно описать это в отдельном тикете или в новой спеку.
