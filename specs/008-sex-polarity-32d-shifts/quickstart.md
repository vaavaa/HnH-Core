# 008 — Sex Polarity & 32D Shifts

- **Спека**: [spec.md](spec.md)
- **Суть**: бинарный пол (`male`/`female`) с явной установкой или детерминированным выводом из натальной полярности; калиброванные сдвиги в 32D (8 осей ×4). Возраст — в спеце 009.
- **Режимы**: `sex_mode="explicit"` (по умолчанию) — пол задаётся явно, при отсутствии — baseline без сдвигов; `sex_mode="infer"` — детерминированный вывод из sign_polarity + sect.
- **Ключевые сущности**: SexResolver, SignPolarityEngine, SectEngine, SexPolarityEngine, SexDelta32Engine, W32 Profile (v1).
- **Критерии**: детерминизм step(), симметрия male/female дельт, границы [0,1], калибровочные пороги в CI.
