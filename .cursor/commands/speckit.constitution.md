---
description: Create or update the project constitution from interactive or provided principle inputs, ensuring all dependent templates stay in sync.
handoffs: 
  - label: Build Specification
    agent: speckit.specify
    prompt: Implement the feature specification based on the updated constitution. I want to build...
---

## User Input

<!--
Sync Impact Report
Version change: 1.0.1 → 1.0.2 (PATCH)
- Ratification/Last Amended dates corrected to 2025-02-17
- Templates aligned with HnH Constitution (Constitution Check / Alignment / Compliance)
Templates: plan, spec, tasks ✅ updated
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


You **MUST** consider the user input before proceeding (if not empty).

## Outline

You are updating the project constitution at `.specify/memory/constitution.md`. This file is a TEMPLATE containing placeholder tokens in square brackets (e.g. `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`). Your job is to (a) collect/derive concrete values, (b) fill the template precisely, and (c) propagate any amendments across dependent artifacts.

**Note**: If `.specify/memory/constitution.md` does not exist yet, it should have been initialized from `.specify/templates/constitution-template.md` during project setup. If it's missing, copy the template first.

Follow this execution flow:

1. Load the existing constitution at `.specify/memory/constitution.md`.
   - Identify every placeholder token of the form `[ALL_CAPS_IDENTIFIER]`.
   **IMPORTANT**: The user might require less or more principles than the ones used in the template. If a number is specified, respect that - follow the general template. You will update the doc accordingly.

2. Collect/derive values for placeholders:
   - If user input (conversation) supplies a value, use it.
   - Otherwise infer from existing repo context (README, docs, prior constitution versions if embedded).
   - For governance dates: `RATIFICATION_DATE` is the original adoption date (if unknown ask or mark TODO), `LAST_AMENDED_DATE` is today if changes are made, otherwise keep previous.
   - `CONSTITUTION_VERSION` must increment according to semantic versioning rules:
     - MAJOR: Backward incompatible governance/principle removals or redefinitions.
     - MINOR: New principle/section added or materially expanded guidance.
     - PATCH: Clarifications, wording, typo fixes, non-semantic refinements.
   - If version bump type ambiguous, propose reasoning before finalizing.

3. Draft the updated constitution content:
   - Replace every placeholder with concrete text (no bracketed tokens left except intentionally retained template slots that the project has chosen not to define yet—explicitly justify any left).
   - Preserve heading hierarchy and comments can be removed once replaced unless they still add clarifying guidance.
   - Ensure each Principle section: succinct name line, paragraph (or bullet list) capturing non‑negotiable rules, explicit rationale if not obvious.
   - Ensure Governance section lists amendment procedure, versioning policy, and compliance review expectations.

4. Consistency propagation checklist (convert prior checklist into active validations):
   - Read `.specify/templates/plan-template.md` and ensure any "Constitution Check" or rules align with updated principles.
   - Read `.specify/templates/spec-template.md` for scope/requirements alignment—update if constitution adds/removes mandatory sections or constraints.
   - Read `.specify/templates/tasks-template.md` and ensure task categorization reflects new or removed principle-driven task types (e.g., observability, versioning, testing discipline).
   - Read each command file in `.specify/templates/commands/*.md` (including this one) to verify no outdated references (agent-specific names like CLAUDE only) remain when generic guidance is required.
   - Read any runtime guidance docs (e.g., `README.md`, `docs/quickstart.md`, or agent-specific guidance files if present). Update references to principles changed.

5. Produce a Sync Impact Report (prepend as an HTML comment at top of the constitution file after update):
   - Version change: old → new
   - List of modified principles (old title → new title if renamed)
   - Added sections
   - Removed sections
   - Templates requiring updates (✅ updated / ⚠ pending) with file paths
   - Follow-up TODOs if any placeholders intentionally deferred.

6. Validation before final output:
   - No remaining unexplained bracket tokens.
   - Version line matches report.
   - Dates ISO format YYYY-MM-DD.
   - Principles are declarative, testable, and free of vague language ("should" → replace with MUST/SHOULD rationale where appropriate).

7. Write the completed constitution back to `.specify/memory/constitution.md` (overwrite).

8. Output a final summary to the user with:
   - New version and bump rationale.
   - Any files flagged for manual follow-up.
   - Suggested commit message (e.g., `docs: amend constitution to vX.Y.Z (principle additions + governance update)`).

Formatting & Style Requirements:

- Use Markdown headings exactly as in the template (do not demote/promote levels).
- Wrap long rationale lines to keep readability (<100 chars ideally) but do not hard enforce with awkward breaks.
- Keep a single blank line between sections.
- Avoid trailing whitespace.

If the user supplies partial updates (e.g., only one principle revision), still perform validation and version decision steps.

If critical info missing (e.g., ratification date truly unknown), insert `TODO(<FIELD_NAME>): explanation` and include in the Sync Impact Report under deferred items.

Do not create a new template; always operate on the existing `.specify/memory/constitution.md` file.
