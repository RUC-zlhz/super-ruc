"""profile 服务层 — FR-018 学生画像。"""
from __future__ import annotations

import html as html_escape
import io
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.enforcement import (
    ensure_export_permission,
    sanitize_student_basic,
)
from app.audit.policies import EXPORT_PROFILE_SNAPSHOT_DETAIL, student_policy_field_names
from app.audit.service import build_audit_detail, log_action
from app.auth import repository as auth_repo
from app.auth.models import Student
from app.core.exceptions import BizError, NotFoundError, PermissionError
from app.profile import repository as repo
from app.profile.models import (
    PROFILE_APPROVAL_APPROVED,
    PROFILE_APPROVAL_PENDING,
    PROFILE_APPROVAL_REJECTED,
    PROFILE_FACT_COMPETITION,
    PROFILE_FACT_LEADERSHIP,
    PROFILE_FACT_PRACTICE,
    PROFILE_FACT_RESEARCH,
    PROFILE_FULL_VIEW_FIELD_PREFIX,
    PROFILE_FULL_VIEW_MARKER_PREFIX,
    PROFILE_FULL_VIEW_TARGET_PROFILE_FACTS,
    PROFILE_FULL_VIEW_TARGET_STUDENT_FIELD,
    PROFILE_SOURCE_IMPORT,
    PROFILE_SOURCE_STUDENT_SELF,
    PROFILE_SOURCE_SYSTEM,
    PROFILE_SOURCE_TEACHER_ENTRY,
    ProfileCorrection,
    ProfileFact,
)
from app.profile.schemas import (
    ProfileFactOut,
    ProfileFactStudentView,
    ProfileFactSubmissionOut,
    ProfileFullViewRequestOut,
    ProfileStudentSelfView,
    ProfileSummary,
    StudentBasic,
)

_GLOBAL_PROFILE_ROLES = {"SUPER_ADMIN", "COLLEGE_LEADER"}
_SCOPED_PROFILE_ROLES = {"COUNSELOR", "HEAD_TEACHER"}
_PROFILE_SOURCE_LABELS = {
    PROFILE_SOURCE_IMPORT: "批量导入",
    PROFILE_SOURCE_TEACHER_ENTRY: "老师录入",
    PROFILE_SOURCE_STUDENT_SELF: "学生补录",
    PROFILE_SOURCE_SYSTEM: "系统同步",
}
_FULL_VIEW_FIELD_KIND = "FIELD:"
_FULL_VIEW_FACTS_KIND = "FACTS"


@dataclass(slots=True)
class _FullViewGrants:
    student_fields: set[str]
    profile_facts: bool = False


def _full_view_requester_marker(requester_user_id: int) -> str:
    return f"{PROFILE_FULL_VIEW_MARKER_PREFIX}{requester_user_id}"


def _parse_full_view_requester_id(row: ProfileCorrection) -> int | None:
    marker = row.current_value or ""
    if not marker.startswith(PROFILE_FULL_VIEW_MARKER_PREFIX):
        return None
    try:
        return int(marker[len(PROFILE_FULL_VIEW_MARKER_PREFIX):])
    except ValueError:
        return None


def _allowed_student_full_view_fields() -> set[str]:
    return set(student_policy_field_names()) & set(StudentBasic.model_fields)


def _encode_full_view_field_name(target_type: str, field_name: str | None) -> str:
    normalized = (target_type or "").strip().upper()
    if normalized == PROFILE_FULL_VIEW_TARGET_STUDENT_FIELD:
        field = (field_name or "").strip()
        if field not in _allowed_student_full_view_fields():
            raise BizError("不支持申请该画像字段的完整查看", code=40190)
        return f"{PROFILE_FULL_VIEW_FIELD_PREFIX}{_FULL_VIEW_FIELD_KIND}{field}"
    if normalized == PROFILE_FULL_VIEW_TARGET_PROFILE_FACTS:
        return f"{PROFILE_FULL_VIEW_FIELD_PREFIX}{_FULL_VIEW_FACTS_KIND}"
    raise BizError("不支持的完整查看申请目标", code=40191)


def _decode_full_view_field_name(encoded: str) -> tuple[str, str | None]:
    if encoded == f"{PROFILE_FULL_VIEW_FIELD_PREFIX}{_FULL_VIEW_FACTS_KIND}":
        return PROFILE_FULL_VIEW_TARGET_PROFILE_FACTS, None
    prefix = f"{PROFILE_FULL_VIEW_FIELD_PREFIX}{_FULL_VIEW_FIELD_KIND}"
    if encoded.startswith(prefix):
        return PROFILE_FULL_VIEW_TARGET_STUDENT_FIELD, encoded[len(prefix):]
    return "UNKNOWN", None


def _build_full_view_request_out(
    row: ProfileCorrection, user_names: dict[int, str] | None = None
) -> ProfileFullViewRequestOut:
    target_type, field_name = _decode_full_view_field_name(row.field_name)
    requester_user_id = _parse_full_view_requester_id(row)
    return ProfileFullViewRequestOut(
        id=row.id,
        student_id=row.student_id,
        requester_user_id=requester_user_id,
        requester_name=(user_names or {}).get(requester_user_id or 0),
        target_type=target_type,
        field_name=field_name,
        reason=row.reason,
        status=row.status,
        handled_by=row.handled_by,
        handled_at=row.handled_at,
        handler_comment=row.handler_comment,
        created_at=row.created_at,
    )


async def _load_full_view_request_user_names(
    db: AsyncSession, rows: list[ProfileCorrection]
) -> dict[int, str]:
    user_ids = {
        user_id
        for row in rows
        for user_id in (_parse_full_view_requester_id(row), row.handled_by)
        if user_id is not None
    }
    return await _load_user_name_map(db, user_ids)


async def _load_full_view_grants(
    db: AsyncSession, *, student_id: int, requester_user_id: int
) -> _FullViewGrants:
    rows = await repo.list_approved_full_view_requests(
        db,
        student_id=student_id,
        requester_user_id=requester_user_id,
    )
    fields: set[str] = set()
    profile_facts = False
    for row in rows:
        target_type, field_name = _decode_full_view_field_name(row.field_name)
        if target_type == PROFILE_FULL_VIEW_TARGET_PROFILE_FACTS:
            profile_facts = True
        elif target_type == PROFILE_FULL_VIEW_TARGET_STUDENT_FIELD and field_name:
            fields.add(field_name)
    return _FullViewGrants(student_fields=fields, profile_facts=profile_facts)


async def _sanitize_student_basic_with_grants(
    db: AsyncSession,
    *,
    roles: str | None,
    student: Student,
    grants: _FullViewGrants,
) -> tuple[StudentBasic, list[str]]:
    sanitized, masked_fields = await sanitize_student_basic(
        db,
        roles=roles,
        student=student,
    )
    if not grants.student_fields:
        return sanitized, masked_fields

    payload = sanitized.model_dump()
    original = _build_student_basic(student).model_dump()
    remaining_masked = set(masked_fields)
    for field_name in grants.student_fields:
        if field_name in payload and field_name in original:
            payload[field_name] = original[field_name]
            remaining_masked.discard(field_name)
    return StudentBasic.model_validate(payload), sorted(remaining_masked)


def _summary_counters(counts: dict[str, float]) -> dict[str, Any]:
    return {
        "research_count": int(counts.get(PROFILE_FACT_RESEARCH, 0)),
        "competition_count": int(counts.get(PROFILE_FACT_COMPETITION, 0)),
        "practice_count": int(counts.get(PROFILE_FACT_PRACTICE, 0)),
        "volunteer_hours": float(counts.get("VOLUNTEER_HOURS", 0)),
        "leadership_count": int(counts.get(PROFILE_FACT_LEADERSHIP, 0)),
    }


def _get_source_label(source: str | None) -> str | None:
    if source is None:
        return None
    return _PROFILE_SOURCE_LABELS.get(source, source)


def _get_review_comment(fact: ProfileFact) -> str | None:
    if isinstance(fact.extra, dict):
        value = fact.extra.get("review_comment")
        return str(value) if value not in (None, "") else None
    return None


def _set_review_comment(fact: ProfileFact, comment: str | None) -> None:
    extra = dict(fact.extra or {})
    if comment:
        extra["review_comment"] = comment
    else:
        extra.pop("review_comment", None)
    fact.extra = extra or None


def _build_student_basic(student: Student) -> StudentBasic:
    return StudentBasic.model_validate(student)


def _build_fact_admin_view(
    fact: ProfileFact, user_names: dict[int, str]
) -> ProfileFactOut:
    return ProfileFactOut(
        id=fact.id,
        student_id=fact.student_id,
        fact_type=fact.fact_type,
        title=fact.title,
        description=fact.description,
        role_in_activity=fact.role_in_activity,
        started_on=fact.started_on,
        ended_on=fact.ended_on,
        hours=float(fact.hours) if fact.hours is not None else None,
        rank_label=fact.rank_label,
        attachments=fact.attachments,
        extra=fact.extra,
        source=fact.source,
        source_label=_get_source_label(fact.source),
        source_ref=fact.source_ref,
        approval_status=fact.approval_status,
        is_sensitive=fact.is_sensitive,
        created_by=fact.created_by,
        updated_by=fact.updated_by,
        created_by_name=user_names.get(fact.created_by or 0),
        updated_by_name=user_names.get(fact.updated_by or 0),
        updated_at=fact.updated_at,
        review_comment=_get_review_comment(fact),
    )


def _build_fact_student_view(fact: ProfileFact) -> ProfileFactStudentView:
    return ProfileFactStudentView(
        id=fact.id,
        fact_type=fact.fact_type,
        title=fact.title,
        description=fact.description,
        role_in_activity=fact.role_in_activity,
        started_on=fact.started_on,
        ended_on=fact.ended_on,
        hours=float(fact.hours) if fact.hours is not None else None,
        rank_label=fact.rank_label,
        attachments=fact.attachments,
        approval_status=fact.approval_status,
        updated_at=fact.updated_at,
    )


def _build_fact_submission_view(fact: ProfileFact) -> ProfileFactSubmissionOut:
    return ProfileFactSubmissionOut(
        id=fact.id,
        fact_type=fact.fact_type,
        title=fact.title,
        description=fact.description,
        role_in_activity=fact.role_in_activity,
        started_on=fact.started_on,
        ended_on=fact.ended_on,
        hours=float(fact.hours) if fact.hours is not None else None,
        rank_label=fact.rank_label,
        attachments=fact.attachments,
        approval_status=fact.approval_status,
        review_comment=_get_review_comment(fact),
        updated_at=fact.updated_at,
    )


async def _load_profile_scope(
    db: AsyncSession, viewer_user_id: int
) -> dict[str, Any]:
    roles = await auth_repo.list_user_roles(db, viewer_user_id)
    role_codes = {row.role_code for row in roles}
    if role_codes & _GLOBAL_PROFILE_ROLES:
        return {
            "is_global": True,
            "class_codes": set(),
            "major_codes": set(),
            "legacy_codes": set(),
        }

    class_codes: set[str] = set()
    major_codes: set[str] = set()
    legacy_codes: set[str] = set()
    for row in roles:
        if row.role_code not in _SCOPED_PROFILE_ROLES:
            continue
        scope_code = (row.scope_code or "").strip()
        if not scope_code:
            continue
        upper = scope_code.upper()
        if upper.startswith("CLASS:"):
            value = scope_code.split(":", 1)[1].strip()
            if value:
                class_codes.add(value)
        elif upper.startswith("MAJOR:"):
            value = scope_code.split(":", 1)[1].strip()
            if value:
                major_codes.add(value)
        else:
            legacy_codes.add(scope_code)
    return {
        "is_global": False,
        "class_codes": class_codes,
        "major_codes": major_codes,
        "legacy_codes": legacy_codes,
    }


def _scope_is_empty(scope: dict[str, Any]) -> bool:
    return not scope["is_global"] and not (
        scope["class_codes"] or scope["major_codes"] or scope["legacy_codes"]
    )


def _student_in_scope(student: Student, scope: dict[str, Any]) -> bool:
    if scope["is_global"]:
        return True
    class_code = student.class_code or ""
    major_code = student.major_code or ""
    return bool(
        (class_code and class_code in scope["class_codes"])
        or (major_code and major_code in scope["major_codes"])
        or (class_code and class_code in scope["legacy_codes"])
        or (major_code and major_code in scope["legacy_codes"])
    )


async def _log_profile_forbidden(
    db: AsyncSession,
    *,
    action: str,
    student_id: int | None,
    actor_user_id: int,
    actor_role: str | None,
    detail: dict[str, Any] | None = None,
) -> None:
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="STUDENT_PROFILE",
        action=action,
        entity_id=student_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        result_code="FORBIDDEN",
        detail=detail,
    )
    await db.commit()


async def _ensure_profile_scope_available(
    db: AsyncSession,
    *,
    viewer_user_id: int,
) -> dict[str, Any]:
    scope = await _load_profile_scope(db, viewer_user_id)
    if _scope_is_empty(scope):
        raise PermissionError("未配置画像查看范围", code=40320)
    return scope


async def _ensure_student_access(
    db: AsyncSession,
    student_id: int,
    *,
    viewer_user_id: int,
    viewer_role: str | None,
    denied_action: str,
    denied_detail: dict[str, Any] | None = None,
) -> Student:
    student = await repo.get_student(db, student_id)
    if student is None:
        raise NotFoundError("学生不存在")
    scope = await _load_profile_scope(db, viewer_user_id)
    if not _student_in_scope(student, scope):
        await _log_profile_forbidden(
            db,
            action=denied_action,
            student_id=student_id,
            actor_user_id=viewer_user_id,
            actor_role=viewer_role,
            detail=denied_detail or {"student_id": student_id},
        )
        raise PermissionError("无权访问该学生画像", code=40321)
    return student


async def _load_user_name_map(
    db: AsyncSession, user_ids: set[int]
) -> dict[int, str]:
    rows = await auth_repo.get_users_by_ids(db, user_ids)
    return {user_id: row.display_name for user_id, row in rows.items()}


async def _load_admin_summary(
    db: AsyncSession,
    student_id: int,
    *,
    viewer_user_id: int,
    viewer_role: str | None,
    denied_action: str,
) -> tuple[Student, list[ProfileFact], dict[str, float], dict[int, str]]:
    student = await _ensure_student_access(
        db,
        student_id,
        viewer_user_id=viewer_user_id,
        viewer_role=viewer_role,
        denied_action=denied_action,
    )
    facts = await repo.list_facts(db, student_id, only_approved=True)
    counts = await repo.count_by_type(db, student_id)
    user_names = await _load_user_name_map(
        db,
        {
            user_id
            for fact in facts
            for user_id in (fact.created_by, fact.updated_by)
            if user_id is not None
        },
    )
    return student, facts, counts, user_names


async def search_students_admin(
    db: AsyncSession,
    *,
    q: str | None,
    grade_code: str | None,
    major_code: str | None,
    class_code: str | None,
    include_non_active: bool,
    enrollment_status: str | None,
    page: int,
    size: int,
    viewer_user_id: int,
    viewer_role: str | None,
) -> tuple[list[StudentBasic], int]:
    scope = await _ensure_profile_scope_available(db, viewer_user_id=viewer_user_id)
    rows, total = await repo.search_students(
        db,
        q=q,
        grade_code=grade_code,
        major_code=major_code,
        class_code=class_code,
        class_scope_codes=scope["class_codes"],
        major_scope_codes=scope["major_codes"],
        legacy_scope_codes=scope["legacy_codes"],
        include_non_active=include_non_active,
        enrollment_status=enrollment_status,
        page=page,
        size=size,
    )
    items: list[StudentBasic] = []
    masked_fields: set[str] = set()
    for row in rows:
        sanitized, current_masked = await sanitize_student_basic(
            db,
            roles=viewer_role,
            student=row,
        )
        items.append(sanitized)
        masked_fields.update(current_masked)
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="STUDENT_PROFILE",
        action="SEARCH_ADMIN",
        actor_user_id=viewer_user_id,
        actor_role=viewer_role,
        detail=build_audit_detail(
            scope={
                "class_codes": sorted(scope["class_codes"]),
                "major_codes": sorted(scope["major_codes"]),
                "legacy_codes": sorted(scope["legacy_codes"]),
            },
            refs=[
                {
                    "q": q,
                    "grade_code": grade_code,
                    "major_code": major_code,
                    "class_code": class_code,
                    "include_non_active": include_non_active,
                    "enrollment_status": enrollment_status,
                }
            ],
            masked_fields=sorted(masked_fields),
            metrics={"count": len(items), "total": total},
        ),
    )
    await db.commit()
    return items, total


async def build_summary_admin(
    db: AsyncSession,
    student_id: int,
    *,
    viewer_user_id: int,
    viewer_role: str | None,
) -> ProfileSummary:
    student, facts, counts, user_names = await _load_admin_summary(
        db,
        student_id,
        viewer_user_id=viewer_user_id,
        viewer_role=viewer_role,
        denied_action="READ_ADMIN_DENIED",
    )
    grants = await _load_full_view_grants(
        db,
        student_id=student_id,
        requester_user_id=viewer_user_id,
    )
    student_basic, masked_fields = await _sanitize_student_basic_with_grants(
        db,
        roles=viewer_role,
        student=student,
        grants=grants,
    )
    summary = ProfileSummary(
        student=student_basic,
        facts=[_build_fact_admin_view(fact, user_names) for fact in facts],
        masked_fields=masked_fields,
        hidden_sensitive_fact_count=0,
        full_view_approved_fields=sorted(grants.student_fields),
        full_view_sensitive_facts_approved=grants.profile_facts,
        generated_at=datetime.now(UTC),
        **_summary_counters(counts),
    )
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="STUDENT_PROFILE",
        action="READ_ADMIN",
        entity_id=student_id,
        actor_user_id=viewer_user_id,
        actor_role=viewer_role,
        detail=build_audit_detail(
            target={"student_id": student_id},
            refs=[
                {
                    "full_view_fields": sorted(grants.student_fields),
                    "full_view_sensitive_facts": grants.profile_facts,
                }
            ],
            masked_fields=masked_fields,
            metrics={"fact_count": len(summary.facts)},
        ),
    )
    await db.commit()
    return summary


async def build_summary_self(
    db: AsyncSession,
    student_id: int,
    *,
    viewer_user_id: int,
    viewer_role: str | None,
) -> ProfileStudentSelfView:
    student = await repo.get_student(db, student_id)
    if student is None:
        raise NotFoundError("学生不存在")
    facts = await repo.list_facts(db, student_id, only_approved=True)
    grants = await _load_full_view_grants(
        db,
        student_id=student_id,
        requester_user_id=viewer_user_id,
    )
    visible = [fact for fact in facts if not fact.is_sensitive or grants.profile_facts]
    hidden_sensitive_fact_count = sum(1 for fact in facts if fact.is_sensitive)
    if grants.profile_facts:
        hidden_sensitive_fact_count = 0
    student_basic, masked_fields = await _sanitize_student_basic_with_grants(
        db,
        roles=viewer_role,
        student=student,
        grants=grants,
    )
    counts = await repo.count_by_type(db, student_id)
    out = ProfileStudentSelfView(
        student=student_basic,
        facts=[_build_fact_student_view(fact) for fact in visible],
        masked_fields=masked_fields,
        hidden_sensitive_fact_count=hidden_sensitive_fact_count,
        full_view_approved_fields=sorted(grants.student_fields),
        full_view_sensitive_facts_approved=grants.profile_facts,
        generated_at=datetime.now(UTC),
        **_summary_counters(counts),
    )
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="STUDENT_PROFILE",
        action="READ_SELF",
        entity_id=student_id,
        actor_user_id=viewer_user_id,
        actor_role=viewer_role,
        detail=build_audit_detail(
            target={"student_id": student_id},
            refs=[
                {
                    "full_view_fields": sorted(grants.student_fields),
                    "full_view_sensitive_facts": grants.profile_facts,
                }
            ],
            masked_fields=masked_fields,
            metrics={"fact_count": len(out.facts)},
        ),
    )
    await db.commit()
    return out


async def create_fact(
    db: AsyncSession,
    student_id: int,
    payload: dict[str, Any],
    *,
    operator_id: int,
    operator_role: str | None,
) -> ProfileFact:
    await _ensure_student_access(
        db,
        student_id,
        viewer_user_id=operator_id,
        viewer_role=operator_role,
        denied_action="CREATE_FACT_DENIED",
    )
    data = dict(payload)
    data["student_id"] = student_id
    data["created_by"] = operator_id
    data["updated_by"] = operator_id
    if data.get("source") == PROFILE_SOURCE_STUDENT_SELF:
        data["approval_status"] = PROFILE_APPROVAL_PENDING
    else:
        data["approval_status"] = PROFILE_APPROVAL_APPROVED
        data["approved_by"] = operator_id
        data["approved_at"] = datetime.now(UTC)
    row = await repo.create_fact(db, data)
    _set_review_comment(row, None)
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="PROFILE_FACT",
        action="CREATE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"student_id": student_id, "fact_type": row.fact_type},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def update_fact(
    db: AsyncSession,
    fact_id: int,
    payload: dict[str, Any],
    *,
    operator_id: int,
    operator_role: str | None,
) -> ProfileFact:
    row = await repo.get_fact(db, fact_id)
    if row is None:
        raise NotFoundError("画像条目不存在")
    await _ensure_student_access(
        db,
        row.student_id,
        viewer_user_id=operator_id,
        viewer_role=operator_role,
        denied_action="UPDATE_FACT_DENIED",
    )
    current_review_comment = _get_review_comment(row)
    for k, v in payload.items():
        if k in ("student_id", "created_by", "approved_by", "approved_at"):
            continue
        if k == "extra":
            next_extra = dict(v or {})
            if current_review_comment and "review_comment" not in next_extra:
                next_extra["review_comment"] = current_review_comment
            row.extra = next_extra or None
            continue
        setattr(row, k, v)
    row.updated_by = operator_id
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="PROFILE_FACT",
        action="UPDATE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_fact(
    db: AsyncSession,
    fact_id: int,
    *,
    operator_id: int,
    operator_role: str | None,
) -> None:
    row = await repo.get_fact(db, fact_id)
    if row is None:
        raise NotFoundError("画像条目不存在")
    await _ensure_student_access(
        db,
        row.student_id,
        viewer_user_id=operator_id,
        viewer_role=operator_role,
        denied_action="DELETE_FACT_DENIED",
    )
    await repo.delete_fact(db, row)
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="PROFILE_FACT",
        action="DELETE",
        entity_id=fact_id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"student_id": row.student_id},
    )
    await db.commit()


async def submit_correction(
    db: AsyncSession,
    student_id: int,
    payload: dict[str, Any],
    *,
    viewer_user_id: int,
) -> ProfileCorrection:
    data = dict(payload)
    data["student_id"] = student_id
    if data.get("fact_id"):
        fact = await repo.get_fact(db, data["fact_id"])
        if fact is None:
            raise NotFoundError("所引用的画像条目不存在")
        if fact.student_id != student_id:
            raise BizError("不允许修改他人画像", code=40180)
        data["current_value"] = str(getattr(fact, data["field_name"], "") or "")
    row = await repo.create_correction(db, data)
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="PROFILE_CORRECTION",
        action="SUBMIT",
        entity_id=row.id,
        actor_user_id=viewer_user_id,
        detail={"student_id": student_id, "field": data["field_name"]},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def list_corrections_admin(
    db: AsyncSession,
    *,
    student_id: int | None,
    status: str | None,
    page: int,
    size: int,
    viewer_user_id: int,
    viewer_role: str | None,
) -> tuple[list[ProfileCorrection], int]:
    if student_id is not None:
        await _ensure_student_access(
            db,
            student_id,
            viewer_user_id=viewer_user_id,
            viewer_role=viewer_role,
            denied_action="LIST_CORRECTION_DENIED",
        )
    scope = await _ensure_profile_scope_available(db, viewer_user_id=viewer_user_id)
    return await repo.list_corrections(
        db,
        student_id=student_id,
        status=status,
        class_scope_codes=scope["class_codes"],
        major_scope_codes=scope["major_codes"],
        legacy_scope_codes=scope["legacy_codes"],
        page=page,
        size=size,
    )


async def decide_correction(
    db: AsyncSession,
    correction_id: int,
    *,
    decision: str,
    comment: str | None,
    apply_to_fact: bool,
    operator_id: int,
    operator_role: str | None,
) -> ProfileCorrection:
    if decision not in (PROFILE_APPROVAL_APPROVED, PROFILE_APPROVAL_REJECTED):
        raise BizError(f"无效的处理结果 {decision}", code=40181)
    row = await repo.get_correction(db, correction_id)
    if row is None:
        raise NotFoundError("申诉记录不存在")
    await _ensure_student_access(
        db,
        row.student_id,
        viewer_user_id=operator_id,
        viewer_role=operator_role,
        denied_action="DECIDE_CORRECTION_DENIED",
    )
    if row.status != PROFILE_APPROVAL_PENDING:
        raise BizError("该申诉已处理", code=40182)

    row.status = decision
    row.handled_by = operator_id
    row.handled_at = datetime.now(UTC)
    row.handler_comment = comment

    if decision == PROFILE_APPROVAL_APPROVED and apply_to_fact and row.fact_id:
        fact = await repo.get_fact(db, row.fact_id)
        if fact is not None and fact.student_id == row.student_id and hasattr(fact, row.field_name):
            setattr(fact, row.field_name, row.proposed_value)
            fact.updated_by = operator_id

    await log_action(
        db,
        event_type="PROFILE",
        entity_code="PROFILE_CORRECTION",
        action="DECIDE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"decision": decision, "apply": apply_to_fact},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def submit_fact(
    db: AsyncSession,
    student_id: int,
    payload: dict[str, Any],
    *,
    viewer_user_id: int,
) -> ProfileFact:
    data = dict(payload)
    data["student_id"] = student_id
    data["source"] = PROFILE_SOURCE_STUDENT_SELF
    data["approval_status"] = PROFILE_APPROVAL_PENDING
    data["created_by"] = viewer_user_id
    data["updated_by"] = viewer_user_id
    data["approved_by"] = None
    data["approved_at"] = None
    data["is_sensitive"] = False
    row = await repo.create_fact(db, data)
    _set_review_comment(row, None)
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="PROFILE_FACT",
        action="SUBMIT",
        entity_id=row.id,
        actor_user_id=viewer_user_id,
        detail={"student_id": student_id, "fact_type": row.fact_type},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def list_my_fact_submissions(
    db: AsyncSession,
    *,
    student_id: int,
    page: int,
    size: int,
) -> tuple[list[ProfileFact], int]:
    return await repo.list_fact_submissions(
        db,
        student_id=student_id,
        page=page,
        size=size,
    )


async def submit_full_view_request(
    db: AsyncSession,
    student_id: int,
    payload: dict[str, Any],
    *,
    requester_user_id: int,
    requester_role: str | None,
    enforce_student_scope: bool = False,
) -> ProfileCorrection:
    if enforce_student_scope:
        await _ensure_student_access(
            db,
            student_id,
            viewer_user_id=requester_user_id,
            viewer_role=requester_role,
            denied_action="FULL_VIEW_REQUEST_DENIED",
        )
    elif await repo.get_student(db, student_id) is None:
        raise NotFoundError("学生不存在")

    encoded_field_name = _encode_full_view_field_name(
        str(payload.get("target_type") or ""),
        payload.get("field_name"),
    )
    existing = await repo.find_active_full_view_request(
        db,
        student_id=student_id,
        encoded_field_name=encoded_field_name,
        requester_user_id=requester_user_id,
    )
    if existing is not None:
        return existing

    row = await repo.create_correction(
        db,
        {
            "student_id": student_id,
            "field_name": encoded_field_name,
            "current_value": _full_view_requester_marker(requester_user_id),
            "proposed_value": None,
            "reason": payload.get("reason"),
            "status": PROFILE_APPROVAL_PENDING,
        },
    )
    target_type, field_name = _decode_full_view_field_name(encoded_field_name)
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="PROFILE_FULL_VIEW_REQUEST",
        action="FULL_VIEW_REQUEST_SUBMIT",
        entity_id=row.id,
        actor_user_id=requester_user_id,
        actor_role=requester_role,
        detail=build_audit_detail(
            target={"student_id": student_id},
            refs=[
                {
                    "target_type": target_type,
                    "field_name": field_name,
                    "requester_user_id": requester_user_id,
                }
            ],
            reason=payload.get("reason"),
        ),
    )
    await db.commit()
    await db.refresh(row)
    return row


async def list_full_view_requests_self(
    db: AsyncSession,
    *,
    student_id: int,
    requester_user_id: int,
    status: str | None,
    page: int,
    size: int,
) -> tuple[list[ProfileCorrection], int]:
    return await repo.list_full_view_requests(
        db,
        student_id=student_id,
        status=status,
        requester_user_id=requester_user_id,
        page=page,
        size=size,
    )


async def list_full_view_requests_admin(
    db: AsyncSession,
    *,
    student_id: int | None,
    status: str | None,
    page: int,
    size: int,
    viewer_user_id: int,
    viewer_role: str | None,
) -> tuple[list[ProfileCorrection], int]:
    if student_id is not None:
        await _ensure_student_access(
            db,
            student_id,
            viewer_user_id=viewer_user_id,
            viewer_role=viewer_role,
            denied_action="LIST_FULL_VIEW_REQUEST_DENIED",
        )
    scope = await _ensure_profile_scope_available(db, viewer_user_id=viewer_user_id)
    return await repo.list_full_view_requests(
        db,
        student_id=student_id,
        status=status,
        class_scope_codes=scope["class_codes"],
        major_scope_codes=scope["major_codes"],
        legacy_scope_codes=scope["legacy_codes"],
        page=page,
        size=size,
    )


async def decide_full_view_request(
    db: AsyncSession,
    request_id: int,
    *,
    decision: str,
    comment: str | None,
    operator_id: int,
    operator_role: str | None,
) -> ProfileCorrection:
    if decision not in (PROFILE_APPROVAL_APPROVED, PROFILE_APPROVAL_REJECTED):
        raise BizError(f"无效的处理结果 {decision}", code=40192)
    row = await repo.get_full_view_request(db, request_id)
    if row is None:
        raise NotFoundError("完整查看申请不存在")
    await _ensure_student_access(
        db,
        row.student_id,
        viewer_user_id=operator_id,
        viewer_role=operator_role,
        denied_action="DECIDE_FULL_VIEW_REQUEST_DENIED",
    )
    if row.status != PROFILE_APPROVAL_PENDING:
        raise BizError("该完整查看申请已处理", code=40193)

    row.status = decision
    row.handled_by = operator_id
    row.handled_at = datetime.now(UTC)
    row.handler_comment = comment

    target_type, field_name = _decode_full_view_field_name(row.field_name)
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="PROFILE_FULL_VIEW_REQUEST",
        action="FULL_VIEW_REQUEST_DECIDE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail=build_audit_detail(
            target={"student_id": row.student_id},
            refs=[
                {
                    "target_type": target_type,
                    "field_name": field_name,
                    "requester_user_id": _parse_full_view_requester_id(row),
                }
            ],
            changes={"decision": decision},
            reason=comment,
        ),
    )
    await db.commit()
    await db.refresh(row)
    return row


async def list_pending_facts_admin(
    db: AsyncSession,
    *,
    student_id: int | None,
    page: int,
    size: int,
    viewer_user_id: int,
    viewer_role: str | None,
) -> tuple[list[ProfileFact], int]:
    if student_id is not None:
        await _ensure_student_access(
            db,
            student_id,
            viewer_user_id=viewer_user_id,
            viewer_role=viewer_role,
            denied_action="LIST_PENDING_FACT_DENIED",
        )
    scope = await _ensure_profile_scope_available(db, viewer_user_id=viewer_user_id)
    return await repo.list_pending_facts(
        db,
        student_id=student_id,
        approval_statuses=[PROFILE_APPROVAL_PENDING],
        class_scope_codes=scope["class_codes"],
        major_scope_codes=scope["major_codes"],
        legacy_scope_codes=scope["legacy_codes"],
        page=page,
        size=size,
    )


async def decide_fact(
    db: AsyncSession,
    fact_id: int,
    *,
    decision: str,
    comment: str | None,
    operator_id: int,
    operator_role: str | None,
) -> ProfileFact:
    if decision not in (PROFILE_APPROVAL_APPROVED, PROFILE_APPROVAL_REJECTED):
        raise BizError(f"无效的处理结果 {decision}", code=40183)
    row = await repo.get_fact(db, fact_id)
    if row is None:
        raise NotFoundError("画像补录不存在")
    await _ensure_student_access(
        db,
        row.student_id,
        viewer_user_id=operator_id,
        viewer_role=operator_role,
        denied_action="DECIDE_FACT_DENIED",
    )
    if row.source != PROFILE_SOURCE_STUDENT_SELF:
        raise BizError("仅学生补录记录可走该审批动作", code=40184)
    if row.approval_status != PROFILE_APPROVAL_PENDING:
        raise BizError("该补录记录已处理", code=40185)

    row.approval_status = decision
    row.updated_by = operator_id
    if decision == PROFILE_APPROVAL_APPROVED:
        row.approved_by = operator_id
        row.approved_at = datetime.now(UTC)
    _set_review_comment(row, comment)

    await log_action(
        db,
        event_type="PROFILE",
        entity_code="PROFILE_FACT",
        action="DECIDE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"decision": decision, "student_id": row.student_id},
    )
    await db.commit()
    await db.refresh(row)
    return row


def _render_profile_snapshot_html(
    student: Student, summary: ProfileSummary
) -> str:
    e = html_escape.escape
    fact_rows = "".join(
        f"""
        <tr>
          <td>{e(fact.fact_type)}</td>
          <td>{e(fact.title)}</td>
          <td>{e(fact.source_label or "-")}</td>
          <td>{e(fact.updated_by_name or "-")}</td>
          <td>{fact.updated_at.strftime("%Y-%m-%d %H:%M")}</td>
        </tr>
        """
        for fact in summary.facts
    )
    if not fact_rows:
        fact_rows = '<tr><td colspan="5">暂无成长记录</td></tr>'
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"/><title>画像快照</title>
<style>
@page {{ size: A4; margin: 1.5cm; }}
body {{ font-family: "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; color: #222; }}
h1 {{ text-align: center; font-size: 20pt; margin-bottom: 20pt; }}
h2 {{ font-size: 13pt; margin: 16pt 0 8pt; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8pt 16pt; font-size: 11pt; }}
.metrics {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 8pt; margin: 12pt 0; }}
.metric {{ border: 1px solid #ddd; padding: 8pt; text-align: center; }}
table {{ width: 100%; border-collapse: collapse; font-size: 10pt; }}
th, td {{ border: 1px solid #ddd; padding: 6pt; text-align: left; vertical-align: top; }}
th {{ background: #f7f7f7; }}
</style></head>
<body>
<h1>学生画像快照</h1>
<div class="grid">
  <div><strong>学号：</strong>{e(student.student_no)}</div>
  <div><strong>姓名：</strong>{e(student.full_name)}</div>
  <div><strong>专业：</strong>{e(student.major_code or "-")}</div>
  <div><strong>班级：</strong>{e(student.class_code or "-")}</div>
  <div><strong>学籍状态：</strong>{e(student.enrollment_status)}</div>
  <div><strong>状态说明：</strong>{e(student.enrollment_status_reason or "-")}</div>
</div>
<div class="metrics">
  <div class="metric"><div>科研</div><strong>{summary.research_count}</strong></div>
  <div class="metric"><div>竞赛</div><strong>{summary.competition_count}</strong></div>
  <div class="metric"><div>实践</div><strong>{summary.practice_count}</strong></div>
  <div class="metric"><div>志愿时长</div><strong>{summary.volunteer_hours}</strong></div>
  <div class="metric"><div>学生骨干</div><strong>{summary.leadership_count}</strong></div>
</div>
<h2>成长记录</h2>
<table>
  <thead>
    <tr>
      <th>类型</th>
      <th>标题</th>
      <th>来源</th>
      <th>最近维护人</th>
      <th>更新时间</th>
    </tr>
  </thead>
  <tbody>{fact_rows}</tbody>
</table>
</body></html>"""


def _render_profile_snapshot_lines(
    student: Student, summary: ProfileSummary
) -> list[str]:
    lines = [
        "Student Profile Snapshot",
        f"Student No: {student.student_no}",
        f"Full Name: {student.full_name}",
        f"Major: {student.major_code or '-'}",
        f"Class: {student.class_code or '-'}",
        f"Enrollment Status: {student.enrollment_status}",
        f"Status Reason: {student.enrollment_status_reason or '-'}",
        (
            "Metrics: "
            f"research={summary.research_count}, "
            f"competition={summary.competition_count}, "
            f"practice={summary.practice_count}, "
            f"volunteer_hours={summary.volunteer_hours}, "
            f"leadership={summary.leadership_count}"
        ),
        "Facts:",
    ]
    if not summary.facts:
        lines.append("  - none")
        return lines
    for fact in summary.facts:
        lines.append(
            "  - "
            f"{fact.fact_type} | {fact.title} | "
            f"{fact.source_label or '-'} | "
            f"{fact.updated_by_name or '-'} | "
            f"{fact.updated_at.strftime('%Y-%m-%d %H:%M')}"
        )
    return lines


def _escape_pdf_text(text: str) -> str:
    return (
        text.encode("latin-1", "replace")
        .decode("latin-1")
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _fallback_pdf_bytes(lines: list[str]) -> bytes:
    left = 48
    top = 792
    line_height = 15
    sanitized = [_escape_pdf_text(line) for line in lines]
    content_lines = ["BT", "/F1 11 Tf", f"{left} {top} Td", f"{line_height} TL"]
    for index, line in enumerate(sanitized):
        if index:
            content_lines.append("T*")
        content_lines.append(f"({line}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 4 0 R >> >> "
            b"/Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    startxref = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        (
            f"trailer << /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{startxref}\n%%EOF"
        ).encode("latin-1")
    )
    return bytes(pdf)


def _html_to_pdf_bytes(html: str, *, fallback_lines: list[str] | None = None) -> bytes:
    try:
        from weasyprint import HTML  # type: ignore
    except Exception as exc:  # noqa: BLE001
        if fallback_lines is not None:
            return _fallback_pdf_bytes(fallback_lines)
        raise BizError(
            "PDF 生成依赖未就绪（weasyprint + GTK 运行时），请联系运维",
            code=50003,
            http_status=500,
        ) from exc
    buf = io.BytesIO()
    HTML(string=html).write_pdf(buf)
    return buf.getvalue()


async def generate_snapshot_pdf(
    db: AsyncSession,
    student_id: int,
    *,
    viewer_user_id: int,
    viewer_role: str | None,
) -> tuple[bytes, str]:
    await _ensure_student_access(
        db,
        student_id,
        viewer_user_id=viewer_user_id,
        viewer_role=viewer_role,
        denied_action="EXPORT_SNAPSHOT_DENIED",
        denied_detail=build_audit_detail(
            target={"student_id": student_id, "format": "pdf"},
        ),
    )
    await ensure_export_permission(
        db,
        roles=viewer_role,
        export_code=EXPORT_PROFILE_SNAPSHOT_DETAIL,
        actor_user_id=viewer_user_id,
        actor_role=viewer_role,
        event_type="PROFILE",
        entity_code="STUDENT_PROFILE_SNAPSHOT",
        action="EXPORT_SNAPSHOT_DENIED",
        entity_id=student_id,
        message="当前角色无权导出画像 PDF 快照",
        detail=build_audit_detail(
            target={"student_id": student_id, "format": "pdf"},
        ),
    )
    student, facts, counts, user_names = await _load_admin_summary(
        db,
        student_id,
        viewer_user_id=viewer_user_id,
        viewer_role=viewer_role,
        denied_action="EXPORT_SNAPSHOT_DENIED",
    )
    summary = ProfileSummary(
        student=_build_student_basic(student),
        facts=[_build_fact_admin_view(fact, user_names) for fact in facts],
        generated_at=datetime.now(UTC),
        **_summary_counters(counts),
    )
    pdf_bytes = _html_to_pdf_bytes(
        _render_profile_snapshot_html(student, summary),
        fallback_lines=_render_profile_snapshot_lines(student, summary),
    )
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="STUDENT_PROFILE_SNAPSHOT",
        action="EXPORT_PDF",
        entity_id=student_id,
        actor_user_id=viewer_user_id,
        actor_role=viewer_role,
        detail=build_audit_detail(
            target={"student_id": student_id, "format": "pdf"},
            metrics={"fact_count": len(summary.facts)},
        ),
    )
    await db.commit()
    return pdf_bytes, f"profile-snapshot-{student.student_no}.pdf"


async def generate_snapshot_xlsx(
    db: AsyncSession,
    student_id: int,
    *,
    viewer_user_id: int,
    viewer_role: str | None,
) -> tuple[bytes, str]:
    await _ensure_student_access(
        db,
        student_id,
        viewer_user_id=viewer_user_id,
        viewer_role=viewer_role,
        denied_action="EXPORT_SNAPSHOT_DENIED",
        denied_detail=build_audit_detail(
            target={"student_id": student_id, "format": "xlsx"},
        ),
    )
    await ensure_export_permission(
        db,
        roles=viewer_role,
        export_code=EXPORT_PROFILE_SNAPSHOT_DETAIL,
        actor_user_id=viewer_user_id,
        actor_role=viewer_role,
        event_type="PROFILE",
        entity_code="STUDENT_PROFILE_SNAPSHOT",
        action="EXPORT_SNAPSHOT_DENIED",
        entity_id=student_id,
        message="当前角色无权导出画像 XLSX 快照",
        detail=build_audit_detail(
            target={"student_id": student_id, "format": "xlsx"},
        ),
    )
    student, facts, _counts, user_names = await _load_admin_summary(
        db,
        student_id,
        viewer_user_id=viewer_user_id,
        viewer_role=viewer_role,
        denied_action="EXPORT_SNAPSHOT_DENIED",
    )
    from app.exchange.service import export_workbook

    headers = [
        "student_no",
        "full_name",
        "fact_type",
        "title",
        "description",
        "source",
        "approval_status",
        "updated_by_name",
        "updated_at",
        "review_comment",
    ]
    rows = [
        [
            student.student_no,
            student.full_name,
            fact.fact_type,
            fact.title,
            fact.description,
            _get_source_label(fact.source),
            fact.approval_status,
            user_names.get(fact.updated_by or 0),
            fact.updated_at,
            _get_review_comment(fact),
        ]
        for fact in facts
    ]
    data = export_workbook(headers, rows, sheet_name="profile_snapshot")
    await log_action(
        db,
        event_type="PROFILE",
        entity_code="STUDENT_PROFILE_SNAPSHOT",
        action="EXPORT_XLSX",
        entity_id=student_id,
        actor_user_id=viewer_user_id,
        actor_role=viewer_role,
        detail=build_audit_detail(
            target={"student_id": student_id, "format": "xlsx"},
            metrics={"fact_count": len(facts)},
        ),
    )
    await db.commit()
    return data, f"profile-snapshot-{student.student_no}.xlsx"
