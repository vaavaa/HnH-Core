"""
Транзитные позиции и аспекты транзит–натал.
Время только инжектируется (без datetime.now()); результат детерминирован.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hnh.astrology import aspects as asp
from hnh.astrology import ephemeris as eph


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
