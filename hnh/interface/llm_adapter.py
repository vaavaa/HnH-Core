"""
LLM Behavioral Adapter (Future): inject behavioral vector into LLM-facing layer.
Personality logic stays in engine; adapter only formats style payload for external LLM.
Optional; mock implementation for tests.
"""

from __future__ import annotations

from typing import Any, Protocol

from hnh.core.parameters import BehavioralVector


class LessonContext:
    """Minimal lesson context for Teacher scenario."""

    def __init__(
        self,
        lesson_id: str,
        topic: str,
        difficulty: float = 0.5,
    ) -> None:
        self.lesson_id = lesson_id
        self.topic = topic
        self.difficulty = difficulty  # 0–1

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "topic": self.topic,
            "difficulty": self.difficulty,
        }


class LLMAdapter(Protocol):
    """Protocol: inject behavioral vector and optional context; return style payload for LLM."""

    def format_style_payload(
        self,
        behavioral_vector: BehavioralVector,
        relational_summary: dict[str, Any] | None = None,
        lesson_context: LessonContext | None = None,
    ) -> dict[str, Any]:
        """Build style payload (hints, params) for external LLM. No API call here."""
        ...


class MockLLMAdapter:
    """
    Deterministic mock: same vector + context → same payload.
    Different vector → different payload (observable style shift for tests).
    """

    def format_style_payload(
        self,
        behavioral_vector: BehavioralVector,
        relational_summary: dict[str, Any] | None = None,
        lesson_context: LessonContext | None = None,
    ) -> dict[str, Any]:
        """Deterministic style payload from vector and context."""
        v = behavioral_vector.to_dict()
        payload: dict[str, Any] = {
            "behavioral_vector": v,
            "style_hint": _vector_to_style_hint(v),
        }
        if relational_summary:
            payload["relational_summary"] = relational_summary
        if lesson_context:
            payload["lesson_context"] = lesson_context.to_dict()
        return payload


def _vector_to_style_hint(v: dict[str, float]) -> str:
    """Stable string hint from vector (for mock; observable when vector changes)."""
    parts = [f"{k}={v[k]:.2f}" for k in sorted(v.keys())]
    return "|".join(parts)
