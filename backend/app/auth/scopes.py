"""Role scope-code helpers shared by admin imports and scoped views."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCOPE_GLOBAL = "GLOBAL"
SCOPE_CLASS = "CLASS"
SCOPE_MAJOR = "MAJOR"
SCOPE_GRADE = "GRADE"
SCOPED_TYPES = {SCOPE_CLASS, SCOPE_MAJOR, SCOPE_GRADE}
VALID_SCOPE_TYPES = {SCOPE_GLOBAL, *SCOPED_TYPES}


@dataclass(slots=True)
class StudentScopeSet:
    is_global: bool = False
    class_codes: set[str] = field(default_factory=set)
    major_codes: set[str] = field(default_factory=set)
    grade_codes: set[str] = field(default_factory=set)
    legacy_codes: set[str] = field(default_factory=set)

    def is_empty(self) -> bool:
        return not self.is_global and not (
            self.class_codes
            or self.major_codes
            or self.grade_codes
            or self.legacy_codes
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "is_global": self.is_global,
            "class_codes": self.class_codes,
            "major_codes": self.major_codes,
            "grade_codes": self.grade_codes,
            "legacy_codes": self.legacy_codes,
        }


def normalize_scope_type(scope_type: str | None) -> str:
    return (scope_type or SCOPE_GLOBAL).strip().upper() or SCOPE_GLOBAL


def build_scope_code(scope_type: str | None, scope_code: str | None) -> str | None:
    normalized_type = normalize_scope_type(scope_type)
    raw_code = (scope_code or "").strip()
    if normalized_type == SCOPE_GLOBAL:
        return None
    return f"{normalized_type}:{raw_code}"


def split_scope_code(scope_code: str | None) -> tuple[str, str] | None:
    raw = (scope_code or "").strip()
    if not raw:
        return None
    if ":" in raw:
        prefix, value = raw.split(":", 1)
        normalized_type = prefix.strip().upper()
        stripped_value = value.strip()
        if normalized_type in SCOPED_TYPES and stripped_value:
            return normalized_type, stripped_value
    return "LEGACY", raw


def split_student_scope_codes(scope_codes: list[str] | tuple[str, ...] | set[str]) -> StudentScopeSet:
    scope = StudentScopeSet()
    for raw_scope in scope_codes:
        parsed = split_scope_code(raw_scope)
        if parsed is None:
            continue
        scope_type, value = parsed
        if scope_type == SCOPE_CLASS:
            scope.class_codes.add(value)
        elif scope_type == SCOPE_MAJOR:
            scope.major_codes.add(value)
        elif scope_type == SCOPE_GRADE:
            scope.grade_codes.add(value)
        else:
            scope.legacy_codes.add(value)
    return scope


def student_in_scope(student: Any, scope: StudentScopeSet | dict[str, Any]) -> bool:
    if isinstance(scope, dict):
        if scope.get("is_global"):
            return True
        class_codes = scope.get("class_codes") or set()
        major_codes = scope.get("major_codes") or set()
        grade_codes = scope.get("grade_codes") or set()
        legacy_codes = scope.get("legacy_codes") or set()
    else:
        if scope.is_global:
            return True
        class_codes = scope.class_codes
        major_codes = scope.major_codes
        grade_codes = scope.grade_codes
        legacy_codes = scope.legacy_codes

    class_code = getattr(student, "class_code", None) or ""
    major_code = getattr(student, "major_code", None) or ""
    grade_code = getattr(student, "grade_code", None) or ""
    return bool(
        (class_code and class_code in class_codes)
        or (major_code and major_code in major_codes)
        or (grade_code and grade_code in grade_codes)
        or (class_code and class_code in legacy_codes)
        or (major_code and major_code in legacy_codes)
        or (grade_code and grade_code in legacy_codes)
    )
