# Примеры 005 — Lifecycle & Entropy (Research Mode)

Скрипты демонстрируют функционал спецификации 005: слой Lifecycle & Entropy поверх модели 32 параметров — усталость F(t), лимит L, фактор активности A_g, психологический возраст, смерть, духовная воля W, трансценденция. Работает только в режиме **research** при `lifecycle_enabled = true`.

**Запуск:** из корня проекта с активированным venv:

```bash
cd /path/to/core
source .venv/bin/activate
python scripts/005/01_lifecycle_formulas_demo.py
```

Для скриптов, использующих транзиты и replay: `pip install -e ".[astrology]"` (как для 002/004).

| Скрипт | Описание |
|--------|----------|
| [01_lifecycle_formulas_demo.py](01_lifecycle_formulas_demo.py) | Демо формул без зависимости от hnh.lifecycle: S_T, load/recovery, F(t+1), L, q, A_g, психовозраст за несколько шагов с фиктивными S_T, R, S_g. Опции: `--days`, `--stress` |
| 02_transit_stress.py | I_T(t), S_T(t) из аспектов по контракту transit-stress; при наличии 002/004 — реальные транзиты. *(После реализации hnh/lifecycle)* |
| 03_fatigue_engine.py | Движок усталости: load, recovery, F, L, q за N дней; вывод траектории F(t), q(t). *(После реализации)* |
| 04_activity_suppression.py | A_g(q), effective_transit_delta и effective_memory_delta, деградация шести параметров. *(После реализации)* |
| 05_death_and_will.py | Условие смерти F >= L, финальный снапшот, delta_W и обновление W при смерти. *(После реализации)* |
| 06_transcendence.py | Порог W >= 0.995, state TRANSCENDED, заморозка профиля. *(После реализации)* |
| 07_lifecycle_replay.py | Полный шаг с lifecycle (research + lifecycle_enabled): подпись реплея, проверка детерминизма. *(После реализации)* |
| 08_life_simulation_lifecycle.py | Симуляция жизни с lifecycle: F, W, A_g, state по дням; при смерти — снапшот. Опции: `--days`, `--lives`, `--seed`, `--no-lifecycle`. *(После реализации)* |

Спека: [specs/005-lifecycle-entropy-research/](../specs/005-lifecycle-entropy-research/).
