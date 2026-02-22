# 008 — Sex Polarity & 32D Shifts

- **Спека**: [spec.md](spec.md)
- **Суть**: бинарный пол (`male`/`female`) с явной установкой или детерминированным выводом из натальной полярности; калиброванные сдвиги в 32D (8 осей ×4). Возраст — в спеце 009.
- **Режимы**: `sex_mode="explicit"` (по умолчанию) — пол задаётся явно, при отсутствии — baseline без сдвигов; `sex_mode="infer"` — детерминированный вывод из sign_polarity + sect.
- **Ключевые сущности**: SexResolver, SignPolarityEngine, SectEngine, SexPolarityEngine, SexDelta32Engine, W32 Profile (v1).
- **Критерии**: детерминизм step(), симметрия male/female дельт, границы [0,1], калибровочные пороги в CI.

## Как передать sex и sex_mode

- **birth_data** при создании Agent может содержать:
  - `sex`: `"male"` | `"female"` | не передавать (тогда при explicit — baseline, при infer — вывод).
  - `sex_mode`: `"explicit"` (по умолчанию) | `"infer"`.
- Пример явного пола: `Agent({"positions": [...], "sex": "male"})`.
- Пример infer: `Agent({"positions": [...], "sex_mode": "infer"})` — пол выводится по наталу; при недостатке данных — ошибка (fallback в None не допускается).

## Калибровка

- Скрипт: `scripts/008/calibration_sanity.py` (из корня репозитория: `uv run python scripts/008/calibration_sanity.py`).
- Фиксированный seed (по умолчанию 42), синтетическая популяция 50/50, пороги по SC-004. Подробности и CI: [scripts/008/README.md](../../scripts/008/README.md).
- При изменении **sex_strength** или **W32** рекомендуется запускать калибровку в CI.
