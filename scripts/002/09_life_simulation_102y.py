#!/usr/bin/env python3
"""
002: Симуляция многих жизней — случайные даты рождения (от Рождества до сегодня), Лондон.

Берём N случайных дат в диапазоне 0001-12-25 .. сегодня. Для каждой даты — жизнь
со случайной длительностью 70–108 лет; каждый день два расчёта (утро/вечер UTC),
натал и транзиты для Лондона. Выводим только дельты (конец − начало) по осям на каждую жизнь.

Запуск из корня проекта (venv активирован):
  python scripts/002/09_life_simulation_102y.py
  python scripts/002/09_life_simulation_102y.py --lives 50 --seed 42
  python scripts/002/09_life_simulation_102y.py --lives 5 --days 365   # быстрый тест (5 жизней по 1 году)
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, datetime, timedelta, timezone

from hnh.config.replay_config import ReplayConfig
from hnh.identity import IdentityCore
from hnh.identity.schema import AXES, NUM_PARAMETERS, _registry
from hnh.state.replay_v2 import run_step_v2

# Лондон: широта, долгота (все родились в Лондоне)
LONDON_LAT = 51.5074
LONDON_LON = -0.1278
# Диапазон дат: от Рождества Христова до сегодня
DATE_FIRST = date(1, 12, 25)
# Два момента в сутки: утро и вечер UTC
TIME_SLOTS = [(6, 0), (18, 0)]

# Пределы длительности жизни (годы)
LIFESPAN_MIN = 70
LIFESPAN_MAX = 108


def _build_natal(birth_date: date) -> dict | None:
    """Натальная карта на дату рождения, Лондон. None если астрология недоступна."""
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
    """Дата конца жизни: birth + years календарных лет (учёт високосов)."""
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
) -> tuple[tuple[float, ...], tuple[float, ...]] | None:
    """
    Один проход жизни: от birth_date до birth_date + lifespan_years дней.
    Если max_days задан — ограничить число дней (для быстрого теста).
    Возвращает (delta_axis_8, delta_params_32) или None при ошибке.
    """
    end_date = _end_date_for_lifespan(birth_date, lifespan_years)
    if max_days is not None:
        capped = birth_date + timedelta(days=max_days)
        if capped < end_date:
            end_date = capped
    natal = _build_natal(birth_date) if use_astrology else None
    identity_id = f"life-{life_index}-{birth_date.isoformat()}"
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

    # Exponential accumulation: phase[t] = phase[t-1]*decay + daily[t] per category (погода/сезон/эпоха)
    phase_state: dict[str, tuple[float, ...]] = {
        "personal": (0.0,) * NUM_PARAMETERS,
        "social": (0.0,) * NUM_PARAMETERS,
        "outer": (0.0,) * NUM_PARAMETERS,
    }
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
            end_params = result.params_final
            end_axis = result.axis_final
        current += timedelta(days=1)

    if start_axis is None or end_axis is None or start_params is None or end_params is None:
        return None
    delta_axis = tuple(e - s for s, e in zip(start_axis, end_axis))
    delta_params = tuple(e - s for s, e in zip(start_params, end_params))
    return (delta_axis, delta_params)


def run() -> None:
    parser = argparse.ArgumentParser(
        description="200 случайных жизней (даты от Р.Х. до сегодня), 70–108 лет, вывод дельт"
    )
    parser.add_argument(
        "--lives",
        type=int,
        default=200,
        metavar="N",
        help="Количество жизней (по умолчанию 200)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        metavar="S",
        help="Seed для воспроизводимости случайных дат",
    )
    parser.add_argument(
        "--no-astrology",
        action="store_true",
        help="Не использовать астрологию (транзиты не учитываются)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        metavar="N",
        help="Макс. дней на жизнь (для быстрого теста; по умолчанию вся жизнь)",
    )
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    today = date.today()
    if DATE_FIRST >= today:
        print("Диапазон дат пуст (сегодня до 0001-12-25).", file=sys.stderr)
        sys.exit(1)
    total_days = (today - DATE_FIRST).days + 1
    # Список из N случайных дат в [DATE_FIRST, today]
    indices = random.sample(range(total_days), min(args.lives, total_days))
    birth_dates = [DATE_FIRST + timedelta(days=i) for i in indices]

    use_astrology = not args.no_astrology
    if use_astrology and _build_natal(birth_dates[0]) is None:
        print("Астрология недоступна (pip install -e \".[astrology]\"), транзиты отключены.", file=sys.stderr)
        use_astrology = False
    else:
        print("Астрология: натал Лондон, транзиты учитываются.", file=sys.stderr)

    config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)

    # Заголовок: дата_рождения  лет  delta_axis_1 ... delta_axis_8  mean_abs_axis  max_abs_params
    header = "birth_date\tlifespan_years\t" + "\t".join(f"d_{ax}" for ax in AXES) + "\tmean_abs_axis\tmax_abs_params"
    print(header)

    for idx, birth_date in enumerate(birth_dates):
        lifespan_years = random.randint(LIFESPAN_MIN, LIFESPAN_MAX)
        result = _run_one_life(birth_date, lifespan_years, config, use_astrology, idx, args.days)
        if result is None:
            print(f"{birth_date.isoformat()}\t{lifespan_years}\tERROR", file=sys.stderr)
            continue
        delta_axis, delta_params = result
        mean_abs_axis = sum(abs(d) for d in delta_axis) / len(delta_axis)
        max_abs_params = max(abs(d) for d in delta_params)
        row = (
            birth_date.isoformat(),
            str(lifespan_years),
            *[f"{d:+.6f}" for d in delta_axis],
            f"{mean_abs_axis:.6f}",
            f"{max_abs_params:.6f}",
        )
        print("\t".join(row))
        sys.stdout.flush()


if __name__ == "__main__":
    run()
