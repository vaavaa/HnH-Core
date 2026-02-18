#!/usr/bin/env python3
"""
002 demo: Relational Memory v2 — get_memory_delta_32, memory_signature.

Shows user-scoped memory, events, then get_memory_delta_32(global_max_delta)
and memory_signature for replay.

Run from project root:
  python scripts/002/05_memory_v2.py
"""

from __future__ import annotations

from hnh.identity.schema import NUM_PARAMETERS
from hnh.memory.relational import RelationalMemory


def main() -> None:
    print("=== RelationalMemory (user-scoped) ===")
    memory = RelationalMemory("user-bob")
    memory.add_event(1, "interaction", {"topic": "intro"})
    memory.add_event(2, "interaction", {"topic": "practice"})
    memory.add_event(3, "error", {"type": "timeout"})

    print("  Events:", [e["type"] for e in memory.events])
    print("  Derived:", memory.derived_metrics())

    global_max_delta = 0.2
    delta_32 = memory.get_memory_delta_32(global_max_delta)
    print(f"\n=== get_memory_delta_32(global_max_delta={global_max_delta}) ===")
    print(f"  length: {len(delta_32)}")
    cap = 0.5 * global_max_delta
    print(f"  |memory_delta[p]| <= {cap}: {all(abs(v) <= cap + 1e-9 for v in delta_32)}")
    non_zero = [i for i, v in enumerate(delta_32) if v != 0.0]
    print(f"  Non-zero count: {len(non_zero)}")

    sig = memory.memory_signature()
    print(f"\n=== memory_signature (for replay) ===")
    print(f"  {sig[:24]}...")


if __name__ == "__main__":
    main()
