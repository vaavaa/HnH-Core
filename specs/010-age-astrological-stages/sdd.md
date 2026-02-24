# Software Design Document: HnH 010 — Age Influence (Astrological Life Stages → 32D)

**Feature Branch**: `010-age-astrological-stages`  
**Created**: 2026-02-24  
**Spec**: [spec.md](spec.md) · **Data model**: [data-model.md](data-model.md)

Документ описывает архитектуру, модули, интерфейсы и интеграцию фичи 010 в ядро HnH.

---

## 1. Цели и ограничения

- **Цель**: ввести детерминированный возраст от `birth_datetime_utc` и момента шага, вектор из 5 астрологических стадий и ограниченную добавку `age_delta_32` в сборку 32D.
- **Ограничения**: без изменения порядка модификаторов 006/008/009; обратная совместимость при `age_mode="off"`; детерминизм replay; соблюдение границ и day-to-day Lipschitz.

---

## 2. Архитектура и место в пайплайне

- **AgeEngine** — отдельный компонент (композиция, не миксин). Агент хранит `age_engine: AgeEngine | None`; при `age_mode="off"` или отсутствии `birth_datetime_utc` — `None`, дельта не применяется.
- **Порядок модификаторов** (FR-202):  
  `params_final = clamp01( params_base + (bounded_delta × sensitivity) + memory_delta + sex_delta + age_delta )`  
  На практике: `params_base` уже включает 008 sex shift; в `assemble_state` передаются `transit_effect`, `memory_delta`, `age_delta_32`. То есть добавка только **age_delta_32** в вызов сборки.
- **Поток данных**:
  1. `Agent.step(date)` получает `injected_time_utc` (из `date` или datetime).
  2. При `age_engine is not None` вызывается `age_engine.compute(birth_dt_utc, injected_time_utc)` → `AgeOutput`.
  3. При необходимости применяется **daily Lipschitz** к `age_delta_32` (см. п. 6).
  4. `BehavioralCore.apply_transits(transit_state, age_delta_32=...)` (или аналог) передаёт дельту в `assemble_state`.
  5. `assemble_state(..., age_delta_32=...)` добавляет её перед `clamp01`; `axis_final` пересчитывается из финального 32D как раньше.

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│ birth_data      │     │ injected_    │     │ AgeConfig       │
│ (birth_dt_utc)  │────▶│ time_utc     │────▶│ (age_mode,      │
└─────────────────┘     └──────┬───────┘     │  strength, ...) │
                               │             └────────┬────────┘
                               ▼                      ▼
                        ┌──────────────┐      ┌──────────────┐
                        │ AgeEngine    │      │ W_age v1     │
                        │ .compute()   │─────▶│ (5×32)       │
                        └──────┬───────┘      └──────────────┘
                               │
                               ▼
                        age_years, age_stage_features_v1, age_delta_32
                               │
                               ▼
                        ┌──────────────────────────────────────┐
                        │ assemble_state( base, sens,           │
                        │   bounded_delta, memory_delta,        │
                        │   age_delta_32 )                      │
                        └──────────────────────────────────────┘
```

---

## 3. Размещение модулей

| Компонент            | Размещение (предложение)     | Назначение |
|----------------------|-----------------------------|------------|
| AgeConfig            | `hnh/config/age_config.py`   | Поля age_mode, age_strength, age_max_param_delta, age_daily_lipschitz, age_profile, age_max_years, константы периодов. |
| AgeEngine            | `hnh/age/engine.py`         | Класс с методом `compute(birth_dt_utc, injected_time_utc) -> AgeOutput`. |
| Stage features v1    | `hnh/age/stage_features.py` | Чистые функции: `age_years_from_delta_days`, `bump`, `sigmoid`, `maturity`, `saturn_event`, `jupiter_return`, `nodal_return`, `uranus_opposition`, `age_stage_features_v1(age_years)`. |
| W_age v1, age_delta  | `hnh/age/delta_32.py`       | Матрица весов W_age v1 (5×32), функция `compute_age_delta_32(features, strength, max_delta) -> tuple[float, ...]`. |
| Lipschitz smoothing  | `hnh/age/engine.py` или `hnh/age/delta_32.py` | Ограничение day-to-day изменения: `apply_daily_lipschitz(prev_delta_32, raw_delta_32, L) -> tuple[float, ...]`. |
| Интеграция в Agent   | `hnh/agent.py`              | Опциональный `age_config`/`AgeEngine` в конструкторе; в `step()` вызов AgeEngine и передача `age_delta_32` в сборку. |
| Интеграция в assembler | `hnh/state/assembler.py`  | Новый опциональный аргумент `age_delta_32: tuple[float, ...] | None = None`; при наличии добавляется к сумме до clamp01. |
| Интеграция в BehavioralCore | `hnh/state/behavioral_core.py` | `apply_transits(transit_state, memory_delta=None, age_delta_32=None)` и передача в `assemble_state`. |

Пакет `hnh/age/` содержит: `engine.py`, `stage_features.py`, `delta_32.py`; при необходимости — `constants.py` для TROPICAL_YEAR_DAYS и периодов.

---

## 4. Интерфейсы и типы

### 4.1 AgeConfig (dataclass или frozen)

- `age_mode: Literal["off", "on"] = "off"`
- `age_strength: float = 0.04`
- `age_max_param_delta: float = 0.06`
- `age_daily_lipschitz: float = 0.001`
- `age_profile: str = "v1"`
- `age_max_years: float = 120.0`

Константы периодов (модуль/конфиг): `TROPICAL_YEAR_DAYS`, `SATURN_PERIOD_YEARS`, `JUPITER_PERIOD_YEARS`, `URANUS_PERIOD_YEARS`, `NODE_PERIOD_YEARS` — как в спеке.

### 4.2 AgeOutput (результат AgeEngine.compute)

- `age_years: float`
- `age_stage_features: tuple[float, ...]`  # длина 5: maturity, saturn_event, jupiter_return, nodal_return, uranus_opposition
- `age_delta_32: tuple[float, ...]`       # длина 32, после Lipschitz и per-parameter cap

Опционально для отладки: `age_delta_32_stats: dict` (max_abs, mean_abs, nonzero_count).

### 4.3 AgeEngine

- Конструктор: `AgeEngine(config: AgeConfig)`.
- Состояние для Lipschitz: хранить `_last_age_delta_32: tuple[float, ...] | None` и `_last_injected_time_utc` (или только предыдущую дельту; при смене даты на +1 день применять Lipschitz).
- Метод: `compute(self, birth_datetime_utc: datetime, injected_time_utc: datetime) -> AgeOutput`.
  - Вычислить `age_years` (через stage_features или здесь).
  - Вызвать `age_stage_features_v1(age_years)`.
  - Вызвать `compute_age_delta_32(features, config.age_strength, config.age_max_param_delta)`.
  - Применить `apply_daily_lipschitz(_last_age_delta_32, raw_delta_32, config.age_daily_lipschitz)`; обновить `_last_age_delta_32` и (если нужно) время.
  - Вернуть AgeOutput.

Важно: для детерминизма replay порядок вызовов `step(date)` фиксирован; состояние Lipschitz зависит только от предыдущего шага и текущей даты, без побочных эффектов.

---

## 5. Алгоритмы (псевдокод)

### 5.1 age_years (FR-010)

```text
delta_days = (injected_time_utc - birth_datetime_utc).total_seconds() / 86400.0
age_years = clamp(delta_days / TROPICAL_YEAR_DAYS, 0.0, age_max_years)
```

Использовать одну и ту же константу 365.2425 в одном месте (например в `stage_features` или `constants`).

### 5.2 bump и sigmoid

```text
def bump(age: float, center: float, width: float) -> float:
    return max(0.0, 1.0 - abs(age - center) / width)   # width MUST be > 0 (spec)

def sigmoid(x: float) -> float:
    # Численно стабильная реализация: при x >= 0 — 1/(1+exp(-x)); при x < 0 — exp(x)/(1+exp(x))
    return 1.0 / (1.0 + exp(-x)) if x >= 0 else exp(x) / (1.0 + exp(x))
```

### 5.3 maturity

```text
maturity = sigmoid((age_years - 25.0) / 7.0)
```

### 5.4 Saturn / Jupiter / Nodal / Uranus (как в спеке)

- `p = age_years % SATURN_PERIOD_YEARS`; центры C0=0, C1=0.25*T, C2=0.5*T, C3=0.75*T; ширины 1.5, 1, 1, 1; `saturn_event = max(bump(p, C0, 1.5), ...)`.
- `pj = age_years % JUPITER_PERIOD_YEARS`; `jupiter_return = bump(pj, 0.0, 0.75)`.
- `pn = age_years % NODE_PERIOD_YEARS`; два центра 0 и 0.5*NODE_PERIOD_YEARS, ширина 1.0.
- `pu = age_years % URANUS_PERIOD_YEARS`; `uranus_opposition = bump(pu, 0.5*URANUS_PERIOD_YEARS, 2.0)`.

Все значения в [0, 1].

### 5.5 age_delta_32 из признаков

Для каждого параметра `i` (0..31):

```text
raw[i] = age_strength * sum(feature[j] * W_age[j][i] for j in 0..4)
age_delta_32[i] = clamp(raw[i], -age_max_param_delta, +age_max_param_delta)
```

Матрица W_age v1 задаётся по спеке (sparse: по имени параметра через `get_parameter_index`, незаданные = 0).

### 5.6 Daily Lipschitz (smoothness)

Чтобы выполнить условие `max_abs(age_delta_32(t+1d) - age_delta_32(t)) <= age_daily_lipschitz`:

- Хранить на движке предыдущий выход: `prev = _last_age_delta_32`.
- **Первый вызов** (`prev is None`): выдать `age_delta_32 = raw_delta_32` без применения Lipschitz; сохранить в `_last_age_delta_32`. Инвариант smoothness применяется к парам **последовательных вызовов после первого**; на первом шаге допустимо изменение до age_max_param_delta.
- **Последующие вызовы**: после вычисления `raw_delta_32`: для каждого `i`: `diff_i = raw_delta_32[i] - prev[i]`; `clipped_i = clamp(diff_i, -L, +L)` где `L = age_daily_lipschitz`; `age_delta_32[i] = prev[i] + clipped_i`. Обновить `_last_age_delta_32 = age_delta_32`.
- Для детерминизма состояние должно однозначно определяться последовательностью вызовов `compute` с теми же (birth_dt, injected_dt_1, injected_dt_2, ...).

---

## 6. Интеграция в Agent и BehavioralCore

### 6.1 Agent

- В конструктор добавить опционально: `age_config: AgeConfig | None = None`. Если передан и `age_config.age_mode == "on"`, создавать `AgeEngine(age_config)` и сохранять в `self._age_engine`; иначе `self._age_engine = None`.
- Для `step(date_or_dt, memory_delta=None)`:
  - Получить `injected_time_utc` (если передан `date`, преобразовать в datetime на начало дня UTC или по контракту 006/CLI).
  - Получить `birth_datetime_utc` из `birth_data` (см. data-model 010). Если нет и `age_engine is not None` — либо считать age_mode как "off" для этого шага, либо ошибка в strict mode (спека).
  - Если `self._age_engine is not None` и birth_datetime_utc есть: `age_out = self._age_engine.compute(birth_datetime_utc, injected_time_utc)`; иначе `age_delta_32 = None`.
  - `memory_delta` передать в `apply_transits` (если None — в apply_transits подставляются нули).
  - Вызвать `self.behavior.apply_transits(transit_state, memory_delta=memory_delta, age_delta_32=age_out.age_delta_32 if age_out else None)`.
  - При debug: добавить в вывод `age_years`, `age_stage_features`, `age_delta_32_stats` из age_out.

### 6.2 BehavioralCore.apply_transits

- Сигнатура: `apply_transits(self, transit_state, memory_delta=None, age_delta_32=None)`.
- Внутри: вызов `assemble_state(self._base_vector, sens, transit_state.bounded_delta, memory_delta=memory_delta, age_delta_32=age_delta_32)`; результат в `self._current_vector`.

### 6.3 assemble_state

- Добавить аргумент `age_delta_32: tuple[float, ...] | None = None`.
- Если `age_delta_32 is None`, подставлять `(0.0,) * 32`.
- Формула: `params_final[p] = clamp01(base_vector[p] + transit + mem[p] + age_delta_32[p])`.
- Проверка длины 32 для age_delta_32 при передаче.

### 6.4 run_step_v2 / replay (FR-199)

- **Делегирование обязательно**: Вся сборка состояния агента (params_final, axis_final) выполняется только в `Agent.step()`. `run_step_v2` и любой другой вызывающий код MUST вызывать `Agent.step(injected_time_utc, memory_delta=...)` и использовать результат агента; MUST NOT вызывать `assemble_state` для поведения агента снаружи Agent.
- **Рефакторинг run_step_v2**: Текущие ветки run_step_v2, которые при наличии только memory_delta (без phase/history) вызывают `assemble_state` сами, MUST быть переписаны: вместо этого создавать Agent (или использовать переданный контекст), вызывать `Agent.step(dt_utc, memory_delta=memory_delta)` и брать `params_final`/`axis_final` из агента. Условие «делегировать в Agent» должно включать случай ненулевого memory_delta (передавать его в step). Ветки с phase/transit_effect_history остаются до переноса в Agent в будущем; целевое состояние — вся логика сборки внутри Agent.step(), при необходимости с расширением сигнатуры step (например precomputed_transit_effect) в отдельной спецификации.

---

## 7. Конфигурация и replay-подпись

- Replay-relevant поля 010: `age_mode`, `age_strength`, `age_max_param_delta`, `age_daily_lipschitz`, `age_profile`, `age_max_years` (и при необходимости константы периодов, если они станут конфигурируемыми). Включить их в `compute_configuration_hash` при наличии секции age (или при age_mode=on), чтобы смена настроек возраста меняла подпись replay.
- Хранение: либо расширить `ReplayConfig` (или отдельный объект конфига), либо отдельный `AgeConfig`, передаваемый в Agent; способ сериализации в replay — в data-model.

---

## 8. Граничные случаи и инварианты

- **Нет birth_datetime_utc**: при `age_engine is not None` не вызывать compute или возвращать нулевую дельту (age_mode трактуется как "off" для шага); в strict mode — ошибка (по спеке).
- **age_years вне [0, age_max_years]**: уже учтено в FR-010 (clamp).
- **Большие скачки даты**: Lipschitz ограничивает изменение от предыдущего шага; за один шаг дельта не может измениться больше чем на 32 * age_daily_lipschitz по норме (и по каждому компоненту — на age_daily_lipschitz).
- **Инварианты**: (1) `max_abs(age_delta_32[i]) <= age_max_param_delta` после cap и Lipschitz; (2) `params_final` в [0,1] за счёт clamp01; (3) детерминизм при одинаковых (birth_dt, последовательность injected_time_utc, config).

---

## 9. Тестирование (кратко)

- Юнит: вычисление age_years по двум датам; bump/sigmoid; все 5 признаков на фиксированных возрастах; W_age и compute_age_delta_32 (границы, нулевые признаки); apply_daily_lipschitz (ограничение шага).
- Интеграция: Agent.step() с age_mode=on/off, сравнение params_final с/без возраста; два прогона с одними входами — совпадение хешей; проверка пиков saturn_event / uranus_opposition на ожидаемых возрастах (при необходимости — скрипт калибровки).

---

## 10. Зависимости от других спецификаций

- **006**: Agent, BehavioralCore, assemble_state, порядок шага.
- **002**: 32 параметра, имена осей/параметров, NUM_PARAMETERS.
- **008**: base_vector уже включает sex; не дублировать sex_delta в формулу сборки в 010.
- **009**: транзитная дельта (bounded_delta) уже может быть масштабирована по полу; age_delta добавляется после неё в одной сумме перед clamp01.

Спека 010 и данный SDD готовы к переносу в plan.md и tasks.md для реализации.
