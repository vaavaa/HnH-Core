"""
CLI: subcommands for simulating agent state; run (001, 7 params), run-v2 (002, 32 params).
Time is always injected from CLI args — no datetime.now() in core.
"""

from __future__ import annotations

import argparse
import sys

import orjson
from datetime import datetime, timezone

from hnh.core.identity import IdentityCore as CoreIdentity001
from hnh.core.parameters import BehavioralVector
from hnh.state.replay import run_step


def _default_identity_001() -> CoreIdentity001:
    """Default identity for CLI run (001: fixed 7-param base vector)."""
    base = BehavioralVector(
        warmth=0.5,
        strictness=0.4,
        verbosity=0.6,
        correction_rate=0.3,
        humor_level=0.5,
        challenge_intensity=0.4,
        pacing=0.5,
    )
    return CoreIdentity001(
        identity_id="cli-default",
        base_traits=base,
        symbolic_input=None,
    )


def _parse_date(s: str) -> datetime:
    """Parse YYYY-MM-DD to UTC noon."""
    dt = datetime.strptime(s, "%Y-%m-%d")
    return dt.replace(tzinfo=timezone.utc, hour=12, minute=0, second=0, microsecond=0)


def _cmd_run(args: argparse.Namespace) -> None:
    """Execute run: one step 001 (7 parameters)."""
    try:
        injected = _parse_date(args.date)
    except ValueError as e:
        print(f"Invalid --date: {e}. Use YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)
        return  # unreachable when exit runs; needed when exit is mocked

    identity = _default_identity_001()
    state = run_step(identity, injected, seed=args.seed, relational_snapshot=None)

    if args.replay:
        state2 = run_step(identity, injected, seed=args.seed, relational_snapshot=None)
        if state.final_behavior_vector.to_dict() != state2.final_behavior_vector.to_dict():
            print("Replay mismatch: outputs differ.", file=sys.stderr)
            sys.exit(1)
        if not args.json:
            print("Replay OK: identical output.")

    if args.json:
        out = {
            "identity_hash": state.identity_hash,
            "injected_time": state.injected_time,
            "final_behavioral_vector": state.final_behavior_vector.to_dict(),
            "active_modifiers": state.active_modifiers,
        }
        print(orjson.dumps(out, option=orjson.OPT_SORT_KEYS).decode("utf-8"))
    else:
        print("final_behavioral_vector:", state.final_behavior_vector.to_dict())
        print("active_modifiers:", state.active_modifiers)


def _default_natal_positions_for_transits() -> dict | None:
    """Default natal chart for CLI run-v2 so transits vary by --date. None if astrology unavailable."""
    try:
        from hnh.core.natal import build_natal_positions
        birth = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        return build_natal_positions(birth, 0.0, 0.0)
    except Exception:
        return None


def _cmd_run_v2(args: argparse.Namespace) -> None:
    """Execute run-v2: one step 002 (32 parameters, 8 axes)."""
    try:
        injected = _parse_date(args.date)
    except ValueError as e:
        print(f"Invalid --date: {e}. Use YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)
        return  # unreachable when exit runs; needed when exit is mocked

    from hnh.config.replay_config import ReplayConfig
    from hnh.identity import IdentityCore
    from hnh.identity.schema import NUM_PARAMETERS, _registry
    from hnh.state.replay_v2 import run_step_v2

    natal_positions = _default_natal_positions_for_transits()

    _registry.discard("cli-default-v2")
    identity = IdentityCore(
        identity_id="cli-default-v2",
        base_vector=(0.5,) * NUM_PARAMETERS,
        sensitivity_vector=(0.5,) * NUM_PARAMETERS,
    )
    config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.5)
    result = run_step_v2(identity, config, injected, natal_positions=natal_positions)

    if args.replay:
        _registry.discard("cli-default-v2-replay")
        identity2 = IdentityCore(
            identity_id="cli-default-v2-replay",
            base_vector=(0.5,) * NUM_PARAMETERS,
            sensitivity_vector=(0.5,) * NUM_PARAMETERS,
        )
        result2 = run_step_v2(identity2, config, injected, natal_positions=natal_positions)
        if result.params_final != result2.params_final or result.axis_final != result2.axis_final:
            print("Replay mismatch: outputs differ.", file=sys.stderr)
            sys.exit(1)
        if not args.json:
            print("Replay OK: identical output.")

    if args.json:
        out = {
            "identity_hash": result.identity_hash,
            "configuration_hash": result.configuration_hash,
            "injected_time_utc": result.injected_time_utc,
            "params_final": list(result.params_final),
            "axis_final": list(result.axis_final),
            "transit_signature": result.transit_signature,
            "shock_flag": result.shock_flag,
            "memory_signature": result.memory_signature,
        }
        if args.legacy:
            # 001-style 7 keys: warmth, strictness, verbosity, correction_rate, humor_level, challenge_intensity, pacing
            idx_001 = (0, 14, 16, 20, 29, 21, 23)  # warmth, rule_adherence, verbosity, correction_intensity, curiosity, challenge_level, pacing
            keys_001 = ("warmth", "strictness", "verbosity", "correction_rate", "humor_level", "challenge_intensity", "pacing")
            legacy = dict(zip(keys_001, (result.params_final[i] for i in idx_001)))
            out["final_behavioral_vector_legacy"] = legacy
        print(orjson.dumps(out, option=orjson.OPT_SORT_KEYS).decode("utf-8"))
    else:
        if args.legacy:
            idx_001 = (0, 14, 16, 20, 29, 21, 23)
            keys_001 = ("warmth", "strictness", "verbosity", "correction_rate", "humor_level", "challenge_intensity", "pacing")
            legacy = dict(zip(keys_001, (result.params_final[i] for i in idx_001)))
            print("final_behavioral_vector (legacy 7):", legacy)
        else:
            print("params_final (32):", list(result.params_final))
            print("axis_final (8):", list(result.axis_final))
        print("identity_hash:", result.identity_hash)
        print("configuration_hash:", result.configuration_hash)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="hnh",
        description="HnH — детерминированный движок личности. Симуляция на заданную дату (время только из аргументов).",
        epilog="Команды: run (модель 001, 7 параметров), run-v2 (модель 002, 32 параметра, 8 осей).",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    # ----- run (001) -----
    run_parser = subparsers.add_parser(
        "run",
        help="Запустить симуляцию на одну дату (модель 001: 7 параметров).",
        description="Один шаг симуляции по модели 001. Вывод: final_behavioral_vector (7 полей), active_modifiers. Время задаётся через --date, системные часы не используются.",
    )
    run_parser.add_argument(
        "--date",
        type=str,
        required=True,
        metavar="YYYY-MM-DD",
        help="Дата симуляции (UTC noon).",
    )
    run_parser.add_argument("--seed", type=int, default=0, help="Seed (по умолчанию 0).")
    run_parser.add_argument(
        "--replay",
        action="store_true",
        help="Два прогона и проверка идентичности вывода.",
    )
    run_parser.add_argument(
        "--json",
        action="store_true",
        help="Вывод одной строкой JSON.",
    )
    run_parser.set_defaults(func=_cmd_run)

    # ----- run-v2 (002) -----
    run_v2_parser = subparsers.add_parser(
        "run-v2",
        help="Запустить симуляцию по модели 002 (32 параметра, 8 осей).",
        description="Один шаг по спецификации 002: params_final (32), axis_final (8), конфиг и подпись replay. Опция --legacy даёт сокращённый вывод в стиле 7 параметров.",
    )
    run_v2_parser.add_argument(
        "--date",
        type=str,
        required=True,
        metavar="YYYY-MM-DD",
        help="Дата симуляции (UTC noon).",
    )
    run_v2_parser.add_argument("--seed", type=int, default=0, help="Seed (по умолчанию 0).")
    run_v2_parser.add_argument(
        "--replay",
        action="store_true",
        help="Два прогона и проверка идентичности вывода.",
    )
    run_v2_parser.add_argument(
        "--json",
        action="store_true",
        help="Вывод одной строкой JSON.",
    )
    run_v2_parser.add_argument(
        "--legacy",
        action="store_true",
        help="Дополнительно вывести 7 параметров в формате 001 (для совместимости).",
    )
    run_v2_parser.set_defaults(func=_cmd_run_v2)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
