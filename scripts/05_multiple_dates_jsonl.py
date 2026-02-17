#!/usr/bin/env python3
"""
Пример: симуляция по нескольким датам, вывод в формате JSON Lines (одна строка JSON на дату).

Удобно для экспорта в файл или конвейеров:
  python scripts/05_multiple_dates_jsonl.py 2024-01-01 2024-01-07
  python scripts/05_multiple_dates_jsonl.py 2024-01-01 2024-01-31 > january.jsonl
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone

from hnh.core.identity import IdentityCore
from hnh.core.parameters import BehavioralVector
from hnh.state.replay import run_step


def main() -> None:
    if len(sys.argv) < 3:
        print("Использование: python scripts/05_multiple_dates_jsonl.py START_DATE END_DATE", file=sys.stderr)
        print("  Например: python scripts/05_multiple_dates_jsonl.py 2024-01-01 2024-01-07", file=sys.stderr)
        sys.exit(1)

    start_str, end_str = sys.argv[1], sys.argv[2]
    start = datetime.strptime(start_str, "%Y-%m-%d").replace(
        tzinfo=timezone.utc, hour=12, minute=0, second=0, microsecond=0
    )
    end = datetime.strptime(end_str, "%Y-%m-%d").replace(
        tzinfo=timezone.utc, hour=12, minute=0, second=0, microsecond=0
    )
    if start > end:
        start, end = end, start

    base = BehavioralVector(
        warmth=0.5, strictness=0.4, verbosity=0.6, correction_rate=0.3,
        humor_level=0.5, challenge_intensity=0.4, pacing=0.5,
    )
    identity = IdentityCore(
        identity_id="script-05-multi",
        base_traits=base,
        symbolic_input=None,
    )

    current = start
    while current <= end:
        state = run_step(identity, current, seed=0)
        record = {
            "date": current.strftime("%Y-%m-%d"),
            "injected_time": state.injected_time,
            "final_behavioral_vector": state.final_behavior_vector.to_dict(),
        }
        print(json.dumps(record, sort_keys=True, ensure_ascii=True))
        current += timedelta(days=1)


if __name__ == "__main__":
    main()
