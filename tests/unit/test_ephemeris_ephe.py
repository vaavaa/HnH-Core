"""
Проверка наличия каталога эфемерид и API get_ephe_path / check_ephe_available.
Не требует pyswisseph; проверяет только путь и наличие .se1 в ephe.
"""

from __future__ import annotations

import pytest

from hnh.astrology import ephemeris as eph


def test_get_ephe_path_returns_path_object():
    """get_ephe_path() возвращает Path, указывающий на каталог ephe в корне репозитория."""
    p = eph.get_ephe_path()
    assert p.name == "ephe"
    assert p.parent.name == "core" or "ephe" in str(p)


def test_check_ephe_available_returns_tuple_of_two_bools():
    """check_ephe_available() возвращает (dir_exists, has_se1)."""
    dir_ok, files_ok = eph.check_ephe_available()
    assert isinstance(dir_ok, bool)
    assert isinstance(files_ok, bool)
    if not dir_ok:
        assert files_ok is False


def test_check_ephe_available_files_implies_directory():
    """Если есть файлы .se1, каталог должен существовать."""
    dir_ok, files_ok = eph.check_ephe_available()
    if files_ok:
        assert dir_ok is True
