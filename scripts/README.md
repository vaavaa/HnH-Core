# Примеры использования HnH

Скрипты в этой папке показывают, как пользоваться библиотекой HnH из Python.

**Требование:** запускать из **корня проекта** с активированным venv. Если пакет установлен (`pip install -e .`), достаточно:

```bash
cd /path/to/core
source .venv/bin/activate
python scripts/01_basic_step.py
```

Если пакет не установлен: `PYTHONPATH=. python scripts/01_basic_step.py`

| Скрипт | Описание |
|--------|----------|
| [01_basic_step.py](01_basic_step.py) | Один шаг симуляции на дату, вывод вектора и модификаторов |
| [02_replay_and_log.py](02_replay_and_log.py) | Шаг → запись в лог (JSON Lines) → replay и проверка совпадения |
| [03_relational_memory.py](03_relational_memory.py) | Relational Memory: события, модификатор, шаг с учётом памяти |
| [04_teacher_pilot.py](04_teacher_pilot.py) | Planetary Teacher: создание, пилотный прогон по диапазону дат |
| [05_multiple_dates_jsonl.py](05_multiple_dates_jsonl.py) | Несколько дат подряд, вывод в формате JSON Lines |

**Скрипты 002 (модель 8×4, 32 параметра):** в подпапке [002/](002/) — восемь демо: схема и IdentityCore v0.2, чувствительность, границы дельт, сборка состояния, память v2, логирование orjson, replay v2, полный шаг. См. [002/README.md](002/README.md).

Подробнее — в [user-guide-readme.md](../user-guide-readme.md).  
**English:** [README.en.md](README.en.md) and [en-user-guide-readme.md](../en-user-guide-readme.md).
