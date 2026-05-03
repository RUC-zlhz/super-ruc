"""字段级权限策略解析与默认基线。"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import RoleFieldPolicy

BASIC_IDENTITY = "basic_identity"
CONTACT = "contact"
ACADEMIC_RECORD = "academic_record"
ACADEMIC_RISK = "academic_risk"
POLITICAL_STATUS = "political_status"
PARTY_STAGE = "party_stage"
DISCIPLINE_RECORD = "discipline_record"
HONOR_RECORD = "honor_record"
REQUEST_RECORD = "request_record"
REQUEST_ATTACHMENT = "request_attachment"
EXPORT_ACTION = "export_action"

EXPORT_STUDENTS_DETAIL = "students_detail"
EXPORT_STUDENTS_SUMMARY = "students_summary"
EXPORT_TRANSCRIPTS_DETAIL = "transcripts_detail"
EXPORT_CURRICULUM_SUMMARY = "curriculum_summary"
EXPORT_PROFILE_SNAPSHOT_DETAIL = "profile_snapshot_detail"
EXPORT_ERROR_REPORT = "error_report"
REQUEST_PROOF_PREVIEW = "proof_preview"

_ALL_ROLES = (
    "SUPER_ADMIN",
    "COLLEGE_LEADER",
    "COUNSELOR",
    "HEAD_TEACHER",
    "YOUTH_LEAGUE_TEACHER",
    "PARTY_BUILD_TEACHER",
    "PARTY_BRANCH_SECRETARY",
    "YOUTH_LEAGUE_SECRETARY",
    "CLASS_MONITOR",
    "STUDENT",
)
_TEACHER_ROLES = (
    "COUNSELOR",
    "HEAD_TEACHER",
    "YOUTH_LEAGUE_TEACHER",
    "PARTY_BUILD_TEACHER",
)
_COLLABORATOR_ROLES = (
    "PARTY_BRANCH_SECRETARY",
    "YOUTH_LEAGUE_SECRETARY",
    "CLASS_MONITOR",
)
_ENTITY_FIELDS: dict[str, tuple[str, ...]] = {
    BASIC_IDENTITY: (
        "student_no",
        "full_name",
        "gender",
        "grade_code",
        "major_code",
        "class_code",
        "enrollment_year",
        "expected_graduation_year",
        "status",
        "enrollment_status",
        "enrollment_status_reason",
        "enrollment_status_updated_at",
    ),
    CONTACT: ("email", "phone_enc"),
    ACADEMIC_RECORD: ("credits", "transcript"),
    ACADEMIC_RISK: ("academic_gap", "risk_level"),
    POLITICAL_STATUS: ("political_status",),
    PARTY_STAGE: ("party_stage",),
    DISCIPLINE_RECORD: ("discipline_record",),
    HONOR_RECORD: ("honor_record",),
    REQUEST_RECORD: ("request_record",),
    REQUEST_ATTACHMENT: ("request_attachment",),
    EXPORT_ACTION: (
        EXPORT_STUDENTS_DETAIL,
        EXPORT_STUDENTS_SUMMARY,
        EXPORT_TRANSCRIPTS_DETAIL,
        EXPORT_CURRICULUM_SUMMARY,
        EXPORT_PROFILE_SNAPSHOT_DETAIL,
        EXPORT_ERROR_REPORT,
        REQUEST_PROOF_PREVIEW,
    ),
}
_STUDENT_FIELD_ENTITIES: dict[str, str] = {
    "student_no": BASIC_IDENTITY,
    "full_name": BASIC_IDENTITY,
    "gender": BASIC_IDENTITY,
    "grade_code": BASIC_IDENTITY,
    "major_code": BASIC_IDENTITY,
    "class_code": BASIC_IDENTITY,
    "enrollment_year": BASIC_IDENTITY,
    "expected_graduation_year": BASIC_IDENTITY,
    "status": BASIC_IDENTITY,
    "enrollment_status": BASIC_IDENTITY,
    "enrollment_status_reason": BASIC_IDENTITY,
    "enrollment_status_updated_at": BASIC_IDENTITY,
    "email": CONTACT,
    "phone_enc": CONTACT,
    "political_status": POLITICAL_STATUS,
}
_MASK_RANK = {
    None: 0,
    "none": 0,
    "partial": 1,
    "full": 2,
}


@dataclass(slots=True)
class PolicyDecision:
    can_read: bool = False
    can_write: bool = False
    mask_strategy: str | None = None


def parse_role_codes(roles: Sequence[str] | str | None) -> list[str]:
    if roles is None:
        return []
    if isinstance(roles, str):
        return [item.strip() for item in roles.split(",") if item.strip()]
    return [str(item).strip() for item in roles if str(item).strip()]


def _blank_role_matrix(role_code: str) -> dict[tuple[str, str], dict[str, Any]]:
    matrix: dict[tuple[str, str], dict[str, Any]] = {}
    for entity_code, fields in _ENTITY_FIELDS.items():
        for field_name in fields:
            matrix[(entity_code, field_name)] = {
                "role_code": role_code,
                "entity_code": entity_code,
                "field_name": field_name,
                "can_read": False,
                "can_write": False,
                "mask_strategy": None,
            }
    return matrix


def _grant(
    matrix: dict[tuple[str, str], dict[str, Any]],
    entity_code: str,
    *,
    fields: Sequence[str] | None = None,
    can_read: bool,
    can_write: bool = False,
    mask_strategy: str | None = None,
) -> None:
    target_fields = fields or _ENTITY_FIELDS[entity_code]
    for field_name in target_fields:
        row = matrix[(entity_code, field_name)]
        row["can_read"] = can_read
        row["can_write"] = can_write
        row["mask_strategy"] = mask_strategy


def _build_default_role_policy_map() -> dict[tuple[str, str, str], dict[str, Any]]:
    policy_map: dict[tuple[str, str, str], dict[str, Any]] = {}

    for role_code in _ALL_ROLES:
        matrix = _blank_role_matrix(role_code)

        if role_code == "SUPER_ADMIN":
            for entity_code in _ENTITY_FIELDS:
                _grant(matrix, entity_code, can_read=True, can_write=entity_code != EXPORT_ACTION)
        elif role_code == "COLLEGE_LEADER":
            for entity_code in (
                BASIC_IDENTITY,
                CONTACT,
                ACADEMIC_RECORD,
                ACADEMIC_RISK,
                POLITICAL_STATUS,
                PARTY_STAGE,
                DISCIPLINE_RECORD,
                HONOR_RECORD,
                REQUEST_RECORD,
                REQUEST_ATTACHMENT,
            ):
                _grant(matrix, entity_code, can_read=True)
            _grant(
                matrix,
                EXPORT_ACTION,
                fields=(EXPORT_STUDENTS_SUMMARY, EXPORT_CURRICULUM_SUMMARY, EXPORT_ERROR_REPORT),
                can_read=True,
            )
            _grant(
                matrix,
                EXPORT_ACTION,
                fields=(REQUEST_PROOF_PREVIEW,),
                can_read=True,
            )
        elif role_code in _TEACHER_ROLES:
            for entity_code in (
                BASIC_IDENTITY,
                CONTACT,
                ACADEMIC_RECORD,
                ACADEMIC_RISK,
                POLITICAL_STATUS,
                PARTY_STAGE,
                HONOR_RECORD,
                REQUEST_RECORD,
                REQUEST_ATTACHMENT,
            ):
                _grant(matrix, entity_code, can_read=True)
            _grant(matrix, POLITICAL_STATUS, can_read=True, can_write=True)
            _grant(matrix, PARTY_STAGE, can_read=True, can_write=True)
            _grant(matrix, REQUEST_RECORD, can_read=True, can_write=True)
            _grant(
                matrix,
                EXPORT_ACTION,
                fields=(EXPORT_CURRICULUM_SUMMARY, EXPORT_ERROR_REPORT, REQUEST_PROOF_PREVIEW),
                can_read=True,
            )
        elif role_code in _COLLABORATOR_ROLES:
            _grant(matrix, POLITICAL_STATUS, can_read=True, mask_strategy="partial")
            _grant(matrix, PARTY_STAGE, can_read=True)
            _grant(matrix, REQUEST_RECORD, can_read=True)
            _grant(matrix, REQUEST_ATTACHMENT, can_read=True, mask_strategy="partial")
        elif role_code == "STUDENT":
            for entity_code in (
                BASIC_IDENTITY,
                CONTACT,
                ACADEMIC_RECORD,
                ACADEMIC_RISK,
                POLITICAL_STATUS,
                PARTY_STAGE,
                HONOR_RECORD,
                REQUEST_RECORD,
                REQUEST_ATTACHMENT,
            ):
                _grant(matrix, entity_code, can_read=True)
            _grant(matrix, REQUEST_RECORD, can_read=True, can_write=True)
            _grant(matrix, REQUEST_ATTACHMENT, can_read=True, can_write=True)
            _grant(matrix, REQUEST_ATTACHMENT, fields=("request_attachment",), can_read=True, can_write=True)
            _grant(matrix, EXPORT_ACTION, fields=(REQUEST_PROOF_PREVIEW,), can_read=True)

        for row in matrix.values():
            policy_map[(role_code, row["entity_code"], row["field_name"])] = row

    return policy_map


_DEFAULT_POLICY_MAP = _build_default_role_policy_map()


def iter_default_role_field_policies() -> list[dict[str, Any]]:
    return [dict(row) for row in _DEFAULT_POLICY_MAP.values()]


def student_policy_field_names() -> tuple[str, ...]:
    """Return student-profile fields controlled by field policies."""

    return tuple(_STUDENT_FIELD_ENTITIES.keys())


def _merge_policy_rows(rows: Sequence[RoleFieldPolicy | Mapping[str, Any]]) -> PolicyDecision:
    if not rows:
        return PolicyDecision()

    can_read = any(bool(getattr(row, "can_read", False) if not isinstance(row, Mapping) else row.get("can_read")) for row in rows)
    can_write = any(bool(getattr(row, "can_write", False) if not isinstance(row, Mapping) else row.get("can_write")) for row in rows)

    readable_masks = []
    for row in rows:
        read_flag = getattr(row, "can_read", False) if not isinstance(row, Mapping) else row.get("can_read")
        if not read_flag:
            continue
        strategy = getattr(row, "mask_strategy", None) if not isinstance(row, Mapping) else row.get("mask_strategy")
        normalized = str(strategy).lower() if strategy not in (None, "") else None
        readable_masks.append(normalized)
    if not readable_masks:
        mask_strategy = None
    else:
        mask_strategy = min(readable_masks, key=lambda item: _MASK_RANK.get(item, 99))
    return PolicyDecision(can_read=can_read, can_write=can_write, mask_strategy=mask_strategy)


async def resolve_field_policy(
    db: AsyncSession,
    roles: Sequence[str] | str | None,
    *,
    entity_code: str,
    field_name: str,
) -> PolicyDecision:
    role_codes = parse_role_codes(roles)
    if not role_codes:
        return PolicyDecision()

    rows = (
        await db.execute(
            select(RoleFieldPolicy).where(
                RoleFieldPolicy.role_code.in_(role_codes),
                RoleFieldPolicy.entity_code == entity_code,
                RoleFieldPolicy.field_name == field_name,
            )
        )
    ).scalars().all()
    if rows:
        return _merge_policy_rows(rows)

    defaults = [
        _DEFAULT_POLICY_MAP[(role_code, entity_code, field_name)]
        for role_code in role_codes
        if (role_code, entity_code, field_name) in _DEFAULT_POLICY_MAP
    ]
    return _merge_policy_rows(defaults)


async def can_export_action(
    db: AsyncSession,
    roles: Sequence[str] | str | None,
    field_name: str,
) -> bool:
    return (
        await resolve_field_policy(
            db,
            roles,
            entity_code=EXPORT_ACTION,
            field_name=field_name,
        )
    ).can_read


def mask_value(value: Any, strategy: str | None) -> Any:
    normalized = str(strategy).lower() if strategy not in (None, "") else "none"
    if value in (None, "") or normalized == "none":
        return value
    if normalized == "full":
        return "***"

    text = str(value)
    if "@" in text:
        local, _, domain = text.partition("@")
        if len(local) <= 1:
            return f"*{'@' + domain if domain else ''}"
        return f"{local[0]}***@{domain}"
    if len(text) <= 2:
        return "*" * len(text)
    if len(text) <= 6:
        return f"{text[0]}***{text[-1]}"
    return f"{text[:2]}***{text[-2:]}"


async def apply_student_basic_policies(
    db: AsyncSession,
    roles: Sequence[str] | str | None,
    data: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    sanitized = dict(data)
    masked_fields: list[str] = []
    for field_name, entity_code in _STUDENT_FIELD_ENTITIES.items():
        if field_name not in sanitized:
            continue
        decision = await resolve_field_policy(
            db,
            roles,
            entity_code=entity_code,
            field_name=field_name,
        )
        if not decision.can_read:
            sanitized[field_name] = None
            masked_fields.append(field_name)
            continue
        if decision.mask_strategy not in (None, "", "none"):
            sanitized[field_name] = mask_value(sanitized[field_name], decision.mask_strategy)
            masked_fields.append(field_name)
    return sanitized, masked_fields
