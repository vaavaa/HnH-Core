"""HnH v0.2 — hierarchical 8×4 personality schema and Identity Core."""

from hnh.identity.schema import (
    AXES,
    PARAMETERS,
    IdentityCore,
    PersonalityAxis,
    PersonalityParameter,
    get_axis_index,
    get_parameter_index,
    get_parameter_axis_index,
)
from hnh.identity.sensitivity import compute_sensitivity, sensitivity_histogram

__all__ = [
    "AXES",
    "PARAMETERS",
    "IdentityCore",
    "PersonalityAxis",
    "PersonalityParameter",
    "compute_sensitivity",
    "sensitivity_histogram",
    "get_axis_index",
    "get_parameter_index",
    "get_parameter_axis_index",
]
