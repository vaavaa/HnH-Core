"""
Natal-derived sensitivity computation (Spec 002).
Pure function: natal_data → 32-dim vector in [0, 1]. No randomness.
T2.1 Modality weighting, T2.2 Saturn stabilization, T2.3 Uranus disruption, T2.4 Normalize.
"""

from __future__ import annotations

from typing import Any

from hnh.identity.schema import (
    AXES,
    NUM_PARAMETERS,
    PARAMETERS,
    _PARAMETER_LIST,
    get_axis_index,
)

# Предвычисление: ось → индексы параметров (4 на ось), чтобы не перебирать все 32 в цикле по планетам
_AXIS_TO_PARAM_IX: tuple[tuple[int, ...], ...] = tuple(
    tuple(p_ix for p_ix, (ax_ix, _) in enumerate(_PARAMETER_LIST) if ax_ix == a)
    for a in range(8)
)

# --- Modality (T2.1): sign index 0..11 → cardinal/fixed/mutable ------------------------------
# Signs: 0=Aries, 1=Taurus, ... 11=Pisces. Modality: 0=cardinal, 1=fixed, 2=mutable.
_SIGN_MODALITY: tuple[int, ...] = (
    0,  # Aries   cardinal
    1,  # Taurus  fixed
    2,  # Gemini  mutable
    0,  # Cancer  cardinal
    1,  # Leo     fixed
    2,  # Virgo   mutable
    0,  # Libra   cardinal
    1,  # Scorpio fixed
    2,  # Sagittarius mutable
    0,  # Capricorn cardinal
    1,  # Aquarius fixed
    2,  # Pisces  mutable
)
# Weights for modality contribution: cardinal=0.6, fixed=0.5, mutable=0.7 (mutable → slightly higher sensitivity)
_MODALITY_WEIGHT: tuple[float, ...] = (0.6, 0.5, 0.7)

# Planet → primary axis index (0..7) for prominence
_PLANET_AXIS: dict[str, int] = {
    "Sun": get_axis_index("motivation_drive"),      # 7
    "Moon": get_axis_index("emotional_tone"),       # 0
    "Mercury": get_axis_index("communication_style"),  # 4
    "Venus": get_axis_index("emotional_tone"),      # 0
    "Mars": get_axis_index("power_boundaries"),     # 6
    "Jupiter": get_axis_index("teaching_style"),    # 5
    "Saturn": get_axis_index("stability_regulation"),  # 1
    "Uranus": get_axis_index("cognitive_style"),    # 2
}


def _longitude_to_sign_index(lon: float) -> int:
    """Longitude [0, 360) → sign index 0..11."""
    deg = lon % 360.0
    return int(deg / 30.0) % 12


def _modality_weight_for_longitude(lon: float) -> float:
    """T2.1: Map longitude to modality weight (deterministic)."""
    sign_ix = _longitude_to_sign_index(lon)
    mod_ix = _SIGN_MODALITY[sign_ix]
    return _MODALITY_WEIGHT[mod_ix]


def _saturn_stabilization_factor(positions: list[dict[str, Any]]) -> float:
    """
    T2.2: Saturn strength reduces sensitivity.
    Return factor in (0, 1]: 1.0 = no Saturn, lower = stronger Saturn (e.g. angular/conjunct).
    """
    return _saturn_factor_from_map(
        {p["planet"]: float(p["longitude"]) for p in positions if p.get("planet")}
    )


def _saturn_factor_from_map(positions_by_planet: dict[str, float]) -> float:
    """T2.2 по словарю планета → долгота (избегаем повторного скана списка)."""
    lon = positions_by_planet.get("Saturn")
    if lon is None:
        return 1.0
    sign_ix = _longitude_to_sign_index(lon)
    mod_ix = _SIGN_MODALITY[sign_ix]
    if mod_ix == 0:
        return 0.75
    if mod_ix == 1:
        return 0.85
    return 0.90


def _uranus_disruption_factor(positions: list[dict[str, Any]]) -> float:
    """
    T2.3: Uranus strength increases sensitivity.
    Return multiplier >= 1.0; 1.0 = no Uranus or weak.
    """
    return _uranus_factor_from_map(
        {p["planet"]: float(p["longitude"]) for p in positions if p.get("planet")}
    )


def _uranus_factor_from_map(positions_by_planet: dict[str, float]) -> float:
    """T2.3 по словарю планета → долгота."""
    lon = positions_by_planet.get("Uranus")
    if lon is None:
        return 1.0
    sign_ix = _longitude_to_sign_index(lon)
    mod_ix = _SIGN_MODALITY[sign_ix]
    if mod_ix == 1:
        return 1.25
    if mod_ix == 0:
        return 1.15
    return 1.10


def _aspect_tension_score(aspects: list[Any]) -> float:
    """
    Aggregate aspect tension (squares/oppositions increase, trines/sextiles decrease).
    Returns value in [0, 1] for use in raw sensitivity.
    """
    if not aspects:
        return 0.5
    tension = 0.0
    for asp in aspects:
        name = (asp.get("aspect") or asp.get("name") or "").lower()
        if "square" in name or "opposition" in name:
            tension += 0.2
        elif "trine" in name or "sextile" in name:
            tension += 0.05
        else:
            tension += 0.1
    # Normalize to [0, 1] (cap at 1.0)
    return min(1.0, tension / max(len(aspects), 1) * 3.0)


def compute_sensitivity(natal_data: dict[str, Any]) -> tuple[float, ...]:
    """
    Compute 32-dim sensitivity vector from natal_data (positions + optional aspects).
    Deterministic, no randomness. Output normalized to [0, 1] (T2.4).
    """
    positions = natal_data.get("positions") or []
    aspects = natal_data.get("aspects") or []

    # Один проход: словарь планета → долгота (для Saturn/Uranus и модальности)
    positions_by_planet = {p["planet"]: float(p["longitude"]) for p in positions if p.get("planet")}

    raw = [0.5] * NUM_PARAMETERS

    # Modality: только параметры нужной оси (через _AXIS_TO_PARAM_IX)
    for planet, lon in positions_by_planet.items():
        axis_ix = _PLANET_AXIS.get(planet)
        if axis_ix is None:
            continue
        weight = _modality_weight_for_longitude(lon)
        delta = (weight - 0.5) * 0.2
        for p_ix in _AXIS_TO_PARAM_IX[axis_ix]:
            raw[p_ix] += delta

    tension = _aspect_tension_score(aspects)
    tension_delta = (tension - 0.5) * 0.1
    for p_ix in range(NUM_PARAMETERS):
        raw[p_ix] += tension_delta

    # Saturn и Uranus: один общий множитель, один проход по raw
    combined_f = _saturn_factor_from_map(positions_by_planet) * _uranus_factor_from_map(
        positions_by_planet
    )
    for p_ix in range(NUM_PARAMETERS):
        raw[p_ix] *= combined_f

    # T2.4 Нормализация: один проход min/max
    min_r = max_r = raw[0]
    for x in raw[1:]:
        if x < min_r:
            min_r = x
        elif x > max_r:
            max_r = x
    if max_r <= min_r:
        return tuple(0.5 for _ in range(NUM_PARAMETERS))
    scale = 1.0 / (max_r - min_r)
    result = tuple((x - min_r) * scale for x in raw)
    # Нижний порог чувствительности для ~40% параметров — меньше "тихих" осей (детерминированно)
    SENSITIVITY_FLOOR = 0.53
    _FLOOR_INDICES = (0, 3, 5, 8, 10, 13, 15, 18, 20, 23, 25, 28, 30)  # 13 из 32
    result_list = list(result)
    for i in _FLOOR_INDICES:
        if result_list[i] < SENSITIVITY_FLOOR:
            result_list[i] = SENSITIVITY_FLOOR
    return tuple(result_list)


def sensitivity_histogram(sensitivity_vector: tuple[float, ...]) -> dict[str, Any]:
    """
    Debug: distribution statistics (e.g. histogram) for sensitivity vector.
    Spec: expose in debug mode. Returns counts in buckets and basic stats.
    """
    if not sensitivity_vector:
        return {
            "histogram": {},
            "low_sensitivity_pct": 0.0,
            "high_sensitivity_pct": 0.0,
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
        }
    buckets: dict[str, int] = {"0.00-0.25": 0, "0.25-0.50": 0, "0.50-0.75": 0, "0.75-1.00": 0}
    min_v = max_v = sensitivity_vector[0]
    total = 0.0
    for s in sensitivity_vector:
        total += s
        if s < min_v:
            min_v = s
        elif s > max_v:
            max_v = s
        if s < 0.25:
            buckets["0.00-0.25"] += 1
        elif s < 0.5:
            buckets["0.25-0.50"] += 1
        elif s < 0.75:
            buckets["0.50-0.75"] += 1
        else:
            buckets["0.75-1.00"] += 1
    n = len(sensitivity_vector)
    low_count = buckets["0.00-0.25"] + buckets["0.25-0.50"]
    high_count = buckets["0.50-0.75"] + buckets["0.75-1.00"]
    return {
        "histogram": dict(buckets),
        "low_sensitivity_pct": round(100.0 * low_count / n, 2),
        "high_sensitivity_pct": round(100.0 * high_count / n, 2),
        "min": min_v,
        "max": max_v,
        "mean": total / n,
    }
