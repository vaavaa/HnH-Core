# Tasks: 008 — Sex Polarity & 32D Shifts

**Input**: Design documents from `specs/008-sex-polarity-32d-shifts/`  
**Prerequisites**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md)

**Organization**: Phase 1 — Foundation (data, validation, resolution order); Phase 2 — User Story 1 (explicit sex, engines, identity integration); Phase 3 — User Story 2 (infer); Phase 4 — User Story 3 (calibration); Phase 5 — Polish and constitution.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Можно выполнять параллельно (разные файлы, нет зависимостей).
- **[Story]**: US1 = Explicit sex (P1), US2 = Infer (P2), US3 = Calibration (P3).

## Path Conventions

- Новые модули: `hnh/sex/` (sign_polarity.py, sect.py, resolver.py, polarity.py, delta_32.py).
- Расширения: `hnh/agent.py` (identity assembly, step output), при необходимости конфиг/ReplayConfig.
- Тесты: `tests/unit/test_008_*.py`, `tests/integration/test_008_*.py`; скрипты: `scripts/008/`. **Тесты уровня Agent для 008** (step() с полями sex/sex_polarity_E, Agent с sex в birth_data, детерминизм вызова step) — в `tests/unit/test_008_agent_sex.py`.

---

## Phase 1: Foundation (Data & Contracts)

**Purpose**: Контракты и порядок разрешения; без этого нельзя начинать US1/US2.

- [x] T001 [P] Расширить контракт **birth_data**: опциональные поля `sex` (`"male"|"female"|None`) и `sex_mode` (`"explicit"|"infer"`). Валидация: если `sex` передан и не в `{"male","female"}` — **fail-fast** (например `ValueError`) с явным сообщением. Документировать тип ошибки и текст (FR-001). Место: валидация при чтении birth_data в Agent или в отдельной утилите в `hnh/sex/`.
- [x] T002 Реализовать **порядок разрешения sex_mode**: сначала `birth_data.sex_mode`, при отсутствии — config агента/replay; дефолт `"explicit"`. Документировать в коде и в data-model. Зависит от T001.
- [x] T003 [P] Определить **источник identity_hash** для tie-break (infer): например digest от birth_data (orjson + xxhash) или поле в identity_config. Использовать детерминированный хеш (xxhash.xxh3_128); документировать в data-model и в коде.

**Checkpoint**: Валидация sex и разрешение sex_mode определены; identity_hash источник зафиксирован.

---

## Phase 2: User Story 1 — Explicit sex in production (Priority: P1)

**Goal**: Явная передача пола в birth_data; сдвиги 32D в identity (base_vector); вывод step() с sex и E; детерминизм и симметрия male/female.

**Independent Test**: Agent.step() с одинаковыми входами дважды — одинаковый вывод; при sex=None — E=0, нулевые сдвиги; при sex=male/female — E≠0, sex_delta_32 симметричны.

### Engines (можно параллельно после Phase 1)

- [x] T004 [P] [US1] **SignPolarityEngine**: вход — натал (планета → знак), веса планет (FR-012). Формула `sign_polarity_score = (Σ weight_p × sign_polarity(sign_p)) / (Σ weight_p)` только по планетам с известным знаком; полярность знаков FR-011. Выход ∈ [-1, 1]. Размещение: `hnh/sex/sign_polarity.py`.
- [x] T005 [P] [US1] **SectEngine**: вход — высота Солнца (предпочтительно) или номер дома Солнца. Правила: altitude >0 → +1, <0 → -1, ==0 → 0; fallback дома 7–12 → day, 1–6 → night. Выход sect_score ∈ {-1, 0, +1}. Размещение: `hnh/sex/sect.py` или `hnh/astrology/sect.py`.
- [x] T006 [P] [US1] **SexPolarityEngine**: вход — resolved sex, sign_polarity_score, sect_score; коэффициенты a,b,c (по умолчанию 0.70, 0.20, 0.10). E = clamp(a*sex_score + b*... + c*..., -1, 1). Размещение: `hnh/sex/polarity.py`.
- [x] T007 [P] [US1] **W32 v1 и SexDelta32Engine**: константа W32_V1 (32 значения по FR-022), порядок осей по 002. Функция/класс: вход E, sex_strength=0.03, sex_max_param_delta=0.04; sex_delta[i] = clamp(sex_strength*E*W32[i], -sex_max_param_delta, +sex_max_param_delta). Выход tuple длины 32; гарантии BOUND-32-1, BOUND-AXIS-1. Размещение: `hnh/sex/delta_32.py` (или profiles.py + delta_32.py).

### Identity assembly и Agent

- [x] T008 [US1] **SexResolver (только explicit путь)**: вход birth_data (sex, sex_mode), config. Разрешение sex_mode (T002). В explicit: вернуть birth_data.sex (после валидации T001); если sex не передан — None. Пока без infer. Размещение: `hnh/sex/resolver.py`. Зависит от T001, T002.
- [x] T009 [US1] **Интеграция identity assembly в Agent**: в месте построения identity (например `_build_identity_config_from_natal` в `hnh/agent.py`) — вызвать SexResolver, при resolved_sex=None задать E=0 и sex_delta_32=(0,*32); иначе SexPolarityEngine → E, SexDelta32Engine → sex_delta_32. base_vector = natal_base + sex_delta_32 (поэлементно), clamp в [0,1] при необходимости. Передать этот base_vector в BehavioralCore. Зависит от T004–T008.
- [x] T010 [US1] **Выход Agent.step()**: расширить возвращаемое значение или last_step_output полями `sex` и `sex_polarity_E` (E). Не логировать sex/birth_data в открытом виде по умолчанию (FR-021a). Зависит от T009.

### Tests US1

- [x] T011 [P] [US1] Юнит-тесты SignPolarityEngine: формула, веса, отсутствующие планеты; SectEngine: высота и дома; SexPolarityEngine: формула E; SexDelta32Engine: W32 v1, границы (BOUND-32-1, BOUND-32-3, при желании BOUND-VEC-1: mean(|sex_delta|) ≤ sex_strength). В `tests/unit/test_008_sign_polarity.py`, `test_008_sect.py`, `test_008_polarity.py`, `test_008_delta_32.py`.
- [x] T012 [P] [US1] **Contract test (FR-022a)**: порядок осей и параметров W32 и sex_delta_32 MUST совпадать с каноническим 32D порядком из спеки 002 (индексы/имена осей). Тест: сравнение с эталоном из 002 или контракт-схемой. Размещение: `tests/unit/test_008_w32_contract.py` или `tests/contract/test_008_w32_order.py`. Зависит от T007.
- [x] T013 [US1] Юнит-тесты: невалидный sex → fail-fast (тип и сообщение); порядок разрешения sex_mode. В `tests/unit/test_008_resolver.py` или `test_008_validation.py`.
- [x] T014 [US1] Интеграционные тесты: identity с sex=male/female/None; base_vector включает sex_delta_32; одинаковые входы → одинаковый step() (детерминизм); sex_delta_32(male) ≈ -sex_delta_32(female) для одного натала. В `tests/integration/test_008_identity_sex.py`. Тесты уровня **Agent** (step() возвращает sex и sex_polarity_E, Agent с birth_data.sex, детерминизм step) — в `tests/unit/test_008_agent_sex.py`.

**Checkpoint**: US1 готов — явный пол, сдвиги в identity, вывод step() с sex и E, тесты проходят.

---

## Phase 3: User Story 2 — Deterministic sex inference (Priority: P2)

**Goal**: Режим infer: при отсутствии sex в birth_data — детерминированный вывод по sign_polarity_score и sect_score; tie-break по identity_hash; при недостатке натальных данных — только fail-fast (пропуск пола не допускается).

**Independent Test**: SexResolver дважды на одном натале + identity_hash — один и тот же пол; при недостатке данных и default "fail" — ошибка.

- [x] T015 [US2] **SexResolver infer путь**: при sex_mode="infer" и отсутствии sex — вычислить sign_polarity_score (SignPolarityEngine), sect_score (SectEngine). При недостатке данных — только **fail-fast** (raise); пропуск пола (sex=None) не допускается. S = k1*sign_polarity_score + k2*sect_score + bias; S > T → male, S < -T → female, иначе tie-break по младшему биту deterministic_hash(identity_hash). T=0.10, k1=1.0, k2=0.2, bias=0.0. Зависит от T004, T005, T008, T003.
- [x] T016 [US2] Передача **identity_hash** в конфиг/Agent при построении identity (для tie-break в infer). Источник identity_hash из T003. При недостатке натальных данных в infer — только fail. Зависит от T003, T009.
- [x] T017 [P] [US2] Юнит-тесты SexResolver infer: детерминизм при одинаковых natal+identity_hash; tie-break стабилен; при недостатке данных — только ошибка (fail-fast). В `tests/unit/test_008_resolver.py`.

**Checkpoint**: US2 готов — infer работает, тесты проходят.

---

## Phase 4: User Story 3 — Calibration guardrails (Priority: P3)

**Goal**: Скрипт калибровки по детерминированной синтетической популяции (фиксированный seed); пороги (mean diff, p95, overlap); CI при изменении W32/sex_strength.

**Independent Test**: Запуск скрипта на фиксированном seed — воспроизводимый результат; при нарушении порогов — падение.

- [x] T018 [US3] **Скрипт калибровки**: генерировать синтетическую популяцию (фиксированный seed, N напр. 10k, 50/50 sex); для каждого натала вызывать step(); считать по осям mean(axis_male - axis_female), p95, Cohen's d или overlap coefficient. Пороги: |mean diff| ≤ 0.01, p95 ≤ 0.10, перекрытие распределений (документировать формулу и пороги в скрипте/конфиге). При нарушении — exit non-zero. Размещение: `scripts/008/calibration_sanity.py` (или run_calibration.py). Зависит от T009.
- [x] T019 [US3] Документировать **запуск калибровки** (локально и в CI): seed, путь к скрипту, как добавить в CI при изменении sex_strength или W32. README в `scripts/008/` или в plan.md/spec.

**Checkpoint**: US3 готов — калибровка воспроизводима, пороги проверяются, CI описан.

---

## Phase 5: Polish & Constitution

- [x] T020 [P] **Логирование (FR-021a)**: убедиться, что по умолчанию sex и birth_data не пишутся в лог в открытом виде; при наличии opt-in audit/debug режима — документировать в коде/спеце.
- [x] T021 **Debug/output (FR-021)**: в режиме debug/research при необходимости выводить sign_polarity_score, sect, sect_score, sex_delta_32; не нарушать FR-021a.
- [x] T022 **Constitution**: Проверить Determinism (одинаковые входы → одинаковый step()), Identity/Core (sex в base_vector, не в step()), Logging (step output с sex и E; без plain sex/birth_data по умолчанию). Чеклист в plan § Constitution Check отметить по факту.
- [x] T023 [P] Обновить **quickstart.md** или README по 008: как передать sex и sex_mode, как запустить калибровку.

---

## Dependencies & Order

- **Phase 1** (T001–T003): сначала; без него не начинать US1/US2.
- **Phase 2** (T004–T014): после Phase 1; T004–T007 параллельно; T008 после T001,T002; T009 после T004–T008; T010 после T009; тесты T011–T014 после соответствующих реализаций; T012 (contract test W32) после T007.
- **Phase 3** (T015–T017): после T004, T005, T008, T003; T015 расширяет SexResolver; T016 — конфиг; T017 — тесты.
- **Phase 4** (T018–T019): после T009; скрипт и документация CI.
- **Phase 5** (T020–T023): после основных фаз; можно частично параллельно.

---

## Optional / Out of scope

- Возраст (spec 009).
- Изменение парсинга натала или системы домов.
- Новые UI/CLI кроме передачи sex/sex_mode и запуска калибровки.
