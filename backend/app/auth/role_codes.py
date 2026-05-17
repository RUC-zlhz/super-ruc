"""Canonical role-code helpers."""
from __future__ import annotations

from collections.abc import Iterable

ROLE_CODE_PARTY_BRANCH_SECRETARY = "PARTY_BRANCH_SECRETARY"
ROLE_CODE_YOUTH_LEAGUE_SECRETARY = "YOUTH_LEAGUE_SECRETARY"
ROLE_CODE_CLASS_MONITOR = "CLASS_MONITOR"

LEGACY_ROLE_CODE_CLASS_CADRE = "CLASS_CADRE"
LEGACY_ROLE_CODE_CLASS_LEADER = "CLASS_LEADER"
LEGACY_ROLE_CODE_YOUTH_BRANCH_SECRETARY = "YOUTH_BRANCH_SECRETARY"

ROLE_CODE_COLLABORATOR_ROLES = (
    ROLE_CODE_PARTY_BRANCH_SECRETARY,
    ROLE_CODE_YOUTH_LEAGUE_SECRETARY,
    ROLE_CODE_CLASS_MONITOR,
)

_ROLE_CODE_ALIASES: dict[str, str] = {
    LEGACY_ROLE_CODE_CLASS_CADRE: ROLE_CODE_CLASS_MONITOR,
    LEGACY_ROLE_CODE_CLASS_LEADER: ROLE_CODE_CLASS_MONITOR,
    LEGACY_ROLE_CODE_YOUTH_BRANCH_SECRETARY: ROLE_CODE_YOUTH_LEAGUE_SECRETARY,
}
_ROLE_CODE_LOOKUP_ALIASES: dict[str, tuple[str, ...]] = {
    ROLE_CODE_YOUTH_LEAGUE_SECRETARY: (
        ROLE_CODE_YOUTH_LEAGUE_SECRETARY,
        LEGACY_ROLE_CODE_YOUTH_BRANCH_SECRETARY,
    ),
    ROLE_CODE_CLASS_MONITOR: (
        ROLE_CODE_CLASS_MONITOR,
        LEGACY_ROLE_CODE_CLASS_CADRE,
        LEGACY_ROLE_CODE_CLASS_LEADER,
    ),
}


def normalize_role_code(role_code: str | None) -> str | None:
    if role_code is None:
        return None
    normalized = str(role_code).strip().upper()
    if not normalized:
        return None
    return _ROLE_CODE_ALIASES.get(normalized, normalized)


def normalize_role_codes(role_codes: Iterable[str | None]) -> list[str]:
    normalized_codes: list[str] = []
    seen: set[str] = set()
    for role_code in role_codes:
        normalized = normalize_role_code(role_code)
        if normalized is None or normalized in seen:
            continue
        seen.add(normalized)
        normalized_codes.append(normalized)
    return normalized_codes


def expand_role_codes_for_lookup(role_codes: Iterable[str | None]) -> list[str]:
    lookup_codes: list[str] = []
    seen: set[str] = set()
    for role_code in normalize_role_codes(role_codes):
        for candidate in _ROLE_CODE_LOOKUP_ALIASES.get(role_code, (role_code,)):
            if candidate in seen:
                continue
            seen.add(candidate)
            lookup_codes.append(candidate)
    return lookup_codes
