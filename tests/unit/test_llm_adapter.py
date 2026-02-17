"""LLM Adapter (Future): mock harness, behavioral vector injection, observable style shift."""

from __future__ import annotations

import pytest

from hnh.core.parameters import BehavioralVector
from hnh.interface.llm_adapter import LessonContext, MockLLMAdapter


def test_mock_adapter_same_vector_same_payload() -> None:
    """Same behavioral vector + context → same style payload."""
    adapter = MockLLMAdapter()
    v = BehavioralVector(
        warmth=0.5,
        strictness=0.4,
        verbosity=0.6,
        correction_rate=0.3,
        humor_level=0.5,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    p1 = adapter.format_style_payload(v)
    p2 = adapter.format_style_payload(v)
    assert p1 == p2
    assert "behavioral_vector" in p1
    assert "style_hint" in p1


def test_mock_adapter_different_vector_different_payload() -> None:
    """Different vector → different payload (observable style shift)."""
    adapter = MockLLMAdapter()
    v1 = BehavioralVector(
        warmth=0.2,
        strictness=0.8,
        verbosity=0.3,
        correction_rate=0.7,
        humor_level=0.2,
        challenge_intensity=0.8,
        pacing=0.3,
    )
    v2 = BehavioralVector(
        warmth=0.8,
        strictness=0.2,
        verbosity=0.8,
        correction_rate=0.2,
        humor_level=0.8,
        challenge_intensity=0.2,
        pacing=0.8,
    )
    p1 = adapter.format_style_payload(v1)
    p2 = adapter.format_style_payload(v2)
    assert p1["style_hint"] != p2["style_hint"]
    assert p1["behavioral_vector"] != p2["behavioral_vector"]


def test_adapter_with_lesson_context() -> None:
    """Adapter accepts lesson context; payload includes it."""
    adapter = MockLLMAdapter()
    v = BehavioralVector(
        warmth=0.5,
        strictness=0.5,
        verbosity=0.5,
        correction_rate=0.5,
        humor_level=0.5,
        challenge_intensity=0.5,
        pacing=0.5,
    )
    ctx = LessonContext(lesson_id="L1", topic="math", difficulty=0.7)
    payload = adapter.format_style_payload(v, lesson_context=ctx)
    assert payload["lesson_context"] == ctx.to_dict()


def test_adapter_with_relational_summary() -> None:
    """Adapter accepts relational summary in payload."""
    adapter = MockLLMAdapter()
    v = BehavioralVector(
        warmth=0.5,
        strictness=0.5,
        verbosity=0.5,
        correction_rate=0.5,
        humor_level=0.5,
        challenge_intensity=0.5,
        pacing=0.5,
    )
    summary = {"interaction_count": 10, "responsiveness_metric": 0.8}
    payload = adapter.format_style_payload(v, relational_summary=summary)
    assert payload["relational_summary"] == summary
