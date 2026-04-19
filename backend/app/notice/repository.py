"""notice 模块仓储层。"""
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student, User
from app.notice.models import (
    DELIVERY_STATUS_READ,
    NOTICE_STATUS_PUBLISHED,
    Notice,
    NoticeDelivery,
    NoticeDeliveryBatch,
    NoticeTag,
)


# ---------- Notice ----------
async def get_notice(db: AsyncSession, notice_id: int) -> Notice | None:
    return await db.get(Notice, notice_id)


async def create_notice(db: AsyncSession, **fields) -> Notice:
    row = Notice(**fields)
    db.add(row)
    await db.flush()
    return row


async def list_notices_admin(
    db: AsyncSession,
    *,
    q: str | None = None,
    status: str | None = None,
    category: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[Sequence[Notice], int]:
    stmt = select(Notice)
    conds = []
    if status:
        conds.append(Notice.status == status)
    if category:
        conds.append(Notice.category == category)
    if q:
        like = f"%{q}%"
        conds.append(or_(Notice.title.ilike(like), Notice.summary.ilike(like)))
    if conds:
        stmt = stmt.where(and_(*conds))
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(Notice.is_pinned.desc(), Notice.published_at.desc().nullslast(),
                        Notice.updated_at.desc()).offset((page - 1) * size).limit(size)
    rows = (await db.execute(stmt)).scalars().unique().all()
    return rows, total


async def set_notice_tags(db: AsyncSession, notice_id: int, tags: list[str]) -> None:
    existing = (
        await db.execute(select(NoticeTag).where(NoticeTag.notice_id == notice_id))
    ).scalars().all()
    for row in existing:
        await db.delete(row)
    for tag in {t.strip() for t in tags if t and t.strip()}:
        db.add(NoticeTag(notice_id=notice_id, tag=tag))
    await db.flush()


# ---------- Target resolution ----------
async def resolve_target_students(
    db: AsyncSession, rule: dict | None
) -> list[Student]:
    """根据 target_rule JSON 解析目标学生列表。"""
    stmt = select(Student).where(Student.deleted_at.is_(None))
    if rule:
        if rule.get("exclude_graduated", True):
            stmt = stmt.where(Student.graduation_flag.is_(False))
        if rule.get("grade_codes"):
            stmt = stmt.where(Student.grade_code.in_(rule["grade_codes"]))
        if rule.get("major_codes"):
            stmt = stmt.where(Student.major_code.in_(rule["major_codes"]))
        if rule.get("class_codes"):
            stmt = stmt.where(Student.class_code.in_(rule["class_codes"]))
        if rule.get("political_status"):
            stmt = stmt.where(Student.political_status.in_(rule["political_status"]))
    stmt = stmt.order_by(Student.id)
    return list((await db.execute(stmt)).scalars().all())


async def find_user_by_student_id(db: AsyncSession, student_id: int) -> User | None:
    stmt = select(User).where(User.student_id == student_id)
    return (await db.execute(stmt)).scalar_one_or_none()


# ---------- Batch / Delivery ----------
async def create_batch(db: AsyncSession, **fields) -> NoticeDeliveryBatch:
    row = NoticeDeliveryBatch(**fields)
    db.add(row)
    await db.flush()
    return row


async def get_batch(db: AsyncSession, batch_id: int) -> NoticeDeliveryBatch | None:
    return await db.get(NoticeDeliveryBatch, batch_id)


async def list_batches_for_notice(
    db: AsyncSession, notice_id: int
) -> Sequence[NoticeDeliveryBatch]:
    stmt = (
        select(NoticeDeliveryBatch)
        .where(NoticeDeliveryBatch.notice_id == notice_id)
        .order_by(NoticeDeliveryBatch.started_at.desc())
    )
    return (await db.execute(stmt)).scalars().all()


async def add_delivery(db: AsyncSession, **fields) -> NoticeDelivery:
    row = NoticeDelivery(**fields)
    db.add(row)
    await db.flush()
    return row


async def list_deliveries_for_batch(
    db: AsyncSession,
    batch_id: int,
    *,
    status: str | None = None,
    channel: str | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[Sequence[NoticeDelivery], int]:
    stmt = select(NoticeDelivery).where(NoticeDelivery.batch_id == batch_id)
    if status:
        stmt = stmt.where(NoticeDelivery.status == status)
    if channel:
        stmt = stmt.where(NoticeDelivery.channel == channel)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(NoticeDelivery.id).offset((page - 1) * size).limit(size)
    rows = (await db.execute(stmt)).scalars().all()
    return rows, total


# ---------- Student-side inbox ----------
async def list_notices_for_student(
    db: AsyncSession,
    user_id: int,
    student_id: int,
    *,
    unread_only: bool = False,
    page: int = 1,
    size: int = 20,
) -> tuple[list[tuple[Notice, NoticeDelivery | None]], int]:
    """学生收件箱：以 IN_APP 投递记录 JOIN 通知。"""
    # 仅展示 IN_APP 投递且 notice 已发布的
    stmt = (
        select(Notice, NoticeDelivery)
        .join(NoticeDelivery, NoticeDelivery.notice_id == Notice.id)
        .where(
            and_(
                NoticeDelivery.student_id == student_id,
                NoticeDelivery.channel == "IN_APP",
                Notice.status == NOTICE_STATUS_PUBLISHED,
            )
        )
    )
    if unread_only:
        stmt = stmt.where(NoticeDelivery.read_at.is_(None))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        stmt.order_by(Notice.is_pinned.desc(), Notice.published_at.desc().nullslast())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    rows = [(r.Notice, r.NoticeDelivery) for r in result.all()]
    return rows, total


async def student_has_notice_delivery(
    db: AsyncSession,
    notice_id: int,
    student_id: int,
    *,
    channel: str | None = None,
) -> bool:
    stmt = select(NoticeDelivery.id).where(
        NoticeDelivery.notice_id == notice_id,
        NoticeDelivery.student_id == student_id,
    )
    if channel:
        stmt = stmt.where(NoticeDelivery.channel == channel)
    return (await db.execute(stmt.limit(1))).scalar_one_or_none() is not None


async def mark_delivery_read(
    db: AsyncSession, delivery_id: int, student_id: int
) -> NoticeDelivery | None:
    from datetime import datetime, timezone
    d = await db.get(NoticeDelivery, delivery_id)
    if d is None or d.student_id != student_id:
        return None
    if d.read_at is None:
        d.read_at = datetime.now(timezone.utc)
        d.status = DELIVERY_STATUS_READ
    await db.flush()
    return d
