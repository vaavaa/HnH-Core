"""
Deterministic identity_hash for tie-break in infer mode (Spec 008, FR-015).
Source: digest of birth_data (canonical JSON, xxhash). Stable across process runs.
"""

from __future__ import annotations

from typing import Any

import orjson
import xxhash

# Per project rules: xxhash for deterministic hash. Not Python's built-in hash().
# Documented in data-model.md: source = digest of birth_data; tie-break = low bit of hash.


def identity_hash_for_tie_break(birth_data: dict[str, Any], *, seed: int = 0) -> bytes:
    """
    Compute deterministic digest of birth_data for tie-break (infer mode).

    Uses orjson (sort keys) + xxhash.xxh3_128. Same birth_data → same digest across runs.
    Tie-break: use (digest[0] & 1) or equivalent; male if odd, female if even (per spec).
    """
    blob = orjson.dumps(birth_data, option=orjson.OPT_SORT_KEYS)
    return xxhash.xxh3_128(blob, seed=seed).digest()


def tie_break_parity(digest: bytes) -> int:
    """Low bit of digest for deterministic male(1) / female(0) tie-break."""
    return digest[0] & 1 if digest else 0
