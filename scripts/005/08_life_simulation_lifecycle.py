#!/usr/bin/env python3
"""
005: Симуляция жизни с lifecycle — F, W, A_g, state по дням; при смерти снапшот.

Опции: --days (макс дней на жизнь), --lives (число жизней), --seed, --no-lifecycle (сравнение с 002).
Запуск из корня:
  python scripts/005/08_life_simulation_lifecycle.py
  python scripts/005/08_life_simulation_lifecycle.py --lives 5 --days 500 --seed 42
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, datetime, timedelta, timezone

from hnh.config.replay_config import ReplayConfig
from hnh.identity import IdentityCore
from hnh.identity.schema import NUM_PARAMETERS, _registry
from hnh.state.replay_v2 import run_step_v2
from hnh.lifecycle.run import is_lifecycle_active, run_step_with_lifecycle
from hnh.lifecycle.engine import LifecycleStepState, LifecycleState

LONDON_LAT = 51.5074
LONDON_LON = -0.1278
DATE_FIRST = date(2000, 1, 1)
TIME_SLOTS = [(6, 0), (18, 0)]
LIFESPAN_MIN_Y = 50
LIFESPAN_MAX_Y = 120


def _build_natal(birth_date: date) -> dict | None:
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


def _end_date(birth: date, years: int) -> date:
    try:
        return date(birth.year + years, birth.month, birth.day)
    except ValueError:
        return date(birth.year + years, 2, 28)


def _run_one_life(
    birth_date: date,
    lifespan_years: int,
    config: ReplayConfig,
    use_astrology: bool,
    use_lifecycle: bool,
    life_index: int,
    max_days: int | None,
) -> dict | None:
    end_date = _end_date(birth_date, lifespan_years)
    if max_days is not None:
        capped = birth_date + timedelta(days=max_days)
        if capped < end_date:
            end_date = capped
    natal = _build_natal(birth_date) if use_astrology else None
    identity_id = f"life-005-{life_index}-{birth_date.isoformat()}"
    _registry.discard(identity_id)
    identity = IdentityCore(
        identity_id=identity_id,
        base_vector=(0.5,) * NUM_PARAMETERS,
        sensitivity_vector=(0.5,) * NUM_PARAMETERS,
    )
    memory_delta = (0.0,) * NUM_PARAMETERS
    memory_signature = ""
    phase_state = {
        "personal": (0.0,) * NUM_PARAMETERS,
        "social": (0.0,) * NUM_PARAMETERS,
        "outer": (0.0,) * NUM_PARAMETERS,
    }
    lifecycle_state = None
    if use_lifecycle and is_lifecycle_active(config):
        lifecycle_state = LifecycleStepState(
            F=getattr(config, "initial_f", 0.0),
            W=getattr(config, "initial_w", 0.0),
            state=LifecycleState.ALIVE,
            sum_v=0.0, sum_burn=0.0, count_days=0,
        )
    current = birth_date
    days_lived = 0
    last_f = 0.0
    last_w = 0.0
    last_state_str = "ALIVE"
    snapshot_at_death = None

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

            if use_lifecycle and lifecycle_state is not None and lifecycle_state.state == LifecycleState.ALIVE:
                aspects = []
                if natal:
                    try:
                        from hnh.astrology.transits import compute_transit_signature
                        sig = compute_transit_signature(dt_utc, natal)
                        aspects = sig.get("aspects_to_natal", [])
                    except Exception:
                        pass
                chrono_days = (current - birth_date).days
                next_lc, _, _, snap = run_step_with_lifecycle(
                    identity, config,
                    result.daily_transit_effect,
                    memory_delta,
                    aspects,
                    float(chrono_days),
                    lifecycle_state,
                )
                lifecycle_state = next_lc
                last_f = lifecycle_state.F
                last_w = lifecycle_state.W
                last_state_str = lifecycle_state.state.value
                if snap is not None:
                    snapshot_at_death = snap
                    return {
                        "birth_date": birth_date,
                        "lifespan_years": lifespan_years,
                        "days_lived": chrono_days,
                        "state": last_state_str,
                        "F": last_f,
                        "W": last_w,
                        "snapshot": snapshot_at_death,
                    }
        current += timedelta(days=1)
        days_lived = (current - birth_date).days

    if use_lifecycle and lifecycle_state is not None:
        return {
            "birth_date": birth_date,
            "lifespan_years": lifespan_years,
            "days_lived": days_lived,
            "state": last_state_str,
            "F": last_f,
            "W": last_w,
            "snapshot": None,
        }
    return {"birth_date": birth_date, "lifespan_years": lifespan_years, "days_lived": days_lived}


def main() -> None:
    parser = argparse.ArgumentParser(description="005: Life simulation with lifecycle")
    parser.add_argument("--lives", type=int, default=10, help="Number of lives")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--days", type=int, default=None, help="Max days per life (quick test)")
    parser.add_argument("--no-lifecycle", action="store_true", help="Disable lifecycle (002-only replay)")
    parser.add_argument("--no-astrology", action="store_true", help="No natal/transits")
    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    today = date.today()
    if DATE_FIRST >= today:
        print("DATE_FIRST >= today", file=sys.stderr)
        sys.exit(1)
    total_days = (today - DATE_FIRST).days + 1
    indices = random.sample(range(total_days), min(args.lives, total_days))
    birth_dates = [DATE_FIRST + timedelta(days=i) for i in indices]
    use_astrology = not args.no_astrology
    if use_astrology and _build_natal(birth_dates[0]) is None:
        use_astrology = False
    use_lifecycle = not args.no_lifecycle
    config = ReplayConfig(
        global_max_delta=0.15,
        shock_threshold=0.8,
        shock_multiplier=1.5,
        mode="research" if use_lifecycle else "product",
        lifecycle_enabled=use_lifecycle,
        initial_f=0.0,
        initial_w=0.0,
    )
    print(f"lifecycle={use_lifecycle} astrology={use_astrology} lives={len(birth_dates)}", file=sys.stderr)
    for idx, birth_date in enumerate(birth_dates):
        lifespan_years = random.randint(LIFESPAN_MIN_Y, LIFESPAN_MAX_Y)
        out = _run_one_life(
            birth_date, lifespan_years, config, use_astrology, use_lifecycle, idx, args.days
        )
        if out is None:
            continue
        if use_lifecycle and out.get("snapshot"):
            snap = out["snapshot"]
            print(f"{birth_date.isoformat()}\t{out['days_lived']}\t{out['state']}\tF={out['F']:.2f}\tW={out['W']:.3f}\tAge_psy={getattr(snap, 'Age_psy', None)}")
        else:
            print(f"{birth_date.isoformat()}\t{out['days_lived']}\t{out.get('state', '—')}\tF={out.get('F', 0):.2f}\tW={out.get('W', 0):.3f}")


if __name__ == "__main__":
    main()
