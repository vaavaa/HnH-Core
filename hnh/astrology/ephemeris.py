"""
Planetary positions via Swiss Ephemeris (pyswisseph).
All times in UTC; datetime normalization and location validation.

Эфемериды: папка ephe в корне репозитория (файлы .se1 из github.com/aloistr/swisseph).
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# Путь к папке ephe в корне репозитория (жёстко)
_EPHE_PATH = str(Path(__file__).resolve().parent.parent.parent / "ephe")

try:
    import swisseph as swe
    swe.set_ephe_path(_EPHE_PATH)
except ImportError:
    swe = None  # type: ignore[assignment]

# Standard planet IDs for natal (Spec 004: 10 planets)
# Swiss Ephemeris: 0=Sun .. 6=Saturn, 7=Uranus, 8=Neptune, 9=Pluto
PLANETS_NATAL = [
    ("Sun", 0),
    ("Moon", 1),
    ("Mercury", 2),
    ("Venus", 3),
    ("Mars", 4),
    ("Jupiter", 5),
    ("Saturn", 6),
    ("Uranus", 7),
    ("Neptune", 8),
    ("Pluto", 9),
]

# Lat/lon bounds
LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0


def normalize_birth_datetime_utc(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: float = 0.0,
) -> datetime:
    """Собирает дату/время рождения в datetime в UTC. Входные компоненты считаются уже в UTC, конвертация часового пояса не выполняется."""
    return datetime(
        year, month, day, hour, minute, int(second), int((second % 1) * 1_000_000),
        tzinfo=timezone.utc,
    )


def validate_location(lat: float, lon: float) -> None:
    """Проверяет, что широта и долгота в допустимых границах (LAT_MIN..LAT_MAX, LON_MIN..LON_MAX). При выходе за границы выбрасывает ValueError."""
    if not (LAT_MIN <= lat <= LAT_MAX):
        raise ValueError(f"Latitude must be in [{LAT_MIN}, {LAT_MAX}], got {lat}")
    if not (LON_MIN <= lon <= LON_MAX):
        raise ValueError(f"Longitude must be in [{LON_MIN}, {LON_MAX}], got {lon}")


def datetime_to_julian_utc(dt: datetime) -> float:
    """Переводит datetime в юлианский день (UT) для Swiss Ephemeris. Если передан не UTC — предварительно приводит к UTC."""
    if swe is None:
        raise RuntimeError("pyswisseph is not installed; install with pip install hnh[astrology]")
    if dt.tzinfo is not None and dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)
    ut = dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + dt.microsecond / 3600e6
    jd = swe.julday(dt.year, dt.month, dt.day, ut)
    return jd


def compute_positions(jd_ut: float) -> list[dict[str, Any]]:
    """
    Считает эклиптические долготы 10 планет (Sun..Pluto) на заданный юлианский день UT.
    Возвращает список словарей {"planet": str, "longitude": float} в фиксированном порядке.
    """
    if swe is None:
        raise RuntimeError("pyswisseph is not installed; install with pip install hnh[astrology]")
    result: list[dict[str, Any]] = [None] * len(PLANETS_NATAL)  # предварительный размер — без роста списка
    for i, (name, pid) in enumerate(PLANETS_NATAL):
        xx, _ = swe.calc_ut(jd_ut, pid)
        result[i] = {"planet": name, "longitude": float(xx[0])}
    return result
