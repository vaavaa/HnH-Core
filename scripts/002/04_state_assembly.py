#!/usr/bin/env python3
"""
002 demo: State assembly — base + (bounded_delta × sensitivity) + memory_delta → params_final, axis_final.

Shows assemble_state: formula final[p] = clamp01(base[p] + bounded_delta[p]*sensitivity[p] + memory_delta[p]),
then axis_final = mean of 4 sub-parameters per axis.

Run from project root:
  python scripts/002/04_state_assembly.py
"""

from __future__ import annotations

from hnh.identity.schema import AXES, NUM_PARAMETERS
from hnh.state.assembler import assemble_state


def main() -> None:
    base = (0.5,) * NUM_PARAMETERS
    sensitivity = (0.5,) * NUM_PARAMETERS
    bounded_delta = (0.02,) * NUM_PARAMETERS
    memory_delta = (0.0,) * NUM_PARAMETERS

    params_final, axis_final = assemble_state(base, sensitivity, bounded_delta, memory_delta)

    print("=== State assembly (32 params → 8 axes) ===")
    print(f"  params_final length: {len(params_final)}")
    print(f"  axis_final length: {len(axis_final)}")
    print(f"  All params in [0,1]: {all(0 <= v <= 1 for v in params_final)}")

    print("\n=== axis_final (mean of 4 sub-params per axis) ===")
    for i, (ax_name, val) in enumerate(zip(AXES, axis_final)):
        print(f"  {i} {ax_name}: {val:.4f}")

    print("\n=== With memory_delta on first 4 params ===")
    mem = [0.0] * NUM_PARAMETERS
    mem[0] = 0.03
    mem[1] = -0.02
    params2, axis2 = assemble_state(base, sensitivity, bounded_delta, tuple(mem))
    print(f"  axis_final[0] (emotional_tone): {axis2[0]:.4f}")


if __name__ == "__main__":
    main()
