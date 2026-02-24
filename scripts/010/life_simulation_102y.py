#!/usr/bin/env python3
"""
010: Симуляция жизни с учётом возраста (астрологические стадии → age_delta_32).

На базе 009: тот же натал и пол, но при age_mode="on" на каждом шаге в сборку 32D
добавляется age_delta_32 (признаки стадий × W_age, с daily Lipschitz). Накопленные
за жизнь delta_axis и delta_params различаются при включённом и выключенном возрасте.

Как меняются дельты с 010:
- 009 без возраста: траектория params/axis определяется только транзитами и полом.
- 010 (age_mode=on): к сборке добавляется age_delta_32; с ростом возраста меняются
  maturity, saturn_event, jupiter_return, nodal_return, uranus_opposition → итоговые
  end_params и delta_axis за жизнь отличаются от прогона без возраста.

Требование: при age_mode=on в birth_data должен быть datetime_utc (добавляется
автоматически из даты рождения).

Запуск из корня проекта (venv активирован):
  python scripts/010/life_simulation_102y.py
  python scripts/010/life_simulation_102y.py --lives 50 --seed 42
  python scripts/010/life_simulation_102y.py --no-age   # без 010: как 009 по сборке
  python scripts/010/life_simulation_102y.py --lives 5 --days 365
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import orjson
import xxhash

# Repo root for imports when run as script
if __name__ == "__main__" and "__file__" in dir():
    _root = Path(__file__).resolve().parent.parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from hnh.agent import Agent
from hnh.astrology import aspects as asp
from hnh.astrology import ephemeris as eph
from hnh.astrology import houses as hou
from hnh.astrology.zodiac_expression import ZodiacExpression
from hnh.config.replay_config import ReplayConfig
from hnh.config.sex_transit_config import SexTransitConfig
from hnh.config.age_config import AgeConfig
from hnh.identity.schema import AXES, NUM_PARAMETERS
from hnh.lifecycle.engine import aggregate_axis
from hnh.age.constants import TROPICAL_YEAR_DAYS

# Лондон
LONDON_LAT = 51.5074
LONDON_LON = -0.1278
DATE_FIRST = date(1, 12, 25)
TIME_SLOTS = [(6, 0), (18, 0)]
LIFESPAN_MIN = 70
LIFESPAN_MAX = 108


def _zodiac_summary_hash(sign_energy_vector: tuple[tuple[float, float, float, float], ...]) -> str:
    blob = orjson.dumps(sign_energy_vector, option=orjson.OPT_SORT_KEYS)
    return xxhash.xxh3_128(blob, seed=0).hexdigest()


def _transit_chart(dt_utc: datetime, lat: float, lon: float) -> dict[str, Any] | None:
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


def _build_birth_data(birth_date: date, with_datetime_utc: bool = True) -> dict[str, Any] | None:
    """Строит birth_data. При with_datetime_utc добавляет datetime_utc (нужно для 010 age_mode=on)."""
    birth_dt = datetime(
        birth_date.year, birth_date.month, birth_date.day,
        12, 0, 0, 0, tzinfo=timezone.utc,
    )
    try:
        from hnh.core.natal import build_natal_positions
        build_natal_positions(birth_dt, LONDON_LAT, LONDON_LON)
        data = {
            "datetime_utc": birth_dt,
            "lat": LONDON_LAT,
            "lon": LONDON_LON,
        }
    except Exception:
        data = None
    if data is None:
        data = {
            "positions": [
                {"planet": "Sun", "longitude": 0.0},
                {"planet": "Moon", "longitude": 30.0},
            ],
        }
    if with_datetime_utc and "datetime_utc" not in data:
        data = {**data, "datetime_utc": birth_dt}
    return data


def _end_date_for_lifespan(birth: date, years: int) -> date:
    try:
        end = date(birth.year + years, birth.month, birth.day)
    except ValueError:
        end = date(birth.year + years, 2, 28)
    return end


def _age_years_from_dates(birth_dt: datetime, end_dt: datetime, age_max_years: float = 120.0) -> float:
    delta_days = (end_dt - birth_dt).total_seconds() / 86400.0
    age = delta_days / TROPICAL_YEAR_DAYS
    return min(max(0.0, age), age_max_years)


def _run_one_life(
    birth_date: date,
    lifespan_years: int,
    config: ReplayConfig,
    sex_transit_config: SexTransitConfig | None,
    age_config: AgeConfig | None,
    use_astrology: bool,
    life_index: int,
    max_days: int | None = None,
    sex: str | None = None,
) -> dict[str, Any] | None:
    """
    Один проход жизни через Agent.step(). 010: при age_config (age_mode=on)
    на каждом шаге в сборку добавляется age_delta_32 → накопленные delta_axis/delta_params
    отличаются от прогона без возраста.
    """
    end_date = _end_date_for_lifespan(birth_date, lifespan_years)
    if max_days is not None:
        capped = birth_date + timedelta(days=max_days)
        if capped < end_date:
            end_date = capped

    birth_data = _build_birth_data(birth_date, with_datetime_utc=(age_config is not None and getattr(age_config, "age_mode", "off") == "on"))
    if use_astrology:
        full_birth = _build_birth_data(birth_date, with_datetime_utc=True)
        if full_birth is not None and "lat" in full_birth:
            birth_data = full_birth
        elif birth_data is None:
            return None
    if birth_data is None:
        birth_data = _build_birth_data(birth_date, with_datetime_utc=(age_config is not None))
    if sex is not None:
        birth_data = {**birth_data, "sex": sex}

    agent = Agent(
        birth_data,
        config=config,
        lifecycle=False,
        sex_transit_config=sex_transit_config,
        age_config=age_config,
    )
    start_params: tuple[float, ...] | None = None
    start_axis: tuple[float, ...] | None = None
    end_params: tuple[float, ...] | None = None
    end_axis: tuple[float, ...] | None = None
    first_dt: datetime | None = None
    last_dt: datetime | None = None
    current = birth_date

    while current <= end_date:
        for hour, minute in TIME_SLOTS:
            dt_utc = datetime(
                current.year, current.month, current.day,
                hour, minute, 0, 0, tzinfo=timezone.utc,
            )
            agent.step(dt_utc)
            params = agent.behavior.current_vector
            axis = aggregate_axis(params)
            if start_params is None:
                start_params = params
                start_axis = axis
                first_dt = dt_utc
            end_params = params
            end_axis = axis
            last_dt = dt_utc
        current += timedelta(days=1)

    if start_axis is None or end_axis is None or start_params is None or end_params is None:
        return None

    delta_axis = tuple(e - s for s, e in zip(start_axis, end_axis))
    delta_params = tuple(e - s for s, e in zip(start_params, end_params))

    birth_dt = datetime(birth_date.year, birth_date.month, birth_date.day, 12, 0, 0, 0, tzinfo=timezone.utc)
    end_age_years = _age_years_from_dates(birth_dt, last_dt) if last_dt else 0.0

    age_mode = getattr(age_config, "age_mode", "off") if age_config else "off"

    out: dict[str, Any] = {
        "sex": getattr(agent._last_step_result, "sex", None) if getattr(agent, "_last_step_result", None) else birth_data.get("sex"),
        "delta_axis": delta_axis,
        "delta_params": delta_params,
        "mean_abs_axis": sum(abs(d) for d in delta_axis) / len(delta_axis),
        "max_abs_params": max(abs(d) for d in delta_params),
        "end_params": end_params,
        "end_axis": end_axis,
        "age_mode": age_mode,
        "end_age_years": end_age_years,
        "sex_transit_mode": sex_transit_config.sex_transit_mode if sex_transit_config else "off",
    }

    if use_astrology and birth_data is not None and birth_data.get("lat") is not None:
        zod = agent.zodiac_expression()
        out["natal_dominant_sign"] = zod.dominant_sign
        out["natal_dominant_sign_name"] = zod.dominant_sign_name()
        out["natal_dominant_sign_element"] = zod.dominant_sign_element()
        out["natal_zodiac_hash"] = _zodiac_summary_hash(zod.sign_vectors)
        natal_data = agent.natal.to_natal_data()
        houses = natal_data.get("houses") or {}
        out["natal_ascendant"] = houses.get("ascendant")
        out["natal_mc"] = houses.get("mc")
    else:
        out["natal_dominant_sign"] = None
        out["natal_dominant_sign_name"] = ""
        out["natal_dominant_sign_element"] = ""
        out["natal_zodiac_hash"] = ""
        out["natal_ascendant"] = None
        out["natal_mc"] = None

    if use_astrology and first_dt is not None and last_dt is not None:
        tc_first = _transit_chart(first_dt, LONDON_LAT, LONDON_LON)
        tc_last = _transit_chart(last_dt, LONDON_LAT, LONDON_LON)
        if tc_first:
            z_first = ZodiacExpression(tc_first)
            out["transit_start_dominant_sign_name"] = z_first.dominant_sign_name()
            out["transit_start_dominant_sign_element"] = z_first.dominant_sign_element()
        else:
            out["transit_start_dominant_sign_name"] = ""
            out["transit_start_dominant_sign_element"] = ""
        if tc_last:
            z_last = ZodiacExpression(tc_last)
            out["transit_end_dominant_sign_name"] = z_last.dominant_sign_name()
            out["transit_end_dominant_sign_element"] = z_last.dominant_sign_element()
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
        description="010: жизни с возрастом (age_delta_32) — накопленные delta_axis/delta_params отличаются при age_mode=on"
    )
    parser.add_argument("--lives", type=int, default=200, metavar="N", help="Количество жизней")
    parser.add_argument("--seed", type=int, default=None, metavar="S", help="Seed для воспроизводимости")
    parser.add_argument("--no-astrology", action="store_true", help="Не использовать астрологию (минимальный натал)")
    parser.add_argument("--no-age", action="store_true", help="Только без возраста: одна строка на жизнь (иначе две: off и on)")
    parser.add_argument("--no-scale-delta", action="store_true", help="Выключить 009 (sex_transit_mode=off)")
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
    if use_astrology and _build_birth_data(birth_dates[0], True) is None:
        print("Астрология недоступна, используется минимальный натал.", file=sys.stderr)
        use_astrology = False

    if args.no_scale_delta:
        sex_transit_config = None
        print("009: sex_transit_mode=off.", file=sys.stderr)
    else:
        sex_transit_config = SexTransitConfig(sex_transit_mode="scale_delta")
        print("009: sex_transit_mode=scale_delta.", file=sys.stderr)

    run_both_age_modes = not args.no_age
    if run_both_age_modes:
        print("010: для каждой жизни две строки — age_mode=off и age_mode=on (одинаковые параметры).", file=sys.stderr)
    else:
        print("010: age_mode=off, одна строка на жизнь.", file=sys.stderr)

    config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)

    header_parts = [
        "birth_date", "sex", "lifespan_years", "age_mode", "end_age_years",
        "sex_transit_mode",
        "natal_dom_sign", "natal_dom_element", "natal_zodiac_hash",
        "natal_asc", "natal_mc",
        "transit_start_dom", "transit_start_el",
        "transit_end_dom", "transit_end_el",
    ]
    header_parts += [f"d_{ax}" for ax in AXES]
    header_parts += ["mean_abs_axis", "max_abs_params"]
    print("\t".join(header_parts))

    def _print_row(result: dict[str, Any]) -> None:
        row = [
            result.get("birth_date", ""),
            result.get("sex") or "male",
            str(result.get("lifespan_years", "")),
            result.get("age_mode", "off"),
            f"{result.get('end_age_years', 0):.2f}",
            result.get("sex_transit_mode", "off"),
            result.get("natal_dominant_sign_name") or "",
            result.get("natal_dominant_sign_element") or "",
            (result.get("natal_zodiac_hash") or "")[:16],
            f"{asc:.1f}" if (asc := result.get("natal_ascendant")) is not None else "",
            f"{mc:.1f}" if (mc := result.get("natal_mc")) is not None else "",
            result.get("transit_start_dominant_sign_name") or "",
            result.get("transit_start_dominant_sign_element") or "",
            result.get("transit_end_dominant_sign_name") or "",
            result.get("transit_end_dominant_sign_element") or "",
        ]
        row += [f"{d:+.6f}" for d in result["delta_axis"]]
        row.append(f"{result['mean_abs_axis']:.6f}")
        row.append(f"{result['max_abs_params']:.6f}")
        print("\t".join(row))

    for idx, birth_date in enumerate(birth_dates):
        lifespan_years = random.randint(LIFESPAN_MIN, LIFESPAN_MAX)
        birth_date_str = birth_date.isoformat()
        sex_label = "male"

        if run_both_age_modes:
            # Сначала без возраста, затем с возрастом — одни и те же birth_date, lifespan, sex, натал
            result_off = _run_one_life(
                birth_date, lifespan_years, config, sex_transit_config, None,
                use_astrology, idx, args.days, sex=sex_label,
            )
            result_on = _run_one_life(
                birth_date, lifespan_years, config, sex_transit_config, AgeConfig(age_mode="on"),
                use_astrology, idx, args.days, sex=sex_label,
            )
            if result_off is None:
                print(f"{birth_date_str}\t{sex_label}\t{lifespan_years}\tERROR (off)", file=sys.stderr)
                continue
            if result_on is None:
                print(f"{birth_date_str}\t{sex_label}\t{lifespan_years}\tERROR (on)", file=sys.stderr)
                continue
            for r in (result_off, result_on):
                r["birth_date"] = birth_date_str
                r["lifespan_years"] = lifespan_years
            print(
                f"CHECK\t{birth_date_str}\t{sex_label}\t{lifespan_years}\toff end_age={result_off['end_age_years']:.1f}\ton end_age={result_on['end_age_years']:.1f}",
                file=sys.stderr,
            )
            _print_row(result_off)
            _print_row(result_on)
        else:
            result = _run_one_life(
                birth_date, lifespan_years, config, sex_transit_config, None,
                use_astrology, idx, args.days, sex=sex_label,
            )
            if result is None:
                print(f"{birth_date_str}\t{sex_label}\t{lifespan_years}\tERROR", file=sys.stderr)
                continue
            result["birth_date"] = birth_date_str
            result["lifespan_years"] = lifespan_years
            _print_row(result)

        sys.stdout.flush()


if __name__ == "__main__":
    run()
