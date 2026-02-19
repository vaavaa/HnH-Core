# Tasks: 004 — Planetary Core + Zodiac Expression Layer

**Input**: Design documents from `specs/004-planetary-core-zodiac-expression/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/sign-rulers.md

**Tests**: Spec 004 requires 99% coverage for zodiac modules and explicit tests (determinism, ruler influence, normalization [0,1], independence from behavioral state, replay consistency). Test tasks are included.

**Organization**: Phases follow plan Implementation Outline: Foundational (10 planets + houses) → Zodiac layer (Z 12×4 + dominant_*) → Logging → Tests → Polish.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 = 10 planets + houses, US2 = Zodiac layer 12×4, US3 = Logging + hash
- Include exact file paths in descriptions

## Path Conventions

- Package: `hnh/` (existing). New/updated: `hnh/astrology/ephemeris.py`, `hnh/astrology/houses.py`, `hnh/astrology/zodiac_expression.py`, `hnh/core/natal.py`, `hnh/astrology/transits.py`
- Tests: `tests/unit/` for unit tests; integration under `tests/integration/` if needed

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure dependencies and structure for 004; no new top-level project.

- [ ] T001 Verify pyswisseph supports 10 planets and house calculation (swe.calc_ut for Uranus/Neptune/Pluto; swe.houses) in hnh/astrology/ephemeris.py environment
- [ ] T002 [P] Implement angular strength from house using scale in specs/004-planetary-core-zodiac-expression/contracts/angular-strength.md (Angular=1.0, Succedent=0.6, Cadent=0.3)

---

## Phase 2: Foundational — 10 Planets & Houses (Blocking)

**Purpose**: Ephemeris extended to 10 planets; house calculation with default Placidus; natal and transit pipelines return sign, house, angular strength per planet. MUST be complete before Zodiac layer.

**Independent Test**: Given birth datetime (UTC) + lat/lon, natal output contains 10 planets, each with longitude, sign (0–11), house (1–12), and angular strength; same input → same output.

- [ ] T003 [US1] Extend PLANETS_NATAL to 10 planets (add Uranus, Neptune, Pluto with Swiss Ephemeris IDs 7,8,9) in hnh/astrology/ephemeris.py
- [ ] T004 [US1] Implement house cusp computation (Placidus default; JD + geolat + geolon → cusps, ascmc) in hnh/astrology/ephemeris.py or new hnh/astrology/houses.py
- [ ] T005 [US1] Implement longitude_to_house_number(lon, cusps) and assign house 1–12 per planet in hnh/astrology/ephemeris.py or hnh/astrology/houses.py
- [ ] T006 [US1] Add angular strength from house only (1,4,7,10 = angular; scale per contract) in hnh/astrology/ephemeris.py or hnh/astrology/houses.py
- [ ] T007 [US1] Update build_natal_positions to request 10 planets and houses; attach sign, house, angular_strength to each position in hnh/core/natal.py
- [ ] T008 [US1] Update compute_transit_signature to use 10 planets (and optionally houses for event chart) in hnh/astrology/transits.py

**Checkpoint**: Natal and transits output 10 planets with sign, house, angular strength. Deterministic.

---

## Phase 3: User Story 2 — Zodiac Expression Layer (12×4, dominant_*)

**Goal**: Compute sign_energy_vector (12×4), dominant_sign, dominant_element from positions and aspects; read-only; no impact on 32 params.

**Independent Test**: Same natal + time → same sign_energy_vector and dominant_sign/dominant_element; all values in [0,1]; no read of params_final/base.

- [ ] T009 [P] [US2] Implement SIGN_RULER (Modern default) from contracts/sign-rulers.md in hnh/astrology/zodiac_expression.py (or hnh/astrology/rulers.py)
- [ ] T010 [US2] Implement ruler strength from ruler planet position and aspects in hnh/astrology/zodiac_expression.py
- [ ] T011 [US2] Implement Z[sign] (12×4) from planetary_presence, ruler_strength, aspects, angular weighting, tension_vs_harmony per spec §4.2 input–dimension table; normalization [0,1]; sign with no planets: ruler+aspects only or (0,0,0,0) in hnh/astrology/zodiac_expression.py
- [ ] T012 [US2] Implement dominant_sign (sign with max intensity) and dominant_element (element with max sum of intensity over 3 signs) per spec §9 in hnh/astrology/zodiac_expression.py
- [ ] T013 [US2] Expose pure function or entry that returns sign_energy_vector, dominant_sign, dominant_element given positions (with sign/house/angular_strength) and aspects in hnh/astrology/zodiac_expression.py

**Checkpoint**: Zodiac layer produces 12×4 and dominant_* deterministically; no behavioral feedback.

---

## Phase 4: User Story 3 — Logging & zodiac_summary_hash

**Goal**: When zodiac is logged, include dominant_sign, dominant_element, sign_energy_vector, zodiac_summary_hash; hash = xxhash of deterministic serialization (orjson OPT_SORT_KEYS) per spec §9.1.

**Independent Test**: Same sign_energy_vector → same zodiac_summary_hash; hash present in log when zodiac output is written.

- [ ] T014 [US3] Implement zodiac_summary_hash(sign_energy_vector) using xxhash and orjson (OPT_SORT_KEYS) in hnh/astrology/zodiac_expression.py or hnh/logging/
- [ ] T015 [US3] Document exact hash input format (e.g. orjson.dumps(sign_energy_vector, option=orjson.OPT_SORT_KEYS)) in specs/004-planetary-core-zodiac-expression/contracts/ or data-model.md
- [ ] T016 [US3] Add optional zodiac fields (dominant_sign, dominant_element, sign_energy_vector, zodiac_summary_hash) to lifecycle log payload where state is logged in hnh/logging/ (e.g. state_logger_v2 or equivalent)

**Checkpoint**: Logs can carry zodiac output; replay consistency verifiable via zodiac_summary_hash.

---

## Phase 5: Tests (Spec §11 — 99% zodiac modules)

**Purpose**: 99% coverage for zodiac computation; determinism; normalization [0,1]; independence from behavioral state; replay consistency.

- [ ] T017 [P] Unit tests for 10 planets and house assignment (determinism, house 1–12, angular strength) in tests/unit/test_ephemeris_004.py or extend tests/unit/test_natal
- [ ] T018 [P] Unit tests for zodiac Z[sign] computation: deterministic output, ruler influence, normalization bounds [0,1], sign with no planets → (0,0,0,0) or ruler-only in tests/unit/test_zodiac_expression.py
- [ ] T019 [P] Unit tests for dominant_sign and dominant_element rules (max intensity; element = max sum intensity) in tests/unit/test_zodiac_expression.py
- [ ] T020 [P] Unit tests for zodiac_summary_hash: same vector → same hash; xxhash + orjson contract in tests/unit/test_zodiac_expression.py
- [ ] T021 Integration test: identical inputs (birth, time, config) → identical sign_energy_vector and zodiac_summary_hash across runs (replay consistency) in tests/integration/test_zodiac_replay.py or tests/unit/
- [ ] T022 Assert no behavioral state mutation: zodiac module does not read params_final/base; test or review in tests/unit/test_zodiac_expression.py
- [ ] T023 Achieve 99% coverage for hnh/astrology/zodiac_expression.py and house-related code (ephemeris/houses) per spec §11

**Checkpoint**: All spec §11 test requirements met; 99% coverage on zodiac modules.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T024 [P] Update quickstart.md or README if needed with 004 usage (natal with houses, zodiac output, hash) in specs/004-planetary-core-zodiac-expression/quickstart.md
- [ ] T025 Ensure sensitivity.py and delta.py use 10-planet positions where they reference Uranus/Neptune/Pluto (no stub longitudes) in hnh/identity/sensitivity.py and hnh/modulation/delta.py
- [ ] T026 Run quickstart.md validation: minimal path natal → zodiac → hash

### Constitution Compliance (HnH)

- [ ] T027 **Deterministic Mode**: Confirm zodiac path uses injected time only; no unseeded randomness; zodiac_summary_hash in log for replay
- [ ] T028 **Identity/Core separation**: Confirm zodiac layer is read-only; no writes to Identity Core or params_final
- [ ] T029 **Logging validation**: Optional zodiac fields and zodiac_summary_hash implemented and verifiable in logs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1. **Blocks** Phase 3 (Zodiac needs 10 planets + houses).
- **Phase 3 (Zodiac layer)**: Depends on Phase 2.
- **Phase 4 (Logging)**: Depends on Phase 3 (needs sign_energy_vector and hash).
- **Phase 5 (Tests)**: Depends on Phases 2–4; can start unit tests for Phase 2/3 as soon as those modules exist.
- **Phase 6 (Polish)**: Depends on Phases 2–5.

### Parallel Opportunities

- T002 can run in parallel with T001.
- Within Phase 2: T003, T004 can start in parallel; T005–T008 after cusps/assignments exist.
- Phase 3: T009 parallel; T010–T013 sequential per dependencies.
- Phase 5: T017–T020, T022 can run in parallel; T021 after implementation; T023 coverage gate last.

---

## Implementation Strategy

### MVP First (Foundational + Zodiac)

1. Complete Phase 1 (Setup).
2. Complete Phase 2 (10 planets + houses) → natal/transits output extended.
3. Complete Phase 3 (Zodiac layer) → sign_energy_vector, dominant_sign, dominant_element.
4. **STOP and VALIDATE**: Unit tests for ephemeris and zodiac; determinism check.
5. Add Phase 4 (logging) and Phase 5 (full tests) for release.

### Incremental Delivery

- After Phase 2: 10 planets and houses are available for downstream (002 pipeline can use them).
- After Phase 3: Zodiac interpretative output available (caller can log or display).
- After Phase 4: Replay-consistent logs with zodiac_summary_hash.
- After Phase 5: Spec §11 and 99% coverage satisfied.

---

## Notes

- [P] = parallelizable (different files or no dependency on same-phase incomplete tasks).
- [US1/US2/US3] maps to Foundational, Zodiac layer, Logging for traceability.
- Exact paths for new modules: `hnh/astrology/houses.py` and `hnh/astrology/zodiac_expression.py` (or under `hnh/core/` per team preference; plan says TBD in tasks — chosen astrology/ here).
- Contract sign-rulers.md already exists; angular strength scale to be added in Phase 1 (T002).
