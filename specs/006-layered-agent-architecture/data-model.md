# Data Model: 006 — Layered Agent Architecture

Сущности и связи, вводимые спецификацией 006. Все слои детерминированы; replay по (birth_data, config, dates) воспроизводим.

---

## 0. Контракт birth_data

**birth_data** — вход для построения NatalChart и для конструктора Agent. Спека задаёт только общее описание; точная схема здесь (и в контрактах 002/004, где используется natal_data).

Допустимы два варианта (реализация NatalChart/Agent должна поддерживать хотя бы один):

**Вариант A — данные для расчёта позиций (дата, время, место):**

| Ключ           | Тип     | Обязательность | Описание |
|----------------|---------|----------------|----------|
| datetime_utc   | str или datetime | да*   | Момент рождения в UTC (ISO 8601 или datetime). |
| lat            | float   | да*            | Широта места рождения в градусах [-90, 90]. |
| lon            | float   | да*            | Долгота места рождения в градусах [-180, 180]. |
| timezone       | str или float | нет  | Часовой пояс (если datetime не в UTC). |

\* Обязательно для варианта A. По этим полям вызывается ephemeris (002/004); результат — список позиций планет.

**Вариант B — готовые позиции (уже посчитанные):**

| Ключ      | Тип     | Обязательность | Описание |
|-----------|---------|----------------|----------|
| positions | tuple[dict, ...] или list[dict] | да | Каждый элемент: `{"planet": str, "longitude": float}`; planet — каноническое имя (Sun, Moon, …); longitude — эклиптическая долгота [0, 360). Совместимо с `hnh/identity/sensitivity.compute_sensitivity(natal_data)`. |
| aspects   | tuple или list | нет | Список аспектов (форма по 002/004); опционально для NatalChart, используется в sensitivity и при необходимости в TransitEngine. |

Для детерминизма и replay один и тот же формат (A или B) и одни и те же значения должны давать один и тот же NatalChart. Реализация MUST документировать, какой вариант поддерживается и какие дополнительные ключи допускаются.

---

## 1. Астрономический слой

### Planet

| Field      | Type   | Notes                          |
|-----------|--------|---------------------------------|
| name      | str    | Каноническое имя (Sun, Moon, …) |
| longitude | float  | Эклиптическая долгота [0, 360)   |
| sign      | str    | Вычисляется: ZODIAC_SIGNS[longitude//30] |
| house     | int \| None | Номер дома (если задана система домов) |

Инвариант: после создания объект неизменяем (frozen/dataclass frozen или readonly properties).

### Aspect

| Field    | Type   | Notes                                  |
|----------|--------|----------------------------------------|
| planet_a | Planet | Первая планета (или долгота)           |
| planet_b | Planet | Вторая планета (или долгота)           |
| angle    | float  | Угол между телами                      |
| type     | str    | Conjunction, Opposition, Square, …     |

Метод: `tension_score() -> float` по контракту transit-stress (hard aspects: Conjunction, Opposition, Square).

### NatalChart

| Field   | Type           | Notes                                                |
|---------|----------------|------------------------------------------------------|
| planets | tuple[Planet, ...] | Планеты (immutable; spec: no lists in final object). |
| aspects | tuple[Aspect, ...] | Аспекты между планетами (immutable).                 |
| houses  | (optional)     | Система домов (например Placidus).                   |

Инвариант: после построения immutable для целей replay.  
Вход построения: **birth_data** по контракту §0 (вариант A — datetime_utc, lat, lon; вариант B — positions, опционально aspects).

---

## 2. Zodiac Layer

### ZodiacExpression

| Field         | Type  | Notes                          |
|---------------|-------|---------------------------------|
| sign_vectors  | (spec 004) | Векторы по знакам/элементам |
| (computed)    | dominant_sign, dominant_element | Read-only view над наталом |

Вход: NatalChart (или эквивалентные данные). Не мутирует натал.

---

## 3. Поведенческий слой (32D)

### BehavioralCore

- **Конструктор**: `BehavioralCore(natal, identity_config)`.  
  **identity_config** — Identity (IdentityCore) или конфиг, дающий base_vector и sensitivity_vector.  
  `sensitivity_vector` живёт в Identity (`hnh/identity/schema.IdentityCore`); не хранится отдельно в BehavioralCore, а передаётся через identity_config при вызовах.

| Field          | Type              | Notes                                    |
|----------------|-------------------|------------------------------------------|
| base_vector    | tuple[float, ...]  | 32 параметра (из identity_config)        |
| current_vector | tuple[float, ...]  | 32 параметра (текущее состояние)         |

Методы: инициализация base_vector (и при необходимости sensitivity) из identity_config; `apply_transits(transit_state: TransitState)` использует `transit_state.bounded_delta` и sensitivity из identity. Делегирование в assembler (boundaries уже применены в TransitState). Не содержит F, W, state lifecycle.

---

## 4. Транзиты

### TransitState (структурированный выход слоя)

| Field          | Type            | Notes |
|----------------|-----------------|-------|
| stress         | float           | S_T(t) по контракту 005 (I_T/C_T, clip [0, 1]) |
| raw_delta      | Vector32        | Сырая дельта 32 параметров (до границ/shock) |
| bounded_delta  | Vector32        | Дельта после boundaries (ReplayConfig); для BehavioralCore |

Vector32 = `tuple[float, ...]` длины 32.

### TransitEngine

Состояние: ссылка на NatalChart. Не хранит поведенческое состояние.

**Единственный метод выхода на дату:**

| Method | Returns | Notes |
|--------|---------|-------|
| state(date, config) | TransitState | Один вызов — stress, raw_delta, bounded_delta. Конфиг нужен для bounded_delta (границы, shock). |

Отдельных методов только stress или только delta нет; контракт: [contracts/transit-engine.md](contracts/transit-engine.md).

---

## 5. Lifecycle

### LifecycleEngine

| Field (state) | Type   | Notes                    |
|---------------|--------|--------------------------|
| F             | float  | Fatigue                  |
| W             | float  | Will                     |
| state         | enum   | ALIVE \| DISABLED \| TRANSCENDED |
| (running)     | sum_v, sum_burn, count_days | Для delta_W при смерти |

Метод: `update_lifecycle(stress: float, resilience: float, ...)` — делегирует в hnh/lifecycle (fatigue, will, death, transcendence). Контракт по data-model 005.

---

## 6. Agent

### Agent

| Field      | Type            | Notes                          |
|------------|-----------------|--------------------------------|
| natal      | NatalChart      | Неизменяемая база              |
| behavior   | BehavioralCore  | 32D состояние                  |
| transits   | TransitEngine   | Погода на дату                 |
| lifecycle  | LifecycleEngine \| None | Опционально (research) |

Метод: `step(date)` — порядок: (1) transit_state = transits.state(date, config); (2) при lifecycle — lifecycle.update_lifecycle(transit_state.stress, resilience), lifecycle учитывает поведение прошлого шага; (3) behavior.apply_transits(transit_state).  
Product-mode: lifecycle=None. Research-mode: lifecycle=LifecycleEngine(...).

---

## 7. Интеграция с существующими моделями

- **Identity (002)**: sensitivity_vector живёт в **IdentityCore** (`hnh/identity/schema`). BehavioralCore принимает identity_config (IdentityCore или конфиг, дающий base_vector и sensitivity_vector); base_vector и sensitivity для apply_transits берутся из identity_config. При построении агента Identity можно получить из натала по логике 002 (compute_sensitivity, база из натала/зодиака) или передать явно.
- **ReplayConfig (002/005)**: передаётся в Agent при создании и далее в BehavioralCore, TransitEngine, LifecycleEngine где нужно; configuration_hash и replay-подпись без изменений.
- **Lifecycle state (005)**: при lifecycle_enabled состояние F, W, state и финальный снапшот по data-model 005; Agent не меняет контракт снапшота/подписи.

---

## 8. Последовательность создания (зависимости)

1. Planet → Aspect (зависит от Planet)
2. NatalChart (зависит от Planet, Aspect и от ephemeris/houses)
3. ZodiacExpression (зависит от NatalChart)
4. BehavioralCore (зависит от NatalChart, identity/schema, modulation, assembler)
5. TransitEngine (зависит от NatalChart, аспекты/стресс)
6. LifecycleEngine (фасад над hnh/lifecycle)
7. Agent (зависит от всех выше; композиция)
