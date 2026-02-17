# Constitution Compliance Checklist (v0.1)

**Spec**: 001-deterministic-personality-engine §6  
**Date**: 2025-02-17

---

- [x] **Identity Core immutable** — enforced in `hnh/core/identity.py` (frozen model); tests in `tests/unit/test_identity.py`.
- [x] **Dynamic State deterministic** — same inputs → same output; tests in `tests/unit/test_modulation.py`, `tests/integration/test_dynamic_state.py`.
- [x] **Seed injection supported** — `run_step(identity, time, seed=...)`; CLI `--seed`.
- [x] **Time injection supported** — all core code uses injected datetime; no `datetime.now()` in core (test in `tests/unit/test_constitution.py`).
- [x] **Logging implemented** — structured, diffable, JSON Lines; `hnh/logging/state_logger.py`; contract in `contracts/state-log-spec.md`.
- [x] **Replay mode implemented** — `hnh/state/replay.py` `run_step`; step-by-step, no system clock; CLI `--replay`.
- [x] **No LLM dependency** — core has no LLM; spec 001 out-of-scope.
- [x] **External contracts documented** — behavioral vector and state log in `contracts/`; state-log-spec.md, behavioral-vector.json.

**Deterministic Mode**: Seed/time injection and replay verified; no unseeded randomness (test: `test_no_unseeded_random_in_core_modules`).  
**Identity/Core separation**: Identity immutable; Dynamic State and Relational Memory do not mutate Core.  
**Logging validation**: State transitions logged; observability via state_logger and replay.
