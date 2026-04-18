"""profile 模块 repository — FR-018。"""
from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student
from app.profile.models import (
    PROFILE_APPROVAL_APPROVED,
    PROFILE_FACT_COMPETITION,
    PROFILE_FACT_LEADERSHIP,
    PROFILE_FACT_PRACTICE,
    PROFILE_FACT_RESEARCH,
    PROFILE_FACT_VOLUNTEER,
    ProfileCorrection,
    ProfileFact,
)


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
    page: int,
    size: int,
) -> tuple[list[Student], int]:
    stmt = select(Student).where(Student.deleted_at.is_(None))
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
    total = (await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar_one()
    stmt = stmt.order_by(Student.student_no.asc()).offset((page - 1) * size).limit(size)
    return list((await db.execute(stmt)).scalars().all()), total


async def list_facts(
    db: AsyncSession,
    student_id: int,
    *,
    only_approved: bool = True,
) -> list[ProfileFact]:
    stmt = select(ProfileFact).where(ProfileFact.student_id == student_id)
    if only_approved:
        stmt = stmt.where(ProfileFact.approval_status == PROFILE_APPROVAL_APPROVED)
    stmt = stmt.order_by(
        ProfileFact.fact_type.asc(),
        ProfileFact.started_on.desc().nullslast(),
        ProfileFact.id.desc(),
    )
    return list((await db.execute(stmt)).scalars().all())


async def create_fact(db: AsyncSession, payload: dict[str, Any]) -> ProfileFact:
    row = ProfileFact(**payload)
    db.add(row)
    await db.flush()
    return row


async def get_fact(db: AsyncSession, fact_id: int) -> ProfileFact | None:
    return (await db.execute(
        select(ProfileFact).where(ProfileFact.id == fact_id)
    )).scalar_one_or_none()


async def delete_fact(db: AsyncSession, fact: ProfileFact) -> None:
    await db.delete(fact)


async def count_by_type(
    db: AsyncSession, student_id: int
) -> dict[str, float]:
    """返回 { 'RESEARCH': n, 'COMPETITION': n, ..., 'VOLUNTEER_HOURS': sum_hours }"""
    rows = (await db.execute(
        select(ProfileFact.fact_type, func.count(), func.coalesce(func.sum(ProfileFact.hours), 0))
        .where(
            ProfileFact.student_id == student_id,
            ProfileFact.approval_status == PROFILE_APPROVAL_APPROVED,
        )
        .group_by(ProfileFact.fact_type)
    )).all()
    out: dict[str, float] = {}
    for t, c, h in rows:
        out[t] = float(c)
        if t == PROFILE_FACT_VOLUNTEER:
            out["VOLUNTEER_HOURS"] = float(h or 0)
    return out


# ---- 纠错申诉 ----
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
    page: int,
    size: int,
) -> tuple[list[ProfileCorrection], int]:
    stmt = select(ProfileCorrection)
    conds = []
    if student_id is not None:
        conds.append(ProfileCorrection.student_id == student_id)
    if status:
        conds.append(ProfileCorrection.status == status)
    if conds:
        stmt = stmt.where(and_(*conds))
    total = (await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar_one()
    stmt = stmt.order_by(ProfileCorrection.id.desc()).offset((page - 1) * size).limit(size)
    return list((await db.execute(stmt)).scalars().all()), total


async def get_correction(
    db: AsyncSession, correction_id: int
) -> ProfileCorrection | None:
    return (await db.execute(
        select(ProfileCorrection).where(ProfileCorrection.id == correction_id)
    )).scalar_one_or_none()
