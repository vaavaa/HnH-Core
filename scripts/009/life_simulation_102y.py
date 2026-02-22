#!/usr/bin/env python3
"""
009: Симуляция жизни с учётом пола и модуляции транзитного отклика (scale_delta).

На базе 008: тот же натал для male и female, но с sex_transit_mode="scale_delta"
транзитные дельты на каждом шаге масштабируются множителями M(E), поэтому
накопленные за жизнь delta_axis и delta_params различаются по полу — не только
натальная разница (008), но и траектория изменений под транзитами (009).

Как меняются дельты с 009:
- 008: male и female отличаются только наталом (base_vector); за жизнь к ним
  применяются одни и те же транзитные дельты → delta_axis за период совпадают.
- 009 (scale_delta): на каждом шаге bounded_delta умножается на M[i](E);
  у male E>0, у female E<0 → M(male) и M(female) симметричны относительно 1.
  Итог: delta_axis(male) ≠ delta_axis(female) при одном натале и одном периоде.

Запуск из корня проекта (venv активирован):
  python scripts/009/life_simulation_102y.py
  python scripts/009/life_simulation_102y.py --lives 50 --seed 42
  python scripts/009/life_simulation_102y.py --no-scale-delta   # как 008: дельты по полу совпадают
  python scripts/009/life_simulation_102y.py --lives 5 --days 365
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
from hnh.identity.schema import AXES, NUM_PARAMETERS
from hnh.lifecycle.engine import aggregate_axis
from hnh.sex.delta_32 import compute_sex_delta_32, DEFAULT_SEX_MAX_PARAM_DELTA

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


def _build_birth_data(birth_date: date) -> dict[str, Any] | None:
    try:
        from hnh.core.natal import build_natal_positions
    except Exception:
        return None
    birth_dt = datetime(
        birth_date.year, birth_date.month, birth_date.day,
        12, 0, 0, 0, tzinfo=timezone.utc,
    )
    try:
        build_natal_positions(birth_dt, LONDON_LAT, LONDON_LON)
        return {
            "datetime_utc": birth_dt,
            "lat": LONDON_LAT,
            "lon": LONDON_LON,
        }
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
    sex_transit_config: SexTransitConfig | None,
    use_astrology: bool,
    life_index: int,
    max_days: int | None = None,
    sex: str | None = None,
) -> dict[str, Any] | None:
    """
    Один проход жизни через Agent.step(). 009: при sex_transit_config с scale_delta
    транзитные дельты на каждом шаге масштабируются по полу → накопленные
    delta_axis/delta_params различаются у male и female.
    """
    end_date = _end_date_for_lifespan(birth_date, lifespan_years)
    if max_days is not None:
        capped = birth_date + timedelta(days=max_days)
        if capped < end_date:
            end_date = capped

    birth_data = _build_birth_data(birth_date) if use_astrology else None
    if use_astrology and birth_data is None:
        return None

    if birth_data is None:
        birth_data = {
            "positions": [
                {"planet": "Sun", "longitude": 0.0},
                {"planet": "Moon", "longitude": 30.0},
            ],
        }
    if sex is not None:
        birth_data = {**birth_data, "sex": sex}

    agent = Agent(
        birth_data,
        config=config,
        lifecycle=False,
        sex_transit_config=sex_transit_config,
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

    E = 0.0
    if getattr(agent, "_last_step_result", None) is not None:
        E = getattr(agent._last_step_result, "sex_polarity_E", 0.0)
    sex_delta_32 = compute_sex_delta_32(E)
    max_abs_sd32 = max(abs(x) for x in sex_delta_32)
    mean_abs_sd32 = sum(abs(x) for x in sex_delta_32) / NUM_PARAMETERS if NUM_PARAMETERS else 0.0

    out: dict[str, Any] = {
        "sex": getattr(agent._last_step_result, "sex", None) if getattr(agent, "_last_step_result", None) else birth_data.get("sex"),
        "delta_axis": delta_axis,
        "delta_params": delta_params,
        "mean_abs_axis": sum(abs(d) for d in delta_axis) / len(delta_axis),
        "max_abs_params": max(abs(d) for d in delta_params),
        "end_params": end_params,
        "end_axis": end_axis,
        "E": E,
        "sex_delta_32": sex_delta_32,
        "max_abs_sex_delta_32": max_abs_sd32,
        "mean_abs_sex_delta_32": mean_abs_sd32,
        "sex_transit_mode": sex_transit_config.sex_transit_mode if sex_transit_config else "off",
    }

    if use_astrology and birth_data is not None and "lat" in birth_data:
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
        description="009: жизни с полом и scale_delta — транзитные дельты по шагам масштабируются по полу, накопленные d_* различаются"
    )
    parser.add_argument("--lives", type=int, default=200, metavar="N", help="Количество жизней")
    parser.add_argument("--seed", type=int, default=None, metavar="S", help="Seed для воспроизводимости")
    parser.add_argument("--no-astrology", action="store_true", help="Не использовать астрологию (минимальный натал)")
    parser.add_argument("--no-scale-delta", action="store_true", help="Выключить 009 (как 008): sex_transit_mode=off, дельты по полу совпадают")
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
    if use_astrology and _build_birth_data(birth_dates[0]) is None:
        print("Астрология недоступна, используется минимальный натал.", file=sys.stderr)
        use_astrology = False

    if args.no_scale_delta:
        sex_transit_config = None  # off — как 008
        print("009: sex_transit_mode=off (как 008), дельты за жизнь у male/female совпадают.", file=sys.stderr)
    else:
        sex_transit_config = SexTransitConfig(sex_transit_mode="scale_delta")
        print("009: sex_transit_mode=scale_delta — транзитный отклик по шагам зависит от пола, d_* male ≠ d_* female.", file=sys.stderr)

    config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)

    header_parts = [
        "birth_date", "sex", "lifespan_years", "sex_transit_mode",
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
        results_by_sex: dict[str, dict[str, Any]] = {}
        for sex in ("male", "female"):
            result = _run_one_life(
                birth_date, lifespan_years, config, sex_transit_config,
                use_astrology, idx, args.days, sex=sex,
            )
            if result is None:
                print(f"{birth_date.isoformat()}\t{sex}\t{lifespan_years}\tERROR", file=sys.stderr)
                continue
            results_by_sex[sex] = result
            s = result.get("sex") or sex
            E_val = result.get("E", 0.0)
            mode = result.get("sex_transit_mode", "off")
            print(
                f"CHECK_B\t{birth_date.isoformat()}\tsex={s}\tE={E_val:+.4f}\tsex_transit_mode={mode}",
                file=sys.stderr,
            )
            row = [
                birth_date.isoformat(),
                result.get("sex") or sex,
                str(lifespan_years),
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

        # 009: при scale_delta delta_axis у male и female различаются; при off — совпадают (как 008)
        if "male" in results_by_sex and "female" in results_by_sex:
            rm = results_by_sex["male"]
            rf = results_by_sex["female"]
            pm = rm.get("end_params")
            pf = rf.get("end_params")
            ax_m = rm.get("end_axis")
            ax_f = rf.get("end_axis")
            dax_m = rm.get("delta_axis")
            dax_f = rf.get("delta_axis")
            if pm is not None and pf is not None and len(pm) == len(pf):
                diffs = [abs(a - b) for a, b in zip(pm, pf)]
                max_abs_params_diff = max(diffs)
                mean_abs_params_diff = sum(diffs) / len(diffs)
            else:
                max_abs_params_diff = mean_abs_params_diff = float("nan")
            if ax_m is not None and ax_f is not None and len(ax_m) == len(ax_f):
                axis_diff = tuple(a - b for a, b in zip(ax_m, ax_f))
                axis_diff_ok = all(abs(d) <= DEFAULT_SEX_MAX_PARAM_DELTA for d in axis_diff)
            else:
                axis_diff = ()
                axis_diff_ok = False
            # Разница накопленных дельт по осям (009: при scale_delta не нулевая)
            if dax_m is not None and dax_f is not None and len(dax_m) == len(dax_f):
                delta_axis_diff = tuple(a - b for a, b in zip(dax_m, dax_f))
                max_delta_axis_diff = max(abs(x) for x in delta_axis_diff)
                any_delta_axis_diff = any(abs(x) > 1e-9 for x in delta_axis_diff)
            else:
                delta_axis_diff = ()
                max_delta_axis_diff = float("nan")
                any_delta_axis_diff = False
            max_diff_bound = 2.0 * DEFAULT_SEX_MAX_PARAM_DELTA
            in_bounds = (0 < max_abs_params_diff <= max_diff_bound) if max_abs_params_diff == max_abs_params_diff else False
            print(
                f"CHECK_A\t{birth_date.isoformat()}\tmax_abs_params_diff={max_abs_params_diff:.6f}\t"
                f"max_delta_axis_diff={max_delta_axis_diff:.6f}\tany_delta_axis_diff={any_delta_axis_diff}\t"
                f"in_bounds={in_bounds}\taxis_diff_ok={axis_diff_ok}",
                file=sys.stderr,
            )
        sys.stdout.flush()


if __name__ == "__main__":
    run()
