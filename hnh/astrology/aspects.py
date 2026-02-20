"""
Major aspects and orb configuration (v0.1).
Config-driven orbs; no hardcoded magic constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Major aspects: (name, angle_degrees)
MAJOR_ASPECTS = [
    ("Conjunction", 0.0),
    ("Opposition", 180.0),
    ("Trine", 120.0),
    ("Square", 90.0),
    ("Sextile", 60.0),
]

# Default orbs (degrees) per aspect — слегка расширены, чтобы больше аспектов давали вклад (меньше "тихих" осей)
DEFAULT_ORBS: dict[str, float] = {
    "Conjunction": 9.0,
    "Opposition": 9.0,
    "Trine": 9.0,
    "Square": 8.0,
    "Sextile": 7.0,
}


@dataclass(frozen=True)
class OrbConfig:
    """Конфигурация орбов по мажорным аспектам (явные значения, без магических констант)."""

    conjunction: float = 9.0
    opposition: float = 9.0
    trine: float = 9.0
    square: float = 8.0
    sextile: float = 7.0

    def get_orb(self, aspect_name: str) -> float:
        """Возвращает допустимый орб (в градусах) для аспекта по имени (Conjunction, Opposition и т.д.)."""
        orb_map = {
            "Conjunction": self.conjunction,
            "Opposition": self.opposition,
            "Trine": self.trine,
            "Square": self.square,
            "Sextile": self.sextile,
        }
        return orb_map.get(aspect_name, 6.0)

    def orbs_tuple(self) -> tuple[float, ...]:
        """Орбы в порядке MAJOR_ASPECTS (для быстрого доступа по индексу в цикле)."""
        return (
            self.conjunction,
            self.opposition,
            self.trine,
            self.square,
            self.sextile,
        )


def angular_separation(lon1: float, lon2: float) -> float:
    """Кратчайшая угловая дуга между двумя долготами в градусах (результат в диапазоне 0–180)."""
    a = lon1 % 360.0
    if a < 0:
        a += 360.0
    b = lon2 % 360.0
    if b < 0:
        b += 360.0
    diff = abs(a - b)
    if diff > 180.0:
        diff = 360.0 - diff  # берём меньшую дугу по кругу
    return diff


def detect_aspects(
    positions: list[dict[str, Any]],
    orb_config: OrbConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Находит мажорные аспекты между всеми парами позиций (например, натальная карта).
    Каждая позиция — dict с ключами "planet" и "longitude".
    Возвращает список словарей: planet1, planet2, aspect, angle, separation, within_orb.
    """
    orb_config = orb_config or OrbConfig()
    orbs = orb_config.orbs_tuple()  # один раз на весь вызов, доступ по индексу
    aspects_found: list[dict[str, Any]] = []
    for i, p1 in enumerate(positions):
        lon1 = p1["longitude"]
        planet1 = p1["planet"]
        for p2 in positions[i + 1 :]:  # noqa: E203  # только уникальные пары
            sep = angular_separation(lon1, p2["longitude"])
            for idx, (aspect_name, angle_deg) in enumerate(MAJOR_ASPECTS):
                orb = orbs[idx]
                if angle_deg == 0:  # Соединение: близко к 0° или к 360°
                    within = sep <= orb or (360.0 - sep) <= orb
                else:
                    within = abs(sep - angle_deg) <= orb
                if within:
                    aspects_found.append({
                        "planet1": planet1,
                        "planet2": p2["planet"],
                        "aspect": aspect_name,
                        "angle": angle_deg,
                        "separation": round(sep, 6),
                        "within_orb": True,
                    })
    return aspects_found


def aspects_between(
    positions_a: list[dict[str, Any]],
    positions_b: list[dict[str, Any]],
    orb_config: OrbConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Находит мажорные аспекты между двумя наборами позиций (например, транзиты и натал).
    Перебирает все пары (p из A, q из B). Формат позиций и результат — как у detect_aspects.
    """
    orb_config = orb_config or OrbConfig()
    orbs = orb_config.orbs_tuple()
    result: list[dict[str, Any]] = []
    for p1 in positions_a:
        lon1 = p1["longitude"]
        planet1 = p1["planet"]
        for p2 in positions_b:
            sep = angular_separation(lon1, p2["longitude"])
            for idx, (aspect_name, angle_deg) in enumerate(MAJOR_ASPECTS):
                orb = orbs[idx]
                if angle_deg == 0:  # Соединение
                    within = sep <= orb or (360.0 - sep) <= orb
                else:
                    within = abs(sep - angle_deg) <= orb
                if within:
                    result.append({
                        "planet1": planet1,
                        "planet2": p2["planet"],
                        "aspect": aspect_name,
                        "angle": angle_deg,
                        "separation": round(sep, 6),
                        "within_orb": True,
                    })
    return result
