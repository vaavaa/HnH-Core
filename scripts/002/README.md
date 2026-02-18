# Примеры 002 — иерархическая модель 8×4 (32 параметра)

Скрипты демонстрируют функционал спецификации 002: схема 8 осей × 4 параметра, чувствительность из натала, границы дельт, сборка состояния, память v2, логирование orjson, replay с допуском 1e-9.

**Запуск:** из корня проекта с активированным venv:

```bash
cd /path/to/core
source .venv/bin/activate
python scripts/002/01_schema_and_identity.py
```

При необходимости: `pip install -e .` и опционально `pip install -e ".[astrology]"`.

| Скрипт | Описание |
|--------|----------|
| [01_schema_and_identity.py](01_schema_and_identity.py) | Реестр 8 осей и 32 параметров, маппинг индексов, IdentityCore v0.2 (base_vector, sensitivity_vector) |
| [02_sensitivity.py](02_sensitivity.py) | Вычисление чувствительности из натала (compute_sensitivity), гистограмма для отладки |
| [03_raw_delta_and_bounds.py](03_raw_delta_and_bounds.py) | raw_delta из аспектов, ReplayConfig, apply_bounds (иерархия, шок) |
| [04_state_assembly.py](04_state_assembly.py) | Сборка состояния: base + bounded×sensitivity + memory → params_final, axis_final |
| [05_memory_v2.py](05_memory_v2.py) | Relational Memory: get_memory_delta_32, memory_signature |
| [06_logging_v2.py](06_logging_v2.py) | Лог v2 (orjson): build_record_v2, write_record_v2. Опции: `--out 002_demo.log`, `--date 2025-02-18` |
| [07_replay_v2.py](07_replay_v2.py) | Replay v2: N прогонов с одинаковыми входами, replay_match (1e-9), replay_output_hash |
| [08_full_step_v2.py](08_full_step_v2.py) | Полный шаг: identity + config + время + память → ReplayResult. Опции: `--date`, `--log` |

Спека: [specs/002-hierarchical-personality-model/](../specs/002-hierarchical-personality-model/).
