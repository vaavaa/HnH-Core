"""
Behavioral vector: exactly 7 dimensions per spec 001.
All values in [0.0, 1.0]. Reject out-of-range; no clamping.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, field_validator


class BehavioralVector(BaseModel):
    """
    Fixed set of 7 normalized (0.0–1.0) dimensions for HnH v0.1.
    Spec: warmth, strictness, verbosity, correction_rate,
    humor_level, challenge_intensity, pacing.
    """

    warmth: float
    strictness: float
    verbosity: float
    correction_rate: float
    humor_level: float
    challenge_intensity: float
    pacing: float

    model_config = {"frozen": True}

    @field_validator(
        "warmth",
        "strictness",
        "verbosity",
        "correction_rate",
        "humor_level",
        "challenge_intensity",
        "pacing",
    )
    @classmethod
    def _reject_out_of_range(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            msg = "Behavioral dimension must be finite (no NaN or inf)"
            raise ValueError(msg)
        if not (0.0 <= v <= 1.0):
            msg = f"Behavioral dimension must be in [0.0, 1.0], got {v}"
            raise ValueError(msg)
        return v

    def __hash__(self) -> int:
        return hash(
            (
                self.warmth,
                self.strictness,
                self.verbosity,
                self.correction_rate,
                self.humor_level,
                self.challenge_intensity,
                self.pacing,
            )
        )

    def to_dict(self) -> dict[str, float]:
        """Stable dict for logging/serialization."""
        return {
            "warmth": self.warmth,
            "strictness": self.strictness,
            "verbosity": self.verbosity,
            "correction_rate": self.correction_rate,
            "humor_level": self.humor_level,
            "challenge_intensity": self.challenge_intensity,
            "pacing": self.pacing,
        }
