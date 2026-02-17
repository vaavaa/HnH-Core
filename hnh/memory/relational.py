"""
User-scoped Relational Memory: ordered events (sequence, type, payload).
Deterministic update rules; serializable snapshot; no Identity Core mutation.
"""

from __future__ import annotations

from typing import Any

from hnh.memory.update_rules import compute_behavioral_modifier, compute_derived


class RelationalMemory:
    """
    In-memory, user-scoped memory. One instance per user_id.
    Ordered list of events; each event: sequence (step), type, payload.
    """

    __slots__ = ("user_id", "_events")

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self._events: list[dict[str, Any]] = []

    def add_event(self, sequence: int, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """Append one event. Deterministic order preserved."""
        self._events.append({
            "sequence": sequence,
            "type": event_type,
            "payload": payload or {},
        })

    @property
    def events(self) -> list[dict[str, Any]]:
        """Ordered list of events (read-only view)."""
        return list(self._events)

    def derived_metrics(self) -> dict[str, Any]:
        """Deterministic derived metrics from current event history."""
        return compute_derived(self._events)

    def get_behavioral_modifier(self) -> dict[str, float]:
        """
        Behavioral modifier (7 dims, [0,1]) for Dynamic State input.
        Same history → same modifier. Reject not applicable here (we clamp in update_rules).
        """
        return compute_behavioral_modifier(self._events)

    def snapshot(self) -> dict[str, Any]:
        """
        Serializable snapshot for replay and inspection.
        Contains user_id, events, and derived metrics.
        """
        return {
            "user_id": self.user_id,
            "events": self.events,
            "derived": self.derived_metrics(),
            "behavioral_modifier": self.get_behavioral_modifier(),
        }
