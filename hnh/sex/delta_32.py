"""
SexDelta32Engine and W32 profile v1 (Spec 008, FR-016, FR-017, FR-022).
Order matches canonical 32D parameter order (spec 002): 8 axes × 4 sub-parameters.
"""

from __future__ import annotations

# FR-022: W32 v1 exact values (8 axes × 4)
# Axis 1 Emotional Tone, 2 Stability & Regulation, ... 8 Motivation & Drive
W32_V1: tuple[int, ...] = (
    # Axis 1 — Emotional Tone (warmth, empathy, patience, emotional_intensity)
    -1, -1, -1, +1,
    # Axis 2 — Stability & Regulation
    +1, +1, -1, +1,
    # Axis 3 — Cognitive Style
    -1, +1, -1, +1,
    # Axis 4 — Structure & Discipline
    +1, -1, -1, +1,
    # Axis 5 — Communication Style
    -1, +1, -1, -1,
    # Axis 6 — Teaching Style
    +1, +1, -1, -1,
    # Axis 7 — Power & Boundaries
    +1, +1, -1, +1,
    # Axis 8 — Motivation & Drive
    +1, -1, +1, -1,
)

DEFAULT_SEX_STRENGTH: float = 0.03
DEFAULT_SEX_MAX_PARAM_DELTA: float = 0.04


def compute_sex_delta_32(
    E: float,
    w32: tuple[int | float, ...] | None = None,
    *,
    sex_strength: float = DEFAULT_SEX_STRENGTH,
    sex_max_param_delta: float = DEFAULT_SEX_MAX_PARAM_DELTA,
) -> tuple[float, ...]:
    """
    FR-017: sex_delta[i] = clamp(sex_strength * E * W32[i], -sex_max_param_delta, +sex_max_param_delta).
    Returns tuple of 32 floats. BOUND-32-1/32-3: |sex_delta[i]| <= sex_max_param_delta.
    """
    if w32 is None:
        w32 = W32_V1
    if len(w32) != 32:
        raise ValueError(f"W32 must have length 32, got {len(w32)}")
    out: list[float] = []
    for i in range(32):
        raw = sex_strength * E * w32[i]
        clamped = max(-sex_max_param_delta, min(sex_max_param_delta, raw))
        out.append(clamped)
    return tuple(out)
