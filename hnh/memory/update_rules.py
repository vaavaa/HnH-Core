"""
Deterministic update rules for Relational Memory.
Same event history → same derived metrics and behavioral modifier. No Identity mutation.
"""

from __future__ import annotations

from typing import Any

DIMENSION_NAMES = (
    "warmth",
    "strictness",
    "verbosity",
    "correction_rate",
    "humor_level",
    "challenge_intensity",
    "pacing",
)


def compute_derived(events: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Deterministic derived metrics from ordered events.
    Returns: interaction_count, error_rate, responsiveness_metric (0–1), etc.
    """
    n = len(events)
    error_count = sum(1 for e in events if e.get("type") == "error")
    error_rate = error_count / max(1, n)
    # Responsiveness: inverse of error rate, capped; or from payload if present
    responsiveness = 1.0 - min(1.0, error_rate * 1.5)
    return {
        "interaction_count": n,
        "error_count": error_count,
        "error_rate": round(error_rate, 6),
        "responsiveness_metric": round(responsiveness, 6),
    }


def compute_behavioral_modifier(events: list[dict[str, Any]]) -> dict[str, float]:
    """
    Map event history to a behavioral modifier vector (7 dims, all in [0, 1]).
    Deterministic: same events → same modifier. For Dynamic State input.
    """
    derived = compute_derived(events)
    n = derived["interaction_count"]
    err = derived["error_rate"]
    resp = derived["responsiveness_metric"]
    # Small shifts: more interactions → slightly more warmth/verbosity; higher error → more strictness
    warmth = 0.5 + (min(n, 20) / 20.0) * 0.1 - err * 0.2
    strictness = 0.5 + err * 0.3
    verbosity = 0.5 + (min(n, 10) / 10.0) * 0.05
    correction_rate = 0.5 + err * 0.2
    humor_level = 0.5 + resp * 0.1
    challenge_intensity = 0.5 + err * 0.15
    pacing = 0.5 + resp * 0.1
    out = {
        "warmth": max(0.0, min(1.0, warmth)),
        "strictness": max(0.0, min(1.0, strictness)),
        "verbosity": max(0.0, min(1.0, verbosity)),
        "correction_rate": max(0.0, min(1.0, correction_rate)),
        "humor_level": max(0.0, min(1.0, humor_level)),
        "challenge_intensity": max(0.0, min(1.0, challenge_intensity)),
        "pacing": max(0.0, min(1.0, pacing)),
    }
    return {k: round(v, 6) for k, v in out.items()}
