"""
SexResolver (Spec 008). Explicit path: birth_data.sex after validation.
Infer path (T015): deterministic inference from sign_polarity_score + sect_score + tie-break.
"""

from __future__ import annotations

from typing import Any

from hnh.sex.resolution import resolve_sex_mode
from hnh.sex.validation import validate_sex
from hnh.sex.sign_polarity import sign_polarity_score
from hnh.sex.sect import sect_score_from_natal
from hnh.sex.identity_hash import identity_hash_for_tie_break, tie_break_parity

# FR-014, FR-010
DEFAULT_INFER_T: float = 0.10
DEFAULT_INFER_K1: float = 1.0
DEFAULT_INFER_K2: float = 0.2
DEFAULT_INFER_BIAS: float = 0.0


class InsufficientNatalDataError(ValueError):
    """Raised when natal data are insufficient for sex inference (e.g. no Sun sign). Fallback to sex=None not permitted."""


def resolve_sex_explicit(birth_data: dict[str, Any], config: Any = None) -> str | None:
    """
    Resolve sex in explicit mode only (T008).
    If sex_mode is "explicit": return validated birth_data.sex ("male"|"female"|None).
    """
    mode = resolve_sex_mode(birth_data, config)
    if mode != "explicit":
        raise NotImplementedError("sex_mode='infer' use resolve_sex() instead")
    return validate_sex(birth_data)


def _infer_sex(
    natal: Any,
    birth_data: dict[str, Any],
    identity_hash_digest: bytes,
    *,
    T: float = DEFAULT_INFER_T,
    k1: float = DEFAULT_INFER_K1,
    k2: float = DEFAULT_INFER_K2,
    bias: float = DEFAULT_INFER_BIAS,
) -> str:
    """
    Infer sex from natal (FR-010..FR-015). Deterministic.
    Raises InsufficientNatalDataError if no Sun sign or sign_polarity_score undefined.
    """
    natal_data = natal.to_natal_data() if hasattr(natal, "to_natal_data") else natal
    planet_signs = {p.name.strip().title(): p.sign_index for p in natal.planets} if hasattr(natal, "planets") else {}
    # Required for inference: at least Sun (data-model)
    if "Sun" not in planet_signs:
        raise InsufficientNatalDataError(
            "Insufficient natal data for sex inference: Sun sign is required (at least one planet with known sign)."
        )
    try:
        sp_score = sign_polarity_score(planet_signs)
    except ValueError as e:
        raise InsufficientNatalDataError(
            "Insufficient natal data for sex inference: cannot compute sign_polarity_score (no planets with known sign)."
        ) from e
    sect_sc = sect_score_from_natal(natal_data)
    S = k1 * sp_score + k2 * float(sect_sc) + bias
    if S > T:
        return "male"
    if S < -T:
        return "female"
    # Tie-break: FR-015 male if low bit 1 else female
    return "male" if tie_break_parity(identity_hash_digest) == 1 else "female"


def resolve_sex(
    birth_data: dict[str, Any],
    config: Any = None,
    natal: Any = None,
    identity_hash_digest: bytes | None = None,
    *,
    infer_T: float = DEFAULT_INFER_T,
    infer_k1: float = DEFAULT_INFER_K1,
    infer_k2: float = DEFAULT_INFER_K2,
    infer_bias: float = DEFAULT_INFER_BIAS,
) -> str | None:
    """
    Resolve sex: explicit or infer per sex_mode (T015).
    explicit: return validate_sex(birth_data) ("male"|"female"|None).
    infer: when sex not provided, infer from natal; requires natal and uses identity_hash_digest for tie-break.
    If identity_hash_digest is None in infer mode, it is computed from birth_data.
    Raises InsufficientNatalDataError when infer and natal data insufficient (no fallback to None).
    """
    mode = resolve_sex_mode(birth_data, config)
    if mode == "explicit":
        return validate_sex(birth_data)
    # infer
    if natal is None:
        raise ValueError("sex_mode='infer' requires natal for inference")
    digest = identity_hash_digest if identity_hash_digest is not None else identity_hash_for_tie_break(birth_data)
    return _infer_sex(natal, birth_data, digest, T=infer_T, k1=infer_k1, k2=infer_k2, bias=infer_bias)
