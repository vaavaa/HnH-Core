# Data Model: 010 — Age Influence (Astrological Life Stages → 32D)

Сущности и контракты данных для спецификации 010. Опирается на birth_data (006) и 32D-схему (002).

---

## 1. Источники времени для возраста

### 1.1 birth_datetime_utc

- **Назначение**: момент рождения в UTC для расчёта возраста.
- **Источник**: из **birth_data** (006 data-model).
  - **Вариант A**: поле `datetime_utc` (str в ISO 8601 или `datetime`). Использовать как есть или привести к `datetime` в UTC.
  - **Вариант B**: если в birth_data есть только позиции без явной даты/времени, то `birth_datetime_utc` для 010 **отсутствует**; при `age_mode="on"` система MUST выполнить **fail-fast** (явная ошибка; реализация документирует тип и сообщение). При `age_mode="off"` отсутствие birth_datetime_utc не является ошибкой.
- **Тип**: `datetime` (timezone-aware UTC) или эквивалент для вычисления `total_seconds()` / дней.

### 1.2 injected_time_utc

- **Назначение**: каноническое время шага (момент, на который считается поведение).
- **Источник**: аргумент `date_or_dt` в `Agent.step(date_or_dt)` (006/CLI). При передаче `date` реализация MUST однозначно преобразовать в datetime: **00:00:00 UTC этого дня** (т.е. момент начала календарного дня в UTC). При передаче `datetime` — использовать как момент в UTC (при необходимости привести к UTC).
- **Тип**: `datetime` (timezone-aware UTC).

---

## 2. Конфигурация возраста (AgeConfig)

| Поле                  | Тип     | По умолчанию | Описание |
|-----------------------|---------|--------------|----------|
| age_mode              | `"off" \| "on"` | `"off"` | Включение расчёта возраста и age_delta_32. |
| age_strength          | float   | 0.04         | Масштаб линейной комбинации признаков перед cap. |
| age_max_param_delta   | float   | 0.06         | Верхняя граница по модулю на каждый компонент age_delta_32. |
| age_daily_lipschitz   | float   | 0.001        | Максимальное допустимое изменение по каждому параметру за один день. |
| age_profile           | str     | `"v1"`       | Профиль признаков и весов (v1 — фазовая модель). |
| age_max_years         | float   | 120.0        | Верхняя граница age_years при clamp. |

**Валидация (Clarifications)**: Недопустимые значения (отрицательные, ноль где запрещено, вне допустимых диапазонов) MUST вызывать fail-fast при использовании конфига; реализация MUST документировать допустимые диапазоны и тип/сообщение ошибки.

Константы периодов (v1, детерминированные):

| Константа               | Значение  |
|-------------------------|-----------|
| TROPICAL_YEAR_DAYS      | 365.2425  |
| SATURN_PERIOD_YEARS     | 29.50     |
| JUPITER_PERIOD_YEARS    | 11.86     |
| URANUS_PERIOD_YEARS     | 84.00     |
| NODE_PERIOD_YEARS       | 18.60     |

---

## 3. Выход AgeEngine (AgeOutput)

| Поле                  | Тип                    | Описание |
|-----------------------|------------------------|----------|
| age_years              | float                  | Возраст в годах (после clamp [0, age_max_years]). |
| age_stage_features     | tuple[float, ...]      | Длина 5: (maturity, saturn_event, jupiter_return, nodal_return, uranus_opposition); все в [0, 1]. |
| age_delta_32           | tuple[float, ...]      | Длина 32; добавка к 32D перед clamp01; после per-parameter cap и daily Lipschitz. |

Опционально (debug):

| Поле                  | Тип     | Описание |
|-----------------------|---------|----------|
| age_delta_32_stats    | dict    | max_abs, mean_abs, nonzero_count по age_delta_32. |

Инварианты: `max(abs(age_delta_32[i])) <= age_max_param_delta`. Smoothness (Clarifications): между любыми двумя последовательными вызовами `compute()` для каждой компоненты i выполняется `abs(age_delta_32[i](next) - age_delta_32[i](prev)) <= age_daily_lipschitz`; ограничение per call (не масштабируется по календарным дням). На **первом** вызове compute допустимо выдать сырую дельту без Lipschitz.

---

## 4. Вектор признаков стадий (age_stage_features_v1)

**Канонический порядок** (единственный источник истины для индекса j в W_age и для порядка в tuple):

| j | Имя              | Описание |
|---|------------------|----------|
| 0 | maturity         | sigmoid((age_years - 25) / 7). |
| 1 | saturn_event     | max из bump по фазам Сатурна (return, square, opposition, square). |
| 2 | jupiter_return   | bump(age_years % JUPITER_PERIOD, 0, 0.75). |
| 3 | nodal_return     | max из двух bump по узлам. |
| 4 | uranus_opposition| bump(age_years % URANUS_PERIOD, 0.5*URANUS_PERIOD, 2.0). |

Реализация MUST использовать этот порядок для `age_stage_features` и для строк/столбцов W_age. Все значения признаков в [0, 1].

---

## 5. Матрица весов W_age v1

- Размер: 5 признаков × 32 параметра.
- Канонический порядок параметров — по 002 (`_PARAMETER_LIST` / `get_parameter_index`).
- Задаётся разреженно: только ненулевые веса (см. spec.md § Mapping age stages to 32 parameters). Не указанные (param, feature) = 0.0.
- Тип в коде: например, структура (dict по (j, param_name) или 2D-массив float 5×32), обеспечивающая детерминированный доступ по индексу параметра.

---

## 6. Интеграция с Agent.step и assemble_state

- **Единое место сборки (FR-199)**: Вычисление `params_final` и `axis_final` выполняется только внутри `Agent.step()`. Вызывающий код (в т.ч. `run_step_v2`) передаёт при необходимости `memory_delta` в `Agent.step(date_or_dt, memory_delta=...)` и не вызывает `assemble_state` снаружи Agent.
- **Вход в Agent.step()**: опциональный `memory_delta: tuple[float, ...] | None = None`. Если передан — длина MUST быть 32; передаётся в `BehavioralCore.apply_transits` и далее в `assemble_state`. Если не передан — при сборке используется `(0.0,) * 32`.
- **Вход в assemble_state**: опциональный `age_delta_32: tuple[float, ...] | None`.
- Если передан: длина MUST быть 32; формула для каждого p:  
  `params_final[p] = clamp01(base_vector[p] + transit_effect[p] + memory_delta[p] + age_delta_32[p])`.
- Если age_delta_32 не передан (None): эквивалент `(0.0,) * 32` (обратная совместимость).

---

## 7. Replay и configuration_hash

При включении 010 в replay подпись MUST учитывать все replay-relevant поля возраста, чтобы смена настроек возраста давала другой configuration_hash. Рекомендуемые поля для хеша (при age_mode=on или при наличии секции age):

- age_mode, age_strength, age_max_param_delta, age_daily_lipschitz, age_profile, age_max_years.

Константы периодов (если в v1 зафиксированы в коде) можно не включать; если в будущем станут конфигурируемыми — включить.

---

## 8. Отладка и логирование

- При debug и age_mode=on (Clarifications): поля `age_years`, `age_stage_features`, `age_delta_32_stats` MUST быть добавлены в **тот же объект, что возвращает step()** (например расширение StepResult), не в отдельный debug-контейнер.
- По умолчанию (debug выключен): вывод остаётся обратно совместимым.
