"""
Planet: astronomical position (Spec 006). Immutable.
Sign from longitude: ZODIAC_SIGNS[int(longitude // 30)].
"""

from __future__ import annotations

from dataclasses import dataclass

# Sign index 0..11 → name (Aries=0, Pisces=11). Same order as zodiac_expression.
ZODIAC_SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def longitude_to_sign_index(longitude: float) -> int:
    """Longitude [0, 360) → sign index 0..11."""
    x = longitude % 360.0
    if x < 0:
        x += 360.0
    return int(x // 30) % 12


@dataclass(frozen=True)
class Planet:
    """
    Immutable planet: name, ecliptic longitude. Sign derived from longitude.
    house optional (filled when house system is used).
    """

    name: str
    longitude: float
    house: int | None = None

    @property
    def sign_index(self) -> int:
        """Sign index 0..11 (Aries=0, Pisces=11)."""
        return longitude_to_sign_index(self.longitude)

    @property
    def sign(self) -> str:
        """Sign name from ZODIAC_SIGNS[int(longitude // 30)]."""
        return ZODIAC_SIGNS[self.sign_index]
