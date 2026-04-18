"""exchange 模块数据库操作 — FR-009 / FR-015。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import Student
from app.exchange.models import (
    BATCH_STATUS_COMMITTED,
    BATCH_STATUS_ROLLED_BACK,
    BATCH_STATUS_VALIDATED,
    CourseEquivalence,
    CourseOffering,
    CurriculumModule,
    CurriculumPlan,
    ImportBatch,
    ImportBatchRow,
    StudentCourseRecord,
)


# ============================================================
# 导入批次
# ============================================================
async def create_batch(
    db: AsyncSession,
    *,
    batch_no: str,
    import_type: str,
    filename: str,
    object_bucket: str | None = None,
    object_key: str | None = None,
    file_size: int | None = None,
    mime_type: str | None = None,
    operator_id: int | None = None,
    operator_role: str | None = None,
) -> ImportBatch:
    row = ImportBatch(
        batch_no=batch_no,
        import_type=import_type,
        filename=filename,
        object_bucket=object_bucket,
        object_key=object_key,
        file_size=file_size,
        mime_type=mime_type,
        operator_id=operator_id,
        operator_role=operator_role,
    )
    db.add(row)
    await db.flush()
    return row


async def add_batch_row(
    db: AsyncSession,
    *,
    batch_id: int,
    row_no: int,
    severity: str,
    result: str,
    field_name: str | None = None,
    message: str | None = None,
    raw_data: dict[str, Any] | None = None,
) -> ImportBatchRow:
    r = ImportBatchRow(
        batch_id=batch_id,
        row_no=row_no,
        severity=severity,
        result=result,
        field_name=field_name,
        message=message,
        raw_data=raw_data,
    )
    db.add(r)
    return r


async def get_batch(db: AsyncSession, batch_id: int) -> ImportBatch | None:
    res = await db.execute(
        select(ImportBatch)
        .where(ImportBatch.id == batch_id)
        .options(selectinload(ImportBatch.rows))
    )
    return res.scalar_one_or_none()


async def list_batches(
    db: AsyncSession,
    *,
    import_type: str | None = None,
    status: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[ImportBatch], int]:
    stmt = select(ImportBatch)
    conds = []
    if import_type:
        conds.append(ImportBatch.import_type == import_type)
    if status:
        conds.append(ImportBatch.status == status)
    if conds:
        stmt = stmt.where(and_(*conds))
    total_res = await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )
    total = total_res.scalar_one()
    stmt = (
        stmt.order_by(ImportBatch.id.desc())
        .offset((page - 1) * size).limit(size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), total


async def list_batch_rows(
    db: AsyncSession,
    batch_id: int,
    *,
    severity: str | None = None,
    limit: int = 200,
) -> list[ImportBatchRow]:
    stmt = select(ImportBatchRow).where(ImportBatchRow.batch_id == batch_id)
    if severity:
        stmt = stmt.where(ImportBatchRow.severity == severity)
    stmt = stmt.order_by(ImportBatchRow.row_no.asc()).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def finalize_batch(
    db: AsyncSession,
    batch: ImportBatch,
    *,
    status: str,
    total_rows: int,
    ok_rows: int,
    warn_rows: int,
    fatal_rows: int,
    summary: dict[str, Any] | None = None,
    note: str | None = None,
) -> ImportBatch:
    batch.status = status
    batch.total_rows = total_rows
    batch.ok_rows = ok_rows
    batch.warn_rows = warn_rows
    batch.fatal_rows = fatal_rows
    batch.summary = summary
    if note is not None:
        batch.note = note
    batch.finished_at = datetime.now(timezone.utc)
    return batch


async def mark_batch_committed(db: AsyncSession, batch: ImportBatch) -> None:
    batch.status = BATCH_STATUS_COMMITTED
    batch.finished_at = datetime.now(timezone.utc)


async def mark_batch_rolled_back(db: AsyncSession, batch: ImportBatch) -> None:
    batch.status = BATCH_STATUS_ROLLED_BACK
    batch.finished_at = datetime.now(timezone.utc)


# ============================================================
# 学生 upsert（供 STUDENT 导入）
# ============================================================
async def upsert_student(
    db: AsyncSession, payload: dict[str, Any]
) -> tuple[Student, bool]:
    """按 student_no upsert；返回 (对象, 是否新建)。"""
    stmt = select(Student).where(Student.student_no == payload["student_no"])
    row = (await db.execute(stmt)).scalar_one_or_none()
    created = False
    if row is None:
        row = Student(**payload)
        db.add(row)
        created = True
    else:
        for k, v in payload.items():
            setattr(row, k, v)
    await db.flush()
    return row, created


# ============================================================
# 成绩 upsert
# ============================================================
async def upsert_student_course_record(
    db: AsyncSession, payload: dict[str, Any]
) -> StudentCourseRecord:
    stmt = select(StudentCourseRecord).where(
        StudentCourseRecord.student_id == payload["student_id"],
        StudentCourseRecord.course_code == payload["course_code"],
        StudentCourseRecord.term_code == payload.get("term_code"),
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        row = StudentCourseRecord(**payload)
        db.add(row)
    else:
        for k, v in payload.items():
            setattr(row, k, v)
    return row


async def get_student_by_no(db: AsyncSession, student_no: str) -> Student | None:
    stmt = select(Student).where(Student.student_no == student_no)
    return (await db.execute(stmt)).scalar_one_or_none()


# ============================================================
# 培养方案
# ============================================================
async def create_or_update_plan(
    db: AsyncSession, payload: dict[str, Any]
) -> CurriculumPlan:
    stmt = select(CurriculumPlan).where(
        CurriculumPlan.grade_code == payload["grade_code"],
        CurriculumPlan.major_code == payload["major_code"],
        CurriculumPlan.version_label == payload.get("version_label"),
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        row = CurriculumPlan(**payload)
        db.add(row)
        await db.flush()
    else:
        for k, v in payload.items():
            setattr(row, k, v)
        await db.flush()
    return row


async def get_plan(db: AsyncSession, plan_id: int) -> CurriculumPlan | None:
    stmt = (
        select(CurriculumPlan)
        .where(CurriculumPlan.id == plan_id)
        .options(selectinload(CurriculumPlan.modules))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_plans(
    db: AsyncSession,
    *,
    grade_code: str | None = None,
    major_code: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[CurriculumPlan], int]:
    stmt = select(CurriculumPlan)
    conds = []
    if grade_code:
        conds.append(CurriculumPlan.grade_code == grade_code)
    if major_code:
        conds.append(CurriculumPlan.major_code == major_code)
    if is_active is not None:
        conds.append(CurriculumPlan.is_active == is_active)
    if conds:
        stmt = stmt.where(and_(*conds))
    total = (await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar_one()
    stmt = (
        stmt.order_by(CurriculumPlan.grade_code.desc(), CurriculumPlan.major_code.asc())
        .offset((page - 1) * size).limit(size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), total


async def delete_plan(db: AsyncSession, plan: CurriculumPlan) -> None:
    await db.delete(plan)


async def set_plan_modules(
    db: AsyncSession, plan_id: int, modules: list[dict[str, Any]]
) -> list[CurriculumModule]:
    # 简单策略：清空再写入
    existing = (await db.execute(
        select(CurriculumModule).where(CurriculumModule.plan_id == plan_id)
    )).scalars().all()
    for m in existing:
        await db.delete(m)
    created: list[CurriculumModule] = []
    for m in modules:
        row = CurriculumModule(plan_id=plan_id, **m)
        db.add(row)
        created.append(row)
    await db.flush()
    return created


async def list_modules_by_plan(
    db: AsyncSession, plan_id: int
) -> list[CurriculumModule]:
    stmt = (
        select(CurriculumModule)
        .where(CurriculumModule.plan_id == plan_id)
        .order_by(CurriculumModule.sort_order.asc(), CurriculumModule.id.asc())
    )
    return list((await db.execute(stmt)).scalars().all())


# ============================================================
# 课程等价
# ============================================================
async def upsert_equivalence(
    db: AsyncSession, payload: dict[str, Any]
) -> CourseEquivalence:
    stmt = select(CourseEquivalence).where(
        CourseEquivalence.source_course_code == payload["source_course_code"],
        CourseEquivalence.target_course_code == payload["target_course_code"],
        CourseEquivalence.grade_code == payload.get("grade_code"),
        CourseEquivalence.major_code == payload.get("major_code"),
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        row = CourseEquivalence(**payload)
        db.add(row)
    else:
        for k, v in payload.items():
            setattr(row, k, v)
    return row


async def list_equivalences(
    db: AsyncSession,
    *,
    grade_code: str | None = None,
    major_code: str | None = None,
    source_code: str | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list[CourseEquivalence], int]:
    stmt = select(CourseEquivalence).where(CourseEquivalence.is_active.is_(True))
    if grade_code:
        stmt = stmt.where(CourseEquivalence.grade_code == grade_code)
    if major_code:
        stmt = stmt.where(CourseEquivalence.major_code == major_code)
    if source_code:
        stmt = stmt.where(CourseEquivalence.source_course_code == source_code)
    total = (await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar_one()
    stmt = stmt.order_by(CourseEquivalence.id.desc()).offset((page - 1) * size).limit(size)
    return list((await db.execute(stmt)).scalars().all()), total


# ============================================================
# 开课
# ============================================================
async def upsert_course_offering(
    db: AsyncSession, payload: dict[str, Any]
) -> CourseOffering:
    stmt = select(CourseOffering).where(
        CourseOffering.term_code == payload["term_code"],
        CourseOffering.course_code == payload["course_code"],
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        row = CourseOffering(**payload)
        db.add(row)
    else:
        for k, v in payload.items():
            setattr(row, k, v)
    return row


async def list_course_offerings(
    db: AsyncSession,
    *,
    term_code: str | None = None,
    course_code: str | None = None,
    major_code: str | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list[CourseOffering], int]:
    stmt = select(CourseOffering).where(CourseOffering.is_active.is_(True))
    if term_code:
        stmt = stmt.where(CourseOffering.term_code == term_code)
    if course_code:
        stmt = stmt.where(CourseOffering.course_code == course_code)
    if major_code:
        # 简单 LIKE 匹配，符合"以逗号分隔"的表示
        stmt = stmt.where(CourseOffering.major_codes.ilike(f"%{major_code}%"))
    total = (await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar_one()
    stmt = stmt.order_by(CourseOffering.term_code.desc(), CourseOffering.course_code.asc()) \
        .offset((page - 1) * size).limit(size)
    return list((await db.execute(stmt)).scalars().all()), total


# ============================================================
# 学生选课 / 成绩（导出）
# ============================================================
async def list_student_records(
    db: AsyncSession,
    *,
    student_id: int | None = None,
    student_no: str | None = None,
    term_code: str | None = None,
    page: int = 1,
    size: int = 100,
) -> tuple[list[StudentCourseRecord], int]:
    stmt = select(StudentCourseRecord)
    if student_id:
        stmt = stmt.where(StudentCourseRecord.student_id == student_id)
    if student_no:
        sub = select(Student.id).where(Student.student_no == student_no)
        stmt = stmt.where(StudentCourseRecord.student_id.in_(sub))
    if term_code:
        stmt = stmt.where(StudentCourseRecord.term_code == term_code)
    total = (await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar_one()
    stmt = stmt.order_by(StudentCourseRecord.term_code.desc().nullslast(),
                         StudentCourseRecord.course_code.asc()) \
        .offset((page - 1) * size).limit(size)
    return list((await db.execute(stmt)).scalars().all()), total


async def list_all_students(
    db: AsyncSession,
    *,
    grade_code: str | None = None,
    major_code: str | None = None,
    limit: int = 5000,
) -> list[Student]:
    stmt = select(Student).where(Student.deleted_at.is_(None))
    if grade_code:
        stmt = stmt.where(Student.grade_code == grade_code)
    if major_code:
        stmt = stmt.where(Student.major_code == major_code)
    stmt = stmt.order_by(Student.student_no.asc()).limit(limit)
    return list((await db.execute(stmt)).scalars().all())
