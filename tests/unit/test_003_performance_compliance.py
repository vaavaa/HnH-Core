"""
Spec 003 — Performance optimization compliance.
Tests: no stdlib json in hnh/ core path; key hashes use xxhash.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Root of the repository (parent of hnh/)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HNH_ROOT = REPO_ROOT / "hnh"


def _python_files_under_hnh() -> list[Path]:
    return [p for p in HNH_ROOT.rglob("*.py") if p.is_file()]


def test_hnh_no_stdlib_json_import() -> None:
    """003 FR-P1: In hnh/ there must be no 'import json' (or 'from json import ...')."""
    violations: list[tuple[str, int]] = []
    for path in _python_files_under_hnh():
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("import json") or stripped.startswith("from json import"):
                violations.append((str(path.relative_to(REPO_ROOT)), i))
    assert not violations, f"Found stdlib json import in hnh/: {violations}"


def test_hnh_no_json_dumps_loads() -> None:
    """003 FR-P1: In hnh/ there must be no stdlib json.dumps or json.loads (orjson is allowed)."""
    violations: list[tuple[str, int]] = []
    for path in _python_files_under_hnh():
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            # Only flag stdlib json usage (e.g. "json.dumps" not "orjson.dumps")
            if "orjson" in line:
                continue
            if "json.dumps" in line or "json.loads" in line:
                violations.append((str(path.relative_to(REPO_ROOT)), i))
    assert not violations, f"Found stdlib json.dumps/json.loads in hnh/: {violations}"


def test_hnh_no_hashlib_import() -> None:
    """003 FR-P2: In hnh/ there must be no 'import hashlib' for hashing (all use xxhash)."""
    violations: list[tuple[str, int]] = []
    for path in _python_files_under_hnh():
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("import hashlib") or stripped.startswith("from hashlib import"):
                violations.append((str(path.relative_to(REPO_ROOT)), i))
    assert not violations, f"Found hashlib import in hnh/: {violations}"


def test_identity_hash_uses_xxhash() -> None:
    """003: identity_hash (IdentityCore v0.2) returns 32-char hex (xxh3_128)."""
    from hnh.identity.schema import IdentityCore

    # IdentityCore.identity_hash uses xxh3_128 → 32 hex chars
    base = (0.5,) * 32
    sens = (0.4,) * 32
    core = IdentityCore(identity_id="test-003-compliance", base_vector=base, sensitivity_vector=sens)
    h = core.identity_hash
    assert len(h) == 32, "xxh3_128 hexdigest is 32 chars"
    assert all(c in "0123456789abcdef" for c in h), "hex string"


def test_configuration_hash_uses_xxhash() -> None:
    """003: compute_configuration_hash returns 32-char hex (xxh3_128)."""
    from hnh.config.replay_config import ReplayConfig, compute_configuration_hash

    config = ReplayConfig(global_max_delta=0.15, shock_threshold=0.8, shock_multiplier=1.0)
    h = compute_configuration_hash(config)
    assert len(h) == 32
    assert all(c in "0123456789abcdef" for c in h)


def test_memory_signature_uses_xxhash() -> None:
    """003: RelationalMemory.memory_signature returns 32-char hex."""
    from hnh.memory.relational import RelationalMemory

    mem = RelationalMemory(user_id="u1")
    h = mem.memory_signature()
    assert len(h) == 32
    assert all(c in "0123456789abcdef" for c in h)
