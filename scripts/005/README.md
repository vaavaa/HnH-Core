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
| [01_lifecycle_formulas_demo.py](01_lifecycle_formulas_demo.py) | Демо формул: S_T, load/recovery, F, L, q, A_g, психовозраст. Опции: `--days`, `--stress`, `--use-module` |
| [02_transit_stress.py](02_transit_stress.py) | I_T(t), S_T(t) из аспектов (контракт transit-stress); при астрологии — `--date`, `--lat`, `--lon` |
| [03_fatigue_engine.py](03_fatigue_engine.py) | Движок усталости: траектория F(t), q(t) за N дней. Опции: `--days`, `--stress`, `--r`, `--s-g` |
| [04_activity_suppression.py](04_activity_suppression.py) | A_g(q), effective deltas, деградация 6 параметров. Опция `--q` для одного значения |
| [05_death_and_will.py](05_death_and_will.py) | Смерть F >= L, снапшот, delta_W. Опции: `--stress`, `--days`, `--r`, `--s-g` |
| [06_transcendence.py](06_transcendence.py) | W >= 0.995, state TRANSCENDED (демо с W(0)=0.996) |
| [07_lifecycle_replay.py](07_lifecycle_replay.py) | Детерминизм: два прогона с одинаковыми входами. Опция `--steps` |
| [08_life_simulation_lifecycle.py](08_life_simulation_lifecycle.py) | Симуляция жизней с lifecycle: F, W, state; при смерти — снапшот. Опции: `--days`, `--lives`, `--seed`, `--no-lifecycle`, `--no-astrology` |

Спека: [specs/005-lifecycle-entropy-research/](../specs/005-lifecycle-entropy-research/).
