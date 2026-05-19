"""profile 模块 repository — FR-018。"""
from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import ENROLLMENT_ACTIVE, Student
from app.core.sql import order_by_nulls_last_desc
from app.profile.models import (
    PROFILE_APPROVAL_APPROVED,
    PROFILE_APPROVAL_PENDING,
    PROFILE_FACT_VOLUNTEER,
    PROFILE_FULL_VIEW_FIELD_PREFIX,
    PROFILE_FULL_VIEW_MARKER_PREFIX,
    PROFILE_SOURCE_STUDENT_SELF,
    ProfileCorrection,
    ProfileFact,
)


def _apply_student_scope(
    stmt,
    *,
    class_codes: set[str] | None = None,
    major_codes: set[str] | None = None,
    grade_codes: set[str] | None = None,
    legacy_codes: set[str] | None = None,
):
    scope_conds = []
    if class_codes:
        scope_conds.append(Student.class_code.in_(sorted(class_codes)))
    if major_codes:
        scope_conds.append(Student.major_code.in_(sorted(major_codes)))
    if grade_codes:
        scope_conds.append(Student.grade_code.in_(sorted(grade_codes)))
    if legacy_codes:
        codes = sorted(legacy_codes)
        scope_conds.append(Student.class_code.in_(codes))
        scope_conds.append(Student.major_code.in_(codes))
        scope_conds.append(Student.grade_code.in_(codes))
    if scope_conds:
        stmt = stmt.where(or_(*scope_conds))
    return stmt


def full_view_requester_marker(requester_user_id: int) -> str:
    return f"{PROFILE_FULL_VIEW_MARKER_PREFIX}{requester_user_id}"


def _full_view_request_condition():
    return ProfileCorrection.field_name.like(f"{PROFILE_FULL_VIEW_FIELD_PREFIX}%")


def _normal_correction_condition():
    return ProfileCorrection.field_name.not_like(f"{PROFILE_FULL_VIEW_FIELD_PREFIX}%")


async def get_student(db: AsyncSession, student_id: int) -> Student | None:
    stmt = select(Student).where(Student.id == student_id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def search_students(
    db: AsyncSession,
    *,
    q: str | None,
    grade_code: str | None,
    major_code: str | None,
    class_code: str | None,
    class_scope_codes: set[str] | None = None,
    major_scope_codes: set[str] | None = None,
    grade_scope_codes: set[str] | None = None,
    legacy_scope_codes: set[str] | None = None,
    include_non_active: bool = False,
    enrollment_status: str | None = None,
    page: int,
    size: int,
) -> tuple[list[Student], int]:
    stmt = select(Student).where(Student.deleted_at.is_(None))
    stmt = _apply_student_scope(
        stmt,
        class_codes=class_scope_codes,
        major_codes=major_scope_codes,
        grade_codes=grade_scope_codes,
        legacy_codes=legacy_scope_codes,
    )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (Student.student_no.ilike(like)) | (Student.full_name.ilike(like))
        )
    if grade_code:
        stmt = stmt.where(Student.grade_code == grade_code)
    if major_code:
        stmt = stmt.where(Student.major_code == major_code)
    if class_code:
        stmt = stmt.where(Student.class_code == class_code)
    if enrollment_status:
        stmt = stmt.where(Student.enrollment_status == enrollment_status)
    elif not include_non_active:
        stmt = stmt.where(Student.enrollment_status == ENROLLMENT_ACTIVE)
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    stmt = stmt.order_by(Student.student_no.asc()).offset((page - 1) * size).limit(size)
    return list((await db.execute(stmt)).scalars().all()), total


async def list_facts(
    db: AsyncSession,
    student_id: int,
    *,
    only_approved: bool = True,
    source: str | None = None,
    approval_statuses: list[str] | None = None,
) -> list[ProfileFact]:
    stmt = select(ProfileFact).where(ProfileFact.student_id == student_id)
    if only_approved:
        stmt = stmt.where(ProfileFact.approval_status == PROFILE_APPROVAL_APPROVED)
    elif approval_statuses:
        stmt = stmt.where(ProfileFact.approval_status.in_(approval_statuses))
    if source:
        stmt = stmt.where(ProfileFact.source == source)
    stmt = stmt.order_by(
        ProfileFact.fact_type.asc(),
        *order_by_nulls_last_desc(ProfileFact.started_on),
        ProfileFact.id.desc(),
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_fact_submissions(
    db: AsyncSession,
    *,
    student_id: int,
    page: int,
    size: int,
) -> tuple[list[ProfileFact], int]:
    stmt = select(ProfileFact).where(
        ProfileFact.student_id == student_id,
        ProfileFact.source == PROFILE_SOURCE_STUDENT_SELF,
    )
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    stmt = (
        stmt.order_by(ProfileFact.updated_at.desc(), ProfileFact.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list((await db.execute(stmt)).scalars().all()), total


async def list_pending_facts(
    db: AsyncSession,
    *,
    student_id: int | None,
    approval_statuses: list[str],
    class_scope_codes: set[str] | None = None,
    major_scope_codes: set[str] | None = None,
    grade_scope_codes: set[str] | None = None,
    legacy_scope_codes: set[str] | None = None,
    page: int,
    size: int,
) -> tuple[list[ProfileFact], int]:
    stmt = (
        select(ProfileFact)
        .join(Student, Student.id == ProfileFact.student_id)
        .where(ProfileFact.source == PROFILE_SOURCE_STUDENT_SELF)
        .where(ProfileFact.approval_status.in_(approval_statuses))
    )
    stmt = _apply_student_scope(
        stmt,
        class_codes=class_scope_codes,
        major_codes=major_scope_codes,
        grade_codes=grade_scope_codes,
        legacy_codes=legacy_scope_codes,
    )
    if student_id is not None:
        stmt = stmt.where(ProfileFact.student_id == student_id)
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    stmt = (
        stmt.order_by(ProfileFact.updated_at.desc(), ProfileFact.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list((await db.execute(stmt)).scalars().all()), total


async def create_fact(db: AsyncSession, payload: dict[str, Any]) -> ProfileFact:
    row = ProfileFact(**payload)
    db.add(row)
    await db.flush()
    return row


async def get_fact(db: AsyncSession, fact_id: int) -> ProfileFact | None:
    return (
        await db.execute(select(ProfileFact).where(ProfileFact.id == fact_id))
    ).scalar_one_or_none()


async def delete_fact(db: AsyncSession, fact: ProfileFact) -> None:
    await db.delete(fact)


async def count_by_type(db: AsyncSession, student_id: int) -> dict[str, float]:
    rows = (
        await db.execute(
            select(
                ProfileFact.fact_type,
                func.count(),
                func.coalesce(func.sum(ProfileFact.hours), 0),
            )
            .where(
                ProfileFact.student_id == student_id,
                ProfileFact.approval_status == PROFILE_APPROVAL_APPROVED,
            )
            .group_by(ProfileFact.fact_type)
        )
    ).all()
    out: dict[str, float] = {}
    for fact_type, count, hours in rows:
        out[fact_type] = float(count)
        if fact_type == PROFILE_FACT_VOLUNTEER:
            out["VOLUNTEER_HOURS"] = float(hours or 0)
    return out


async def create_correction(
    db: AsyncSession, payload: dict[str, Any]
) -> ProfileCorrection:
    row = ProfileCorrection(**payload)
    db.add(row)
    await db.flush()
    return row


async def list_corrections(
    db: AsyncSession,
    *,
    student_id: int | None,
    status: str | None,
    class_scope_codes: set[str] | None = None,
    major_scope_codes: set[str] | None = None,
    grade_scope_codes: set[str] | None = None,
    legacy_scope_codes: set[str] | None = None,
    page: int,
    size: int,
) -> tuple[list[ProfileCorrection], int]:
    stmt = select(ProfileCorrection).where(_normal_correction_condition())
    if class_scope_codes or major_scope_codes or grade_scope_codes or legacy_scope_codes:
        stmt = stmt.join(Student, Student.id == ProfileCorrection.student_id)
        stmt = _apply_student_scope(
            stmt,
            class_codes=class_scope_codes,
            major_codes=major_scope_codes,
            grade_codes=grade_scope_codes,
            legacy_codes=legacy_scope_codes,
        )
    conds = []
    if student_id is not None:
        conds.append(ProfileCorrection.student_id == student_id)
    if status:
        conds.append(ProfileCorrection.status == status)
    if conds:
        stmt = stmt.where(and_(*conds))
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    stmt = stmt.order_by(ProfileCorrection.id.desc()).offset((page - 1) * size).limit(size)
    return list((await db.execute(stmt)).scalars().all()), total


async def get_correction(
    db: AsyncSession, correction_id: int
) -> ProfileCorrection | None:
    return (
        await db.execute(
            select(ProfileCorrection).where(ProfileCorrection.id == correction_id)
        )
    ).scalar_one_or_none()


async def find_active_full_view_request(
    db: AsyncSession,
    *,
    student_id: int,
    encoded_field_name: str,
    requester_user_id: int,
) -> ProfileCorrection | None:
    marker = full_view_requester_marker(requester_user_id)
    stmt = (
        select(ProfileCorrection)
        .where(
            _full_view_request_condition(),
            ProfileCorrection.student_id == student_id,
            ProfileCorrection.field_name == encoded_field_name,
            ProfileCorrection.current_value == marker,
            ProfileCorrection.status.in_(
                [PROFILE_APPROVAL_PENDING, PROFILE_APPROVAL_APPROVED]
            ),
        )
        .order_by(ProfileCorrection.id.desc())
    )
    return (await db.execute(stmt)).scalars().first()


async def get_full_view_request(
    db: AsyncSession,
    request_id: int,
) -> ProfileCorrection | None:
    return (
        await db.execute(
            select(ProfileCorrection).where(
                ProfileCorrection.id == request_id,
                _full_view_request_condition(),
            )
        )
    ).scalar_one_or_none()


async def list_full_view_requests(
    db: AsyncSession,
    *,
    student_id: int | None = None,
    status: str | None = None,
    requester_user_id: int | None = None,
    class_scope_codes: set[str] | None = None,
    major_scope_codes: set[str] | None = None,
    grade_scope_codes: set[str] | None = None,
    legacy_scope_codes: set[str] | None = None,
    page: int,
    size: int,
) -> tuple[list[ProfileCorrection], int]:
    stmt = select(ProfileCorrection).where(_full_view_request_condition())
    if class_scope_codes or major_scope_codes or grade_scope_codes or legacy_scope_codes:
        stmt = stmt.join(Student, Student.id == ProfileCorrection.student_id)
        stmt = _apply_student_scope(
            stmt,
            class_codes=class_scope_codes,
            major_codes=major_scope_codes,
            grade_codes=grade_scope_codes,
            legacy_codes=legacy_scope_codes,
        )
    conds = []
    if student_id is not None:
        conds.append(ProfileCorrection.student_id == student_id)
    if status:
        conds.append(ProfileCorrection.status == status)
    if requester_user_id is not None:
        conds.append(
            ProfileCorrection.current_value
            == full_view_requester_marker(requester_user_id)
        )
    if conds:
        stmt = stmt.where(and_(*conds))
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    stmt = (
        stmt.order_by(ProfileCorrection.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list((await db.execute(stmt)).scalars().all()), total


async def list_approved_full_view_requests(
    db: AsyncSession,
    *,
    student_id: int,
    requester_user_id: int,
) -> list[ProfileCorrection]:
    stmt = select(ProfileCorrection).where(
        _full_view_request_condition(),
        ProfileCorrection.student_id == student_id,
        ProfileCorrection.current_value == full_view_requester_marker(requester_user_id),
        ProfileCorrection.status == PROFILE_APPROVAL_APPROVED,
    )
    return list((await db.execute(stmt)).scalars().all())
