<!--
Sync Impact Report
Version change: 1.0.1 → 1.0.2 (PATCH)
- Ratification/Last Amended dates corrected to 2025-02-17
- Templates aligned with HnH Constitution (Constitution Check / Alignment / Compliance)
Templates requiring updates:
- .specify/templates/plan-template.md ✅ updated
- .specify/templates/spec-template.md ✅ updated
- .specify/templates/tasks-template.md ✅ updated
Follow-up TODOs:
- Define structured logging format in specification phase
-->

# HnH Constitution

**Project Name:** HnH (Human Needs Human)  
**Constitution Version:** 1.0.2  
**Ratification Date:** 2025-02-17  
**Last Amended Date:** 2025-02-17  

---

## 1. Mission

HnH is an open-source deterministic personality simulation framework.

The system exists to simulate adaptive AI agent personalities through:

- Immutable Identity Core  
- Deterministic Dynamic State  
- Isolated Relational Memory  
- Explicit Behavioral Interface  

HnH is an engine.  
Language models are adapters, not the core system.

---

## 2. Architectural Invariants (Non-Negotiable)

### 2.1 Identity Core (Immutable)

The Identity Core:

- MUST be immutable after initialization.
- MUST be serializable.
- MUST be hashable.
- MUST NOT depend on runtime state.
- MUST define structured personality parameters.

Symbolic systems (e.g., natal charts) MAY be used as inputs,
but MUST map to measurable parameters.

---

### 2.2 Dynamic State (Deterministic)

Dynamic State:

- MUST be computed deterministically.
- MUST accept injected seed.
- MUST accept injected time.
- MUST NOT mutate Identity Core.
- MUST be replayable.

No hidden entropy sources allowed.

---

### 2.3 Relational Memory (Isolated)

Relational Memory:

- MUST be user-scoped.
- MUST NOT modify Identity Core.
- MUST expose explicit update rules.
- MUST be serializable.

No implicit behavioral mutation.

---

### 2.4 Behavioral Interface (Pure Mapping Layer)

Behavioral Interface:

- MUST NOT contain personality logic.
- MUST consume structured parameters.
- MAY connect to LLMs or rule engines.
- MUST remain replaceable.

LLM prompts MUST NOT embed hidden personality logic.

---

## 3. Deterministic Simulation Mode (MANDATORY)

HnH MUST implement a Deterministic Simulation Mode.

This mode guarantees:

- Reproducible personality behavior.
- Fixed seed replay.
- Identical outputs given identical inputs.

### Requirements:

- All randomness MUST be seeded.
- Seed MUST be injectable.
- Time MUST be injectable.
- State transitions MUST be logged.
- Simulation MUST be replayable step-by-step.

Non-deterministic code is prohibited in core modules.

---

## 4. Minimal Reference Implementation (MANDATORY)

The repository MUST contain a reference implementation that:

- Does NOT depend on any LLM.
- Does NOT call external APIs.
- Logs personality state transitions.
- Outputs structured behavioral parameters.
- Supports deterministic replay.

The exact structured logging format MUST be defined in the project specification,
not in this constitution.

This reference implementation defines canonical engine behavior.

---

## 5. Behavioral Parameterization

All symbolic constructs (including astrological elements)
MUST map to measurable parameters.

Allowed behavioral dimensions include:

- warmth
- strictness
- verbosity
- correction_rate
- humor_level
- challenge_intensity
- pacing

Symbolic-only logic is prohibited.

Mappings MUST be documented and test-covered.

---

## 6. Repository Engineering Standards

### 6.1 Single Language / Unified Style

The repository MUST maintain:

- One primary language.
- One formatter.
- One linter.
- One test framework.

No mixed core logic languages.

---

### 6.2 External Contracts

All external interfaces MUST be:

- Explicitly documented.
- Versioned.
- Covered by automated tests.

Includes:

- API schemas.
- Personality parameter formats.
- State transition inputs/outputs.

---

### 6.3 Test Coverage

Core personality engine logic MUST be:

- Deterministically testable.
- Seed-reproducible.
- Covered by unit tests.
- Covered by integration tests.

---

## 7. Observability & Debuggability

The engine MUST support:

- Identity snapshot export.
- State introspection.
- Deterministic replay mode.
- Parameter diffing between states.

No black-box transitions allowed.

---

## 8. Governance

### 8.1 Amendments

Changes to this constitution require:

- Pull Request.
- Explicit rationale.
- Architectural impact statement.
- Maintainer approval.

---

### 8.2 Versioning Policy

Semantic Versioning MUST be used:

- MAJOR: Incompatible architectural changes.
- MINOR: New principle or section added.
- PATCH: Clarifications or non-semantic edits.

---

### 8.3 Compliance Review

All feature specifications MUST include:

- Deterministic Mode compliance check.
- Identity/Core separation validation.
- Logging validation.

---

## 9. Ethical Guardrails

HnH MUST NOT:

- Claim real consciousness.
- Obfuscate artificial nature in documentation.
- Encourage emotional dependency design patterns.

Simulated subjectivity ≠ real personhood.

---

## 10. Non-Goals

HnH is not:

- A horoscope generator.
- A chatbot wrapper.
- A prompt engineering toolkit.
- A roleplay framework.

It is a deterministic personality simulation engine.
