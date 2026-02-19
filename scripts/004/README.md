# Примеры 004 — Planetary Core + Zodiac Expression Layer

Скрипты демонстрируют функционал спецификации 004: 10 планет (эфемериды), дома Placidus, натал с sign/house/angular_strength, слой Zodiac Expression (12×4), zodiac_summary_hash и полный пайплайн.

**Запуск:** из корня проекта с активированным venv:

```bash
cd /path/to/core
source .venv/bin/activate
python scripts/004/01_ephemeris_10_planets.py
```

Зависимости: `pip install -e ".[astrology]"` (pyswisseph, orjson, xxhash).

| Скрипт | Описание |
|--------|----------|
| [01_ephemeris_10_planets.py](01_ephemeris_10_planets.py) | 10 планет (Sun..Pluto), compute_positions, детерминизм по JD |
| [02_houses_placidus.py](02_houses_placidus.py) | Дома Placidus: compute_houses, longitude_to_house_number, angular_strength (1/0.6/0.3), assign_houses_and_strength |
| [03_natal_10_planets_houses.py](03_natal_10_planets_houses.py) | Натал 004: build_natal_positions — 10 планет, sign, house, angular_strength, houses (cusps, ascendant, mc). Опции: `--date`, `--lat`, `--lon` |
| [04_zodiac_expression.py](04_zodiac_expression.py) | Zodiac Expression: compute_zodiac_output → sign_energy_vector (12×4), dominant_sign, dominant_element. Опции: `--date`, `--lat`, `--lon` |
| [05_zodiac_hash.py](05_zodiac_hash.py) | zodiac_summary_hash: xxhash от sign_energy_vector (orjson OPT_SORT_KEYS), replay consistency §9.1 |
| [06_full_zodiac_pipeline.py](06_full_zodiac_pipeline.py) | Полный пайплайн: натал → зодиак → хеш. Опции: `--date`, `--lat`, `--lon`, `--out` (запись одной JSON-строки) |
| [09_life_simulation_102y.py](09_life_simulation_102y.py) | Симуляция многих жизней (как 002): случайные даты рождения от Р.Х. до сегодня, Лондон, 70–108 лет, два расчёта/день. Вывод: дельты по осям + 004-параметры (натал: dominant_sign, dominant_element, zodiac_hash, ascendant, mc; транзитный зодиак в начале и в конце жизни). Опции: `--lives`, `--seed`, `--days`, `--no-astrology` |

Спека: [specs/004-planetary-core-zodiac-expression/](../specs/004-planetary-core-zodiac-expression/).
