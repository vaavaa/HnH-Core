# Research: 001 Deterministic Personality Engine

**Feature**: 001-deterministic-personality-engine  
**Date**: 2025-02-17  

---

## 1. Language & Runtime

**Decision**: Python 3.12+

**Rationale**: Детерминизм удобно контролировать; богатая экосистема (pydantic, pytest, при необходимости pyswisseph); типизация и тесты на уровне индустрии.

**Alternatives considered**: Rust (сложнее итерация, меньше готовых биндингов для астрологии); Go (менее удобная модель данных для контрактов).

---

## 2. Data Contracts

**Decision**: Pydantic v2 для всех публичных контрактов (Identity Core, Dynamic State, Behavioral Vector, Log record, Relational Memory snapshot).

**Rationale**: Валидация на границах, сериализация/десериализация, совместимость со spec (reject вне [0,1], обязательные поля). Dataclasses — где внутренние структуры без нужды в валидации.

**Alternatives considered**: Только dataclasses (слабее валидация); ручные проверки (больше кода и риска расхождения со спекой).

---

## 3. Astrology (optional)

**Decision**: pyswisseph (Swiss Ephemeris) как опциональная зависимость для natal/transit; локальная библиотека, не сетевой API. Соответствует «optional symbolic_input» в спеке.

**Rationale**: Широко используется, детерминированные расчёты при фиксированной дате/времени/месте. Для reference implementation 001 можно обойтись без неё (base_traits задаются напрямую).

**Alternatives considered**: Другие эфемериды; отложить астрологию до следующей фичи.

---

## 4. Logging Format

**Decision**: JSON Lines (одна строка — один JSON-объект на переход состояния). Поля из spec: seed, injected_time, identity_hash, active_modifiers, final_behavioral_vector; при необходимости добавляются transit_signature, relational_snapshot_hash.

**Rationale**: Diffable, парсится по строкам, удобен для replay и тестов. structlog или stdlib logging с JSON-сериализатором.

**Alternatives considered**: Чистый CSV (менее гибко); бинарный формат (сложнее отладка).

---

## 5. Testing Strategy

**Decision**: pytest + pytest-cov; контрактные тесты на границах (Identity, State, Log); интеграционные тесты на replay (одинаковые входы → одинаковый вывод); unit на модулях без I/O. Цель 90%+ по ядру (spec FR-013).

**Rationale**: Соответствие конституции и спеке; воспроизводимость и детерминизм проверяются автоматически.

---

## 6. Determinism Guarantees

**Decision**: Все входы времени и случайности — только через явную инжекцию (параметры функций/конструкторов). В ядре запрещены datetime.now(), random без seed, неконтролируемые float-операции. Конфиг (орбы, веса) версионируется и загружается явно.

**Rationale**: Требования конституции и спеки; воспроизводимость replay и тестов.
