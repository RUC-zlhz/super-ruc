"""notice 模块仓储层。"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import Student, User, UserRole
from app.auth.role_codes import expand_role_codes_for_lookup
from app.core.sql import order_by_nulls_last_desc
from app.notice.models import (
    DELIVERY_STATUS_READ,
    NOTICE_STATUS_PUBLISHED,
    Notice,
    NoticeDelivery,
    NoticeDeliveryAttempt,
    NoticeDeliveryBatch,
    NoticeIngestRun,
    NoticeSource,
    NoticeTag,
    WechatSubscribeAuthorization,
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
    stmt = stmt.order_by(
        Notice.is_pinned.desc(),
        *order_by_nulls_last_desc(Notice.published_at),
        Notice.updated_at.desc(),
    ).offset((page - 1) * size).limit(size)
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


async def get_notice_by_source_url(db: AsyncSession, source_url: str) -> Notice | None:
    stmt = select(Notice).where(Notice.source_url == source_url)
    return (await db.execute(stmt.limit(1))).scalar_one_or_none()


# ---------- Controlled ingest sources ----------
async def create_notice_source(db: AsyncSession, **fields) -> NoticeSource:
    row = NoticeSource(**fields)
    db.add(row)
    await db.flush()
    return row


async def get_notice_source(db: AsyncSession, source_id: int) -> NoticeSource | None:
    return await db.get(NoticeSource, source_id)


async def list_notice_sources(
    db: AsyncSession,
    *,
    is_active: bool | None = None,
    source_type: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[Sequence[NoticeSource], int]:
    stmt = select(NoticeSource)
    if is_active is not None:
        stmt = stmt.where(NoticeSource.is_active.is_(is_active))
    if source_type:
        stmt = stmt.where(NoticeSource.source_type == source_type)
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    stmt = (
        stmt.order_by(NoticeSource.updated_at.desc(), NoticeSource.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return (await db.execute(stmt)).scalars().all(), total


async def create_ingest_run(db: AsyncSession, **fields) -> NoticeIngestRun:
    row = NoticeIngestRun(**fields)
    db.add(row)
    await db.flush()
    return row


async def list_ingest_runs(
    db: AsyncSession,
    *,
    source_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[Sequence[NoticeIngestRun], int]:
    stmt = select(NoticeIngestRun).options(selectinload(NoticeIngestRun.source))
    if source_id is not None:
        stmt = stmt.where(NoticeIngestRun.source_id == source_id)
    if status:
        stmt = stmt.where(NoticeIngestRun.status == status)
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    stmt = (
        stmt.order_by(NoticeIngestRun.started_at.desc(), NoticeIngestRun.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return (await db.execute(stmt)).scalars().all(), total


# ---------- Target resolution ----------
async def resolve_target_students(
    db: AsyncSession, rule: dict | None
) -> list[Student]:
    """根据 target_rule JSON 解析目标学生列表。"""
    normalized_rule = rule or {}
    stmt = select(Student).distinct().where(Student.deleted_at.is_(None))

    if normalized_rule.get("exclude_graduated", True):
        stmt = stmt.where(Student.graduation_flag.is_(False))
    if normalized_rule.get("grade_codes"):
        stmt = stmt.where(Student.grade_code.in_(normalized_rule["grade_codes"]))
    if normalized_rule.get("major_codes"):
        stmt = stmt.where(Student.major_code.in_(normalized_rule["major_codes"]))
    if normalized_rule.get("class_codes"):
        stmt = stmt.where(Student.class_code.in_(normalized_rule["class_codes"]))
    if normalized_rule.get("political_status"):
        stmt = stmt.where(Student.political_status.in_(normalized_rule["political_status"]))
    if normalized_rule.get("role_codes"):
        lookup_role_codes = expand_role_codes_for_lookup(
            normalized_rule["role_codes"]
        )
        stmt = (
            stmt.join(
                User,
                and_(
                    User.student_id == Student.id,
                    User.deleted_at.is_(None),
                    User.is_active.is_(True),
                ),
            )
            .join(UserRole, UserRole.user_id == User.id)
            .where(UserRole.role_code.in_(lookup_role_codes))
        )
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


async def get_delivery(db: AsyncSession, delivery_id: int) -> NoticeDelivery | None:
    stmt = (
        select(NoticeDelivery)
        .where(NoticeDelivery.id == delivery_id)
        .options(selectinload(NoticeDelivery.attempts))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def add_delivery_attempt(db: AsyncSession, **fields) -> NoticeDeliveryAttempt:
    row = NoticeDeliveryAttempt(**fields)
    db.add(row)
    await db.flush()
    return row


async def next_delivery_attempt_no(db: AsyncSession, delivery_id: int) -> int:
    stmt = select(func.coalesce(func.max(NoticeDeliveryAttempt.attempt_no), 0)).where(
        NoticeDeliveryAttempt.delivery_id == delivery_id
    )
    current = (await db.execute(stmt)).scalar_one()
    return int(current or 0) + 1


# ---------- WeChat subscribe authorizations ----------
async def upsert_wechat_subscribe_authorization(
    db: AsyncSession,
    *,
    user_id: int,
    student_id: int | None,
    openid: str,
    template_id: str,
    scene: str,
    status: str,
) -> WechatSubscribeAuthorization:
    stmt = select(WechatSubscribeAuthorization).where(
        WechatSubscribeAuthorization.user_id == user_id,
        WechatSubscribeAuthorization.template_id == template_id,
    )
    row = (await db.execute(stmt.limit(1))).scalar_one_or_none()
    now = datetime.now(UTC)
    if row is None:
        row = WechatSubscribeAuthorization(
            user_id=user_id,
            student_id=student_id,
            openid=openid,
            template_id=template_id,
            scene=scene,
            status=status,
            authorized_at=now if status == "accept" else None,
        )
        db.add(row)
    else:
        row.student_id = student_id
        row.openid = openid
        row.scene = scene
        row.status = status
        if status == "accept":
            row.authorized_at = now
    await db.flush()
    return row


async def get_wechat_subscribe_authorization(
    db: AsyncSession,
    *,
    user_id: int,
    template_id: str,
) -> WechatSubscribeAuthorization | None:
    stmt = select(WechatSubscribeAuthorization).where(
        WechatSubscribeAuthorization.user_id == user_id,
        WechatSubscribeAuthorization.template_id == template_id,
    )
    return (await db.execute(stmt.limit(1))).scalar_one_or_none()


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
        stmt.order_by(
            Notice.is_pinned.desc(),
            *order_by_nulls_last_desc(Notice.published_at),
        )
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
    from datetime import datetime
    d = await db.get(NoticeDelivery, delivery_id)
    if d is None or d.student_id != student_id:
        return None
    if d.read_at is None:
        d.read_at = datetime.now(UTC)
        d.status = DELIVERY_STATUS_READ
    await db.flush()
    return d
