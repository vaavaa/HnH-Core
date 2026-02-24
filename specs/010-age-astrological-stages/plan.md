# Implementation Plan: 010 — Age Influence (Astrological Life Stages → 32D)

**Branch**: `010-age-astrological-stages` | **Date**: 2026-02-24 | **Spec**: [spec.md](spec.md)  
**Depends on**: 006 (Agent, BehavioralCore, assemble_state), 002 (32D schema), 008 (sex in base), 009 (transit modulation).  
**Design detail**: [sdd.md](sdd.md) — алгоритмы, интерфейсы, daily Lipschitz.

---

## Summary

Ввести **хронологический возраст** от `birth_datetime_utc` и `injected_time_utc`, детерминированный вектор из 5 астрологических стадий (maturity, saturn_event, jupiter_return, nodal_return, uranus_opposition) и ограниченную добавку **age_delta_32** в сборку 32D. Компонент **AgeEngine** (композиция в Agent). При `age_mode="off"` — нулевая дельта, обратная совместимость. При `age_mode="on"` и отсутствии birth_datetime_utc — **fail-fast** (явная ошибка; реализация документирует тип и сообщение). Порядок модификаторов: base + transit + memory + **age_delta** → clamp01. Границы: per-parameter cap (age_max_param_delta), Lipschitz **per call** (age_daily_lipschitz — макс. изменение по каждой компоненте между двумя последовательными вызовами compute(), без масштабирования по календарным дням). Детерминизм replay сохраняется; конфиг возраста входит в configuration_hash при age_mode=on.

---

## Technical Context

**Language**: Python 3.12 (текущий стек HnH).  
**Dependencies**: 002 (NUM_PARAMETERS, PARAMETERS, get_parameter_index), 006 (Agent, BehavioralCore, TransitEngine, step order), 008 (base_vector уже с sex), 009 (bounded_delta может быть масштабирован).  
**Integration**: AgeEngine опционально в Agent; в `step()` — получение birth_datetime_utc из birth_data, вызов `AgeEngine.compute(birth_dt_utc, injected_time_utc)` → AgeOutput; передача `age_delta_32` в `BehavioralCore.apply_transits(..., age_delta_32=...)` и в `assemble_state(..., age_delta_32=...)`.  
**Config**: AgeConfig (age_mode, age_strength, age_max_param_delta, age_daily_lipschitz, age_profile, age_max_years); константы периодов в коде или конфиге.  
**Testing**: pytest; unit — age_years, bump/sigmoid, stage features, W_age/delta_32, daily Lipschitz; integration — Agent.step() с/без age, детерминизм, границы.  
**Constraints**: age_mode default "off"; без RNG; debug-поля (age_years, age_stage_features, age_delta_32_stats) только при включённом debug.

---

## Constitution Check (010)

- [ ] **Determinism**: Same (birth_dt, config, date sequence) → same age_years, age_stage_features, age_delta_32; Lipschitz state from previous step only; no RNG.
- [ ] **Identity/Core separation**: Age не мутирует Identity; age_delta — добавка в сборку на каждом шаге, как memory_delta.
- [ ] **Behavioral parameterization**: Признаки стадий и W_age — числовые, версионируемые (v1).
- [ ] **Logging & observability**: age_years, age_stage_features, age_delta_32_stats только при debug; без debug вывод обратно совместим.
- [ ] **Repository standards**: Python, type hints; константы и W_age в коде/модуле, документированы.

---

## Implementation Outline

### 1. Константы и конфиг

- **Константы периодов** (v1): TROPICAL_YEAR_DAYS=365.2425, SATURN_PERIOD_YEARS=29.50, JUPITER_PERIOD_YEARS=11.86, URANUS_PERIOD_YEARS=84.00, NODE_PERIOD_YEARS=18.60 — в `hnh/age/constants.py` или внутри модуля stage_features.
- **AgeConfig**: dataclass (frozen или обычный) в `hnh/config/age_config.py`: age_mode, age_strength, age_max_param_delta, age_daily_lipschitz, age_profile, age_max_years с дефолтами из спеки. **Валидация (spec Clarifications)**: age_mode in ("off", "on") — при неизвестном fail-fast; недопустимые значения числовых полей (например отрицательные, ноль где запрещено, вне допустимых диапазонов) MUST вызывать fail-fast при использовании конфига; реализация MUST документировать допустимые диапазоны и тип/сообщение ошибки.

### 2. Stage features (v1)

- **Модуль** `hnh/age/stage_features.py`: чистые функции — `bump(age, center, width)` (width > 0), `sigmoid(x)` (численно стабильная реализация), `age_years_from_delta_days(delta_days, age_max_years)`, `maturity(age_years)`, `saturn_event(age_years)`, `jupiter_return(age_years)`, `nodal_return(age_years)`, `uranus_opposition(age_years)`, `age_stage_features_v1(age_years) -> tuple[float, ...]` (длина 5). Все значения в [0, 1]; детерминировано.

### 3. W_age v1 и age_delta_32

- **Модуль** `hnh/age/delta_32.py`: матрица W_age v1 (5×32) по спеке (sparse → массив по каноническому порядку 002); функция `compute_age_delta_32(features: tuple[float, ...], age_strength: float, age_max_param_delta: float) -> tuple[float, ...]`. Per-parameter clamp после линейной комбинации.
- **Lipschitz (per call)**: функция `apply_daily_lipschitz(prev_delta_32, raw_delta_32, L)` в том же модуле или в engine; сохранять prev в AgeEngine. Ограничение: макс. изменение по каждой компоненте между двумя последовательными вызовами compute() равно L (не масштабируется по календарным дням между вызовами).

### 4. AgeEngine

- **Модуль** `hnh/age/engine.py`: класс `AgeEngine(config: AgeConfig)`. Состояние: `_last_age_delta_32: tuple[float, ...] | None`, обновляется после каждого `compute`.
- **Метод** `compute(...) -> AgeOutput`: delta_days → age_years (clamp); age_stage_features_v1(age_years); raw_delta_32 = compute_age_delta_32(...); при первом вызове (_last_age_delta_32 is None) вернуть raw_delta_32 как age_delta_32 и сохранить в _last_age_delta_32; иначе age_delta_32 = apply_daily_lipschitz(_last_age_delta_32, raw_delta_32, config.age_daily_lipschitz), обновить _last_age_delta_32; вернуть AgeOutput(age_years, age_stage_features, age_delta_32 [, stats]).
- **Отсутствие birth_datetime_utc** (spec Clarifications): при age_mode=on и невозможности получить birth_datetime_utc из birth_data — **fail-fast**: MUST выбросить явную ошибку (e.g. ValueError); реализация MUST документировать тип и сообщение ошибки.

### 5. Интеграция в assemble_state и BehavioralCore

- **assemble_state** (`hnh/state/assembler.py`): добавить аргумент `age_delta_32: tuple[float, ...] | None = None`; при None — (0.0,) * 32; формула: `params_final[p] = clamp01(base_vector[p] + transit + mem[p] + age_delta_32[p])`; проверка длины 32.
- **BehavioralCore.apply_transits** (`hnh/state/behavioral_core.py`): сигнатура `apply_transits(self, transit_state, memory_delta=None, age_delta_32=None)`; передать оба в assemble_state.

### 6. Интеграция в Agent (FR-199, FR-199a)

- **Единое место сборки**: Вся сборка состояния (params_final, axis_final) выполняется только в `Agent.step()`. Никакой вызывающий код (в т.ч. run_step_v2) не должен вызывать assemble_state для агента снаружи; должен делегировать в `Agent.step(...)`.
- **Конструктор**: опционально `age_config: AgeConfig | None = None`. Если передан и age_config.age_mode == "on", создать `AgeEngine(age_config)`, иначе `_age_engine = None`.
- **step(date_or_dt, memory_delta=None)**: сигнатура с опциональным `memory_delta`; привести к injected_time_utc; из birth_data получить birth_datetime_utc (при _age_engine и отсутствии birth_datetime_utc — fail-fast). При наличии _age_engine вычислить age_out и age_delta_32; вызвать `behavior.apply_transits(transit_state, memory_delta=memory_delta, age_delta_32=age_out.age_delta_32 if age_out else None)` (при memory_delta=None в apply_transits подставлять нули). **Debug (spec Clarifications)**: при debug=True и age_mode=on добавить age_years, age_stage_features, age_delta_32_stats в **тот же объект, что возвращает step()** (расширение StepResult), не в отдельный контейнер.
- **run_step_v2**: рефакторинг — при пути «только memory_delta, без phase/history» MUST вызывать `Agent.step(dt_utc, memory_delta=memory_delta)` и не вызывать assemble_state сам. Условие делегирования в Agent расширить так, чтобы ненулевой memory_delta не отключал делегирование (передавать memory_delta в step). Пути с phase/transit_effect_history — целевой рефакторинг в будущем (вся сборка в Agent.step()).

### 7. Replay и configuration_hash

- При age_mode=on включить в payload для configuration_hash поля: age_mode, age_strength, age_max_param_delta, age_daily_lipschitz, age_profile, age_max_years (см. data-model 010). Реализация в `hnh/config/replay_config.py` или там, где формируется хеш.

### 8. Тесты

- **Unit**: age_years от двух дат (Δt/365.2425, clamp); bump, sigmoid; все 5 признаков на фиксированных возрастах; compute_age_delta_32 (границы, нулевые признаки); apply_daily_lipschitz (ограничение шага per call); невалидный AgeConfig → fail-fast; при age_mode=on и отсутствии birth_datetime_utc → fail-fast (документированный тип ошибки).
- **Integration**: Agent.step() с age_mode=on/off; с memory_delta и без; один и тот же натал/даты — два прогона, одинаковые хеши; сравнение params_final с age 20 vs 40 при том же натале; проверка max_abs(age_delta_32) <= age_max_param_delta; run_step_v2 с memory_delta делегирует в Agent.step(memory_delta=...) и результат совпадает с ожидаемой сборкой; при debug и age_mode=on объект, возвращаемый step(), содержит age_years, age_stage_features, age_delta_32_stats.

---

## Target Package Layout (010)

```text
hnh/
  age/
    __init__.py
    constants.py      # или в stage_features
    stage_features.py
    delta_32.py
    engine.py
  config/
    age_config.py    # AgeConfig
  state/
    assembler.py     # + age_delta_32
    behavioral_core.py # + age_delta_32 in apply_transits
  agent.py           # + age_engine, age_config, step() calls AgeEngine

specs/010-age-astrological-stages/
  spec.md
  plan.md            # этот файл
  tasks.md
  data-model.md
  sdd.md
```

Tests: `tests/unit/test_010_*.py`, `tests/integration/test_010_*.py` (по плану выше).

**Success Criterion 5 (population guardrails)**: по Clarifications автоматический скрипт/CI для проверки порогов (N≥10k, mean shift, adjacent slices) **не обязателен** в рамках 010; пороги остаются целевыми для калибровки и ручной или будущей автоматической проверки.
