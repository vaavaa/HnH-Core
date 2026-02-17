"""
Logging contracts: aligned with specs/001-deterministic-personality-engine/contracts/.
Behavioral vector schema and state log record contract.
"""

from __future__ import annotations

from hnh.core.parameters import BehavioralVector

__all__ = ["BehavioralVector", "STATE_LOG_REQUIRED_FIELDS"]

# Minimal contract from spec: required fields per state transition log record
STATE_LOG_REQUIRED_FIELDS = (
    "seed",
    "injected_time",
    "identity_hash",
    "active_modifiers",
    "final_behavioral_vector",
)
