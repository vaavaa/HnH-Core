#!/usr/bin/env python3
"""
002 demo: Schema (8 axes, 32 parameters) and IdentityCore v0.2.

Shows canonical axis/parameter registry, index mapping, and creating
an Identity with base_vector and sensitivity_vector (32 each).

Run from project root:
  python scripts/002/01_schema_and_identity.py
"""

from __future__ import annotations

from hnh.identity import (
    AXES,
    PARAMETERS,
    IdentityCore,
    get_axis_index,
    get_parameter_index,
    get_parameter_axis_index,
)
from hnh.identity.schema import NUM_AXES, NUM_PARAMETERS, _registry


def main() -> None:
    print("=== 8 axes ===")
    for i, name in enumerate(AXES):
        print(f"  {i}: {name}")
    print(f"\n=== 32 parameters (first 12) ===")
    for i in range(min(12, len(PARAMETERS))):
        axis_ix = get_parameter_axis_index(i)
        print(f"  {i}: {PARAMETERS[i]} (axis {axis_ix}: {AXES[axis_ix]})")
    print("  ...")

    print("\n=== Index mapping ===")
    print(f"  get_axis_index('emotional_tone') = {get_axis_index('emotional_tone')}")
    print(f"  get_parameter_index('warmth') = {get_parameter_index('warmth')}")
    print(f"  get_parameter_axis_index(0) = {get_parameter_axis_index(0)}")

    _registry.discard("script-002-01")
    base = (0.5,) * NUM_PARAMETERS
    sensitivity = (0.6,) * NUM_PARAMETERS
    identity = IdentityCore(
        identity_id="script-002-01",
        base_vector=base,
        sensitivity_vector=sensitivity,
    )
    print("\n=== IdentityCore v0.2 ===")
    print(f"  identity_id: {identity.identity_id}")
    print(f"  identity_hash: {identity.identity_hash[:16]}...")
    print(f"  base_vector length: {len(identity.base_vector)}")
    print(f"  sensitivity_vector length: {len(identity.sensitivity_vector)}")


if __name__ == "__main__":
    main()
