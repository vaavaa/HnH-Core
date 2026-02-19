"""Tests for fatigue engine: R, S_g, load, recovery, F, L, q (Spec 005 §5-6)."""

import pytest

from hnh.identity.schema import NUM_PARAMETERS, _PARAMETER_LIST
from hnh.lifecycle.fatigue import (
    resilience_from_base_vector,
    global_sensitivity,
    load,
    recovery,
    fatigue_limit,
    update_fatigue,
    normalized_fatigue,
)
from hnh.lifecycle.constants import LifecycleConstants, DEFAULT_LIFECYCLE_CONSTANTS

STABILITY_AXIS = 1


def test_resilience_from_base_vector() -> None:
    base = [0.5] * NUM_PARAMETERS
    for p_ix, (ax, _) in enumerate(_PARAMETER_LIST):
        if ax == STABILITY_AXIS:
            base[p_ix] = 0.8
    r = resilience_from_base_vector(tuple(base))
    assert 0 <= r <= 1
    assert abs(r - 0.8) < 1e-6


def test_global_sensitivity() -> None:
    sens = (0.4,) * NUM_PARAMETERS
    s_g = global_sensitivity(sens)
    assert abs(s_g - 0.4) < 1e-6


def test_load_recovery() -> None:
    c = DEFAULT_LIFECYCLE_CONSTANTS
    ld = load(0.5, 0.5, 0.5, c)
    rec = recovery(0.5, 0.5, c)
    assert ld >= 0 and rec >= 0


def test_fatigue_limit_positive() -> None:
    c = DEFAULT_LIFECYCLE_CONSTANTS
    L = fatigue_limit(0.5, 0.5, c)
    assert L > 0


def test_f_update_growth() -> None:
    c = DEFAULT_LIFECYCLE_CONSTANTS
    f = 1.0
    ld = 1.0
    rec = 0.1
    f_new = update_fatigue(f, ld, rec, c)
    assert f_new > f


def test_f_update_decay() -> None:
    c = DEFAULT_LIFECYCLE_CONSTANTS
    f = 5.0
    ld = 0.01
    rec = 1.0
    f_new = update_fatigue(f, ld, rec, c)
    assert f_new < f


def test_normalized_q() -> None:
    assert 0 <= normalized_fatigue(0, 10) <= 1
    assert abs(normalized_fatigue(5, 10) - 0.5) < 1e-6
    assert normalized_fatigue(15, 10) == 1.0
