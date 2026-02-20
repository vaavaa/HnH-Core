#!/usr/bin/env python3
"""
Demo: Agent (product and research) — step() over a date range.
Optional: compare with replay_v2 for determinism (same inputs → same outputs).
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

# Add repo root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from hnh.agent import Agent
from hnh.config.replay_config import ReplayConfig
from hnh.identity.schema import IdentityCore, NUM_PARAMETERS
from hnh.identity.sensitivity import compute_sensitivity


def main() -> None:
    birth_data = {
        "positions": [
            {"planet": "Sun", "longitude": 90.0},
            {"planet": "Moon", "longitude": 120.0},
        ],
    }
    config = ReplayConfig(global_max_delta=0.08, shock_threshold=0.5, shock_multiplier=1.0)

    # Product-mode
    agent_product = Agent(birth_data, config=config, lifecycle=False)
    start = date(2020, 6, 1)
    for i in range(5):
        d = start + timedelta(days=i)
        agent_product.step(d)
    print("Product-mode: 5 steps OK")
    print(f"  current_vector[:4] = {agent_product.behavior.current_vector[:4]}")

    # Research-mode (with lifecycle)
    agent_research = Agent(birth_data, config=config, lifecycle=True)
    for i in range(3):
        agent_research.step(start + timedelta(days=i))
    print("Research-mode: 3 steps OK")
    print(f"  F={agent_research.lifecycle.F:.4f} W={agent_research.lifecycle.W:.4f} state={agent_research.lifecycle.state}")

    # Optional: compare with replay_v2 (single step)
    from hnh.astrology.natal_chart import NatalChart
    from hnh.state.replay_v2 import run_step_v2
    from datetime import datetime, timezone

    natal = NatalChart.from_birth_data(birth_data)
    natal_data = natal.to_natal_data()
    sens = compute_sensitivity(natal_data)
    identity = IdentityCore(identity_id="demo-006", base_vector=(0.5,) * NUM_PARAMETERS, sensitivity_vector=sens)
    dt = datetime(2020, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    result = run_step_v2(identity, config, dt, natal_positions=natal_data)
    agent_compare = Agent(birth_data, config=config, lifecycle=False)
    agent_compare.step(dt)
    match = all(abs(a - b) < 1e-6 for a, b in zip(agent_compare.behavior.current_vector, result.params_final))
    print(f"Agent.step() vs replay_v2 (single step): match={match}")


if __name__ == "__main__":
    main()
