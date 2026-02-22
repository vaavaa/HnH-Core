"""T012: Contract test FR-022a — W32 and sex_delta_32 order matches canonical 32D (002)."""

import pytest

from hnh.identity.schema import NUM_PARAMETERS, NUM_AXES, _PARAMETER_LIST
from hnh.sex.delta_32 import W32_V1, compute_sex_delta_32


def test_w32_length_matches_schema():
    """W32 and sex_delta_32 length MUST match NUM_PARAMETERS (32)."""
    assert len(W32_V1) == NUM_PARAMETERS
    delta = compute_sex_delta_32(0.5)
    assert len(delta) == NUM_PARAMETERS


def test_w32_axes_grouping():
    """8 axes × 4 parameters: indices 0-3 axis 0, 4-7 axis 1, ... (002 order)."""
    assert len(W32_V1) == 32
    for axis in range(NUM_AXES):
        for j in range(4):
            idx = axis * 4 + j
            assert _PARAMETER_LIST[idx][0] == axis
