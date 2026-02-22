"""
Sex_mode resolution (Spec 008, data-model).
Order: birth_data.sex_mode first; if absent, agent/replay config; default "explicit".
"""

from __future__ import annotations

from typing import Any

# Resolution order (documented in data-model.md):
# 1. birth_data.sex_mode
# 2. config.sex_mode (agent or replay config)
# 3. default "explicit"


def resolve_sex_mode(birth_data: dict[str, Any], config: Any = None) -> str:
    """
    Resolve sex_mode for 008 pipeline.

    Resolution order: birth_data.sex_mode first; if absent, config.sex_mode; default "explicit".
    Returns "explicit" | "infer".
    """
    mode = birth_data.get("sex_mode")
    if isinstance(mode, str) and mode.strip().lower() in ("explicit", "infer"):
        return mode.strip().lower()
    if config is not None:
        cfg_mode = getattr(config, "sex_mode", None)
        if isinstance(cfg_mode, str) and cfg_mode.strip().lower() in ("explicit", "infer"):
            return cfg_mode.strip().lower()
    return "explicit"
