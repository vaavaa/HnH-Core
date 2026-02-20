"""
Транзитные позиции и аспекты транзит–натал.
TransitEngine: state(date, config) -> TransitState (Spec 006). Stateless; deterministic.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from hnh.astrology import aspects as asp
from hnh.astrology import ephemeris as eph
from hnh.astrology.transit_state import TransitState

from hnh.config.replay_config import ReplayConfig
from hnh.lifecycle.stress import compute_transit_stress
from hnh.modulation.boundaries import apply_bounds
from hnh.modulation.delta import compute_raw_delta_32


def _date_to_datetime_utc(d: date | datetime) -> datetime:
    """Normalize date or datetime to UTC datetime (noon if date only)."""
    if isinstance(d, datetime):
        if d.tzinfo is None:
            return d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    return datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=timezone.utc)


class TransitEngine:
    """
    Stateless transit layer: state(date, config) -> TransitState.
    Takes NatalChart; does not store behavioral state. Contract: contracts/transit-engine.md.
    """

    __slots__ = ("_natal",)

    def __init__(self, natal: Any) -> None:
        """natal: NatalChart (or object with to_natal_data())."""
        self._natal = natal

    def state(self, date_or_dt: date | datetime, config: ReplayConfig) -> TransitState:
        """
        Single output for date: stress, raw_delta, bounded_delta.
        Deterministic: same (natal, date, config) -> same TransitState.
        """
        dt = _date_to_datetime_utc(date_or_dt)
        natal_data = self._natal.to_natal_data() if hasattr(self._natal, "to_natal_data") else self._natal
        sig = compute_transit_signature(dt, natal_data)
        aspects = sig.get("aspects_to_natal", [])
        i_t, s_t = compute_transit_stress(aspects)
        stress = max(0.0, min(1.0, s_t))
        raw_delta = compute_raw_delta_32(aspects)
        shock_active = max(abs(r) for r in raw_delta) > config.shock_threshold
        bounded_delta, _ = apply_bounds(raw_delta, config, shock_active)
        return TransitState(stress=stress, raw_delta=raw_delta, bounded_delta=bounded_delta)


def compute_transit_signature(
    injected_time_utc: datetime,
    natal_positions: dict[str, Any],
    orb_config: asp.OrbConfig | None = None,
) -> dict[str, Any]:
    """
    Строит детерминированную транзитную сигнатуру для заданного времени и натальных позиций.
    Одинаковые время и натал дают один и тот же вывод. Системные часы не используются.
    Positions: 10 планет (Spec 004) с долготой до 6 знаков. Возвращает: timestamp_utc, jd_ut, positions, aspects_to_natal.
    """
    if injected_time_utc.tzinfo is None:
        injected_time_utc = injected_time_utc.replace(tzinfo=timezone.utc)
    elif injected_time_utc.tzinfo != timezone.utc:
        injected_time_utc = injected_time_utc.astimezone(timezone.utc)
    jd_ut = eph.datetime_to_julian_utc(injected_time_utc)
    transit_positions = eph.compute_positions(jd_ut)
    n_pos = len(transit_positions)
    transit_rounded: list[dict[str, Any]] = [None] * n_pos  # один раз по размеру, без роста списка
    for i in range(n_pos):
        p = transit_positions[i]
        transit_rounded[i] = {"planet": p["planet"], "longitude": round(p["longitude"], 6)}
    natal_pos_list = natal_positions.get("positions", [])
    aspects_to_natal = asp.aspects_between(transit_positions, natal_pos_list, orb_config)
    return {
        "timestamp_utc": injected_time_utc.isoformat(),
        "jd_ut": round(jd_ut, 6),
        "positions": transit_rounded,
        "aspects_to_natal": aspects_to_natal,
    }
