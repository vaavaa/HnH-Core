"""
T043, T046: No datetime.now() in core; constitution compliance checks.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


# Core modules (no datetime.now() allowed)
CORE_MODULE_DIRS = ["hnh/core", "hnh/state", "hnh/memory", "hnh/astrology", "hnh/logging"]


def _collect_py_files() -> list[Path]:
    root = Path(__file__).resolve().parent.parent.parent
    out: list[Path] = []
    for subdir in CORE_MODULE_DIRS:
        d = root / subdir
        if not d.exists():
            continue
        for p in d.rglob("*.py"):
            out.append(p)
    return out


def test_no_datetime_now_in_core_modules() -> None:
    """T043: Core modules must not use datetime.now() (time must be injected)."""
    root = Path(__file__).resolve().parent.parent.parent
    found: list[tuple[str, int]] = []
    for path in _collect_py_files():
        rel = path.relative_to(root)
        try:
            src = path.read_text()
        except Exception:
            continue
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "datetime"
                        and node.func.attr == "now"
                    ):
                        found.append((str(rel), node.lineno or 0))
    assert not found, f"datetime.now() found in core: {found}"


def test_no_unseeded_random_in_core_modules() -> None:
    """Constitution: no unseeded randomness in core (no random module in core)."""
    root = Path(__file__).resolve().parent.parent.parent
    found: list[str] = []
    for path in _collect_py_files():
        rel = path.relative_to(root)
        src = path.read_text()
        if "import random" in src or "from random import" in src:
            found.append(str(rel))
    assert not found, f"random module imported in core: {found}"
