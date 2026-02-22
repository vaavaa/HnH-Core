"""
Spec 008: Sex Polarity & 32D Shifts.
Pure components: validation, resolution, sign_polarity, sect, polarity, delta_32, resolver.
"""

from hnh.sex.validation import validate_sex
from hnh.sex.resolution import resolve_sex_mode
from hnh.sex.identity_hash import identity_hash_for_tie_break
from hnh.sex.resolver import resolve_sex, resolve_sex_explicit, InsufficientNatalDataError

__all__ = [
    "validate_sex",
    "resolve_sex_mode",
    "identity_hash_for_tie_break",
    "resolve_sex",
    "resolve_sex_explicit",
    "InsufficientNatalDataError",
]
