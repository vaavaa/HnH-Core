#!/usr/bin/env python3
"""
Demo 005 — формулы Lifecycle без зависимости от hnh.lifecycle.

Показывает за N дней: S_T (фиктивный), load, recovery, F(t+1), L, q, A_g, Age_psy.
Константы по умолчанию из spec 005. Запуск из корня: python scripts/005/01_lifecycle_formulas_demo.py
"""
from __future__ import annotations

import argparse


# Defaults from spec 005
C_T = 3.0
THETA_SHOCK = 0.90
ALPHA_SHOCK = 0.6
BETA_S = 0.6
BETA_R = 0.7
GAMMA_0 = 0.12
GAMMA_R = 0.30
GAMMA_C = 0.20
LAMBDA_UP = 0.010
LAMBDA_DOWN = 0.009
L0 = 14.0
DELTA_R = 0.8
DELTA_S = 0.5
RHO = 2.5
ETA_0 = 0.80
ETA_1 = 0.45
KAPPA = 2.0


def clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def stress_normalized(raw_intensity: float, c_t: float = C_T) -> float:
    return clip(raw_intensity / c_t, 0.0, 1.0)


def shock_multiplier(s_t: float) -> float:
    return (1.0 + ALPHA_SHOCK) if s_t >= THETA_SHOCK else 1.0


def load(s_t: float, r: float, s_g: float) -> float:
    mult = shock_multiplier(s_t)
    return mult * s_t * (1.0 + BETA_S * s_g) * (1.0 - BETA_R * r)


def recovery(s_t: float, r: float) -> float:
    return GAMMA_0 + GAMMA_R * r + GAMMA_C * (1.0 - s_t)


def fatigue_limit(r: float, s_g: float) -> float:
    return L0 * (1.0 + DELTA_R * r) * (1.0 - DELTA_S * s_g)


def activity_factor(q: float) -> float:
    return clip(1.0 - q**RHO, 0.0, 1.0)


def age_psy(chrono_days: float, q: float) -> float:
    return chrono_days * (ETA_0 + ETA_1 * (q**KAPPA))


def run_demo(days: int, stress_level: float, r: float = 0.5, s_g: float = 0.5) -> None:
    s_t = stress_normalized(stress_level)
    l = fatigue_limit(r, s_g)
    f = 0.0
    print(f"Inputs: S_T={s_t:.4f}, R={r:.2f}, S_g={s_g:.2f}, L={l:.2f}")
    print(f"{'day':>4} {'F':>8} {'q':>6} {'A_g':>6} {'load':>7} {'rec':>7} {'Age_psy':>8}")
    print("-" * 52)

    for day in range(days):
        ld = load(s_t, r, s_g)
        rec = recovery(s_t, r)
        f = max(0.0, f + LAMBDA_UP * ld - LAMBDA_DOWN * rec)
        q = clip(f / l, 0.0, 1.0)
        a_g = activity_factor(q)
        a_psy = age_psy(float(day), q)
        print(f"{day:4d} {f:8.4f} {q:6.3f} {a_g:6.3f} {ld:7.4f} {rec:7.4f} {a_psy:8.2f}")


def main() -> None:
    ap = argparse.ArgumentParser(description="005 Lifecycle formulas demo")
    ap.add_argument("--days", type=int, default=30, help="Number of days to simulate")
    ap.add_argument("--stress", type=float, default=1.5, help="Fake raw I_T for S_T = I_T/C_T (default 1.5 -> S_T=0.5)")
    ap.add_argument("--use-module", action="store_true", help="Use hnh.lifecycle module if available")
    args = ap.parse_args()
    if args.use_module:
        try:
            from hnh.lifecycle.fatigue import (
                load as lc_load,
                recovery as lc_recovery,
                update_fatigue,
                fatigue_limit,
                normalized_fatigue,
            )
            from hnh.lifecycle.engine import activity_factor as lc_activity_factor, age_psy_years
            from hnh.lifecycle.constants import DEFAULT_LIFECYCLE_CONSTANTS

            def run_with_module() -> None:
                c = DEFAULT_LIFECYCLE_CONSTANTS
                s_t = stress_normalized(args.stress)
                r, s_g = 0.5, 0.5
                L = fatigue_limit(r, s_g, c)
                f = 0.0
                print(f"[hnh.lifecycle] S_T={s_t:.4f}, R={r}, S_g={s_g}, L={L:.2f}")
                print(f"{'day':>4} {'F':>8} {'q':>6} {'A_g':>6} {'Age_psy_y':>8}")
                print("-" * 40)
                for day in range(args.days):
                    ld = lc_load(s_t, r, s_g, c)
                    rec = lc_recovery(s_t, r, c)
                    f = update_fatigue(f, ld, rec, c)
                    q = normalized_fatigue(f, L)
                    a_g = lc_activity_factor(q, c)
                    age_y = age_psy_years(float(day), q, c)
                    print(f"{day:4d} {f:8.4f} {q:6.3f} {a_g:6.3f} {age_y:8.2f}")

            run_with_module()
            return
        except ImportError:
            print("hnh.lifecycle not available, using built-in formulas")
    run_demo(args.days, args.stress)


if __name__ == "__main__":
    main()
