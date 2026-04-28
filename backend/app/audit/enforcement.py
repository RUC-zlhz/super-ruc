"""Shared permission enforcement helpers for S4."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import policies
from app.audit.service import AUDIT_RESULT_DENIED, log_action
from app.core.exceptions import PermissionError
from app.profile.schemas import StudentBasic

EXPORT_PERMISSION_DENIED_CODE = 40330


def join_role_codes(roles: Sequence[str] | str | None) -> str | None:
    role_codes = policies.parse_role_codes(roles)
    if not role_codes:
        return None
    return ",".join(role_codes)


async def audit_forbidden_and_raise(
    db: AsyncSession,
    *,
    event_type: str,
    entity_code: str,
    action: str,
    actor_user_id: int | None,
    actor_role: str | None,
    message: str,
    code: int = 40300,
    entity_id: int | None = None,
    detail: Mapping[str, Any] | None = None,
) -> None:
    await log_action(
        db,
        event_type=event_type,
        entity_code=entity_code,
        action=action,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        result_code=AUDIT_RESULT_DENIED,
        detail=dict(detail) if detail else None,
        message=message,
    )
    await db.commit()
    raise PermissionError(message, code=code)


async def ensure_export_permission(
    db: AsyncSession,
    *,
    roles: Sequence[str] | str | None,
    export_code: str,
    actor_user_id: int | None,
    actor_role: str | None,
    event_type: str,
    entity_code: str,
    action: str,
    message: str,
    code: int = EXPORT_PERMISSION_DENIED_CODE,
    entity_id: int | None = None,
    detail: Mapping[str, Any] | None = None,
) -> None:
    allowed = await policies.can_export_action(db, roles, export_code)
    if allowed:
        return
    await audit_forbidden_and_raise(
        db,
        event_type=event_type,
        entity_code=entity_code,
        action=action,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        message=message,
        code=code,
        entity_id=entity_id,
        detail=detail,
    )


async def sanitize_student_mapping(
    db: AsyncSession,
    *,
    roles: Sequence[str] | str | None,
    data: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    return await policies.apply_student_basic_policies(db, roles, dict(data))


async def sanitize_student_basic(
    db: AsyncSession,
    *,
    roles: Sequence[str] | str | None,
    student: StudentBasic | Mapping[str, Any] | Any,
) -> tuple[StudentBasic, list[str]]:
    if isinstance(student, StudentBasic):
        payload = student.model_dump()
    elif isinstance(student, Mapping):
        payload = StudentBasic.model_validate(student).model_dump()
    else:
        payload = StudentBasic.model_validate(student).model_dump()
    sanitized, masked_fields = await sanitize_student_mapping(
        db,
        roles=roles,
        data=payload,
    )
    return StudentBasic.model_validate(sanitized), masked_fields
