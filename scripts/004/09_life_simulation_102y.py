#!/usr/bin/env python3
"""
004: Симуляция многих жизней — случайные даты рождения (от Рождества до сегодня), Лондон.

Берём N случайных дат в диапазоне 0001-12-25 .. сегодня. Для каждой даты — жизнь
со случайной длительностью 70–108 лет; каждый день два расчёта (утро/вечер UTC),
натал и транзиты для Лондона. Как в 002: дельты по осям на каждую жизнь.
Дополнительно (004): натальный зодиак (dominant_sign, dominant_element, zodiac_summary_hash),
дома (ascendant, mc), транзитный зодиак в начале и в конце жизни.

Запуск из корня проекта (venv активирован):
  python scripts/004/09_life_simulation_102y.py
  python scripts/004/09_life_simulation_102y.py --lives 50 --seed 42
  python scripts/004/09_life_simulation_102y.py --lives 5 --days 365   # быстрый тест
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any

import orjson
import xxhash

from hnh.astrology import aspects as asp
from hnh.astrology import ephemeris as eph
from hnh.astrology import houses as hou
from hnh.astrology import zodiac_expression as ze
from hnh.config.replay_config import ReplayConfig
from hnh.identity import IdentityCore
from hnh.identity.schema import AXES, NUM_PARAMETERS, _registry
from hnh.state.replay_v2 import run_step_v2

# Лондон
LONDON_LAT = 51.5074
LONDON_LON = -0.1278
DATE_FIRST = date(1, 12, 25)
TIME_SLOTS = [(6, 0), (18, 0)]
LIFESPAN_MIN = 70
LIFESPAN_MAX = 108


def _zodiac_summary_hash(sign_energy_vector: list[tuple[float, float, float, float]]) -> str:
    """Хеш от sign_energy_vector для replay (Spec 004 §9.1)."""
    blob = orjson.dumps(sign_energy_vector, option=orjson.OPT_SORT_KEYS)
    return xxhash.xxh3_128(blob).hexdigest()


def _transit_chart(dt_utc: datetime, lat: float, lon: float) -> dict[str, Any] | None:
    """Транзитная карта на момент dt_utc: позиции 10 планет с домами и аспекты между транзитами."""
    try:
        eph.validate_location(lat, lon)
        jd = eph.datetime_to_julian_utc(dt_utc)
        positions = eph.compute_positions(jd)
        positions_round = [{"planet": p["planet"], "longitude": round(p["longitude"], 6)} for p in positions]
        cusps, ascmc = hou.compute_houses(jd, lat, lon)
        positions_with_houses = hou.assign_houses_and_strength(positions_round, cusps)
        aspects_list = asp.detect_aspects(positions, None)
        return {
            "positions": positions_with_houses,
            "aspects": aspects_list,
            "houses": {"cusps": list(cusps), "ascendant": ascmc[0] if ascmc else None, "mc": ascmc[1] if len(ascmc) > 1 else None},
        }
    except Exception:
        return None


def _build_natal(birth_date: date) -> dict[str, Any] | None:
    """Натальная карта 004 на дату рождения, Лондон."""
    try:
        from hnh.core.natal import build_natal_positions
    except Exception:
        return None
    birth_dt = datetime(
        birth_date.year, birth_date.month, birth_date.day,
        12, 0, 0, 0, tzinfo=timezone.utc,
    )
    try:
        return build_natal_positions(birth_dt, LONDON_LAT, LONDON_LON)
    except Exception:
        return None


def _end_date_for_lifespan(birth: date, years: int) -> date:
    try:
        end = date(birth.year + years, birth.month, birth.day)
    except ValueError:
        end = date(birth.year + years, 2, 28)
    return end


def _run_one_life(
    birth_date: date,
    lifespan_years: int,
    config: ReplayConfig,
    use_astrology: bool,
    life_index: int,
    max_days: int | None = None,
) -> dict[str, Any] | None:
    """
    Один проход жизни. Возвращает словарь с дельтами осей и 004-параметрами,
    либо None при ошибке.
    """
    end_date = _end_date_for_lifespan(birth_date, lifespan_years)
    if max_days is not None:
        capped = birth_date + timedelta(days=max_days)
        if capped < end_date:
            end_date = capped

    natal = _build_natal(birth_date) if use_astrology else None
    identity_id = f"life-004-{life_index}-{birth_date.isoformat()}"
    _registry.discard(identity_id)
    identity = IdentityCore(
        identity_id=identity_id,
        base_vector=(0.5,) * NUM_PARAMETERS,
        sensitivity_vector=(0.5,) * NUM_PARAMETERS,
    )
    memory_delta = (0.0,) * NUM_PARAMETERS
    memory_signature = ""

    start_params: tuple[float, ...] | None = None
    start_axis: tuple[float, ...] | None = None
    end_params: tuple[float, ...] | None = None
    end_axis: tuple[float, ...] | None = None

    phase_state: dict[str, tuple[float, ...]] = {
        "personal": (0.0,) * NUM_PARAMETERS,
        "social": (0.0,) * NUM_PARAMETERS,
        "outer": (0.0,) * NUM_PARAMETERS,
    }
    first_dt: datetime | None = None
    last_dt: datetime | None = None
    current = birth_date

    while current <= end_date:
        for hour, minute in TIME_SLOTS:
            dt_utc = datetime(
                current.year, current.month, current.day,
                hour, minute, 0, 0, tzinfo=timezone.utc,
            )
            result = run_step_v2(
                identity,
                config,
                dt_utc,
                memory_delta=memory_delta,
                memory_signature=memory_signature,
                natal_positions=natal,
                transit_effect_phase_prev_by_category=phase_state,
            )
            if result.phase_by_category_after:
                phase_state = result.phase_by_category_after
            if start_params is None:
                start_params = result.params_final
                start_axis = result.axis_final
                first_dt = dt_utc
            end_params = result.params_final
            end_axis = result.axis_final
            last_dt = dt_utc
        current += timedelta(days=1)

    if start_axis is None or end_axis is None or start_params is None or end_params is None:
        return None

    delta_axis = tuple(e - s for s, e in zip(start_axis, end_axis))
    delta_params = tuple(e - s for s, e in zip(start_params, end_params))

    out: dict[str, Any] = {
        "delta_axis": delta_axis,
        "delta_params": delta_params,
        "mean_abs_axis": sum(abs(d) for d in delta_axis) / len(delta_axis),
        "max_abs_params": max(abs(d) for d in delta_params),
    }

    # 004: натальный зодиак и дома (element = элемент доминантного знака, Scorpio → Water)
    if natal:
        zod = ze.compute_zodiac_output(natal["positions"], natal["aspects"])
        out["natal_dominant_sign"] = zod["dominant_sign"]
        out["natal_dominant_sign_name"] = zod["dominant_sign_name"]
        out["natal_dominant_sign_element"] = zod.get("dominant_sign_element") or zod["dominant_element"]
        out["natal_zodiac_hash"] = _zodiac_summary_hash(zod["sign_energy_vector"])
        houses = natal.get("houses") or {}
        out["natal_ascendant"] = houses.get("ascendant")
        out["natal_mc"] = houses.get("mc")
    else:
        out["natal_dominant_sign"] = None
        out["natal_dominant_sign_name"] = ""
        out["natal_dominant_sign_element"] = ""
        out["natal_zodiac_hash"] = ""
        out["natal_ascendant"] = None
        out["natal_mc"] = None

    # 004: транзитный зодиак в первый и последний момент
    if use_astrology and first_dt is not None and last_dt is not None:
        tc_first = _transit_chart(first_dt, LONDON_LAT, LONDON_LON)
        tc_last = _transit_chart(last_dt, LONDON_LAT, LONDON_LON)
        if tc_first:
            z_first = ze.compute_zodiac_output(tc_first["positions"], tc_first["aspects"])
            out["transit_start_dominant_sign_name"] = z_first["dominant_sign_name"]
            out["transit_start_dominant_sign_element"] = z_first.get("dominant_sign_element") or z_first["dominant_element"]
        else:
            out["transit_start_dominant_sign_name"] = ""
            out["transit_start_dominant_sign_element"] = ""
        if tc_last:
            z_last = ze.compute_zodiac_output(tc_last["positions"], tc_last["aspects"])
            out["transit_end_dominant_sign_name"] = z_last["dominant_sign_name"]
            out["transit_end_dominant_sign_element"] = z_last.get("dominant_sign_element") or z_last["dominant_element"]
        else:
            out["transit_end_dominant_sign_name"] = ""
            out["transit_end_dominant_sign_element"] = ""
    else:
        out["transit_start_dominant_sign_name"] = ""
        out["transit_start_dominant_sign_element"] = ""
        out["transit_end_dominant_sign_name"] = ""
        out["transit_end_dominant_sign_element"] = ""

    return out


def run() -> None:
    parser = argparse.ArgumentParser(
        description="004: случайные жизни (даты от Р.Х. до сегодня), 70–108 лет, дельты + зодиак/дома"
    )
    parser.add_argument("--lives", type=int, default=200, metavar="N", help="Количество жизней")
    parser.add_argument("--seed", type=int, default=None, metavar="S", help="Seed для воспроизводимости")
    parser.add_argument("--no-astrology", action="store_true", help="Не использовать астрологию")
    parser.add_argument("--days", type=int, default=None, metavar="N", help="Макс. дней на жизнь (быстрый тест)")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    today = date.today()
    if DATE_FIRST >= today:
        print("Диапазон дат пуст.", file=sys.stderr)
        sys.exit(1)
    total_days = (today - DATE_FIRST).days + 1
    indices = random.sample(range(total_days), min(args.lives, total_days))
    birth_dates = [DATE_FIRST + timedelta(days=i) for i in indices]

    use_astrology = not args.no_astrology
    if use_astrology and _build_natal(birth_dates[0]) is None:
        print("Астрология недоступна (pip install -e \".[astrology]\"), транзиты отключены.", file=sys.stderr)
        use_astrology = False
    else:
        print("004: натал + транзиты (10 планет, дома, зодиак). Лондон.", file=sys.stderr)

    config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)

    # Заголовок: 002-колонки + 004 (натал зодиак, дома, транзит начало/конец)
    header_parts = [
        "birth_date", "lifespan_years",
        "natal_dom_sign", "natal_dom_element", "natal_zodiac_hash",
        "natal_asc", "natal_mc",
        "transit_start_dom", "transit_start_el",
        "transit_end_dom", "transit_end_el",
    ]
    header_parts += [f"d_{ax}" for ax in AXES]
    header_parts += ["mean_abs_axis", "max_abs_params"]
    print("\t".join(header_parts))

    for idx, birth_date in enumerate(birth_dates):
        lifespan_years = random.randint(LIFESPAN_MIN, LIFESPAN_MAX)
        result = _run_one_life(birth_date, lifespan_years, config, use_astrology, idx, args.days)
        if result is None:
            print(f"{birth_date.isoformat()}\t{lifespan_years}\tERROR", file=sys.stderr)
            continue
        asc = result.get("natal_ascendant")
        mc = result.get("natal_mc")
        row = [
            birth_date.isoformat(),
            str(lifespan_years),
            result.get("natal_dominant_sign_name") or "",
            result.get("natal_dominant_sign_element") or "",
            (result.get("natal_zodiac_hash") or "")[:16],
            f"{asc:.1f}" if asc is not None else "",
            f"{mc:.1f}" if mc is not None else "",
            result.get("transit_start_dominant_sign_name") or "",
            result.get("transit_start_dominant_sign_element") or "",
            result.get("transit_end_dominant_sign_name") or "",
            result.get("transit_end_dominant_sign_element") or "",
        ]
        row += [f"{d:+.6f}" for d in result["delta_axis"]]
        row.append(f"{result['mean_abs_axis']:.6f}")
        row.append(f"{result['max_abs_params']:.6f}")
        print("\t".join(row))
        sys.stdout.flush()


if __name__ == "__main__":
    run()
