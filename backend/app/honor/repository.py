"""honor 模块 repository — FR-017。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.honor.models import (
    HONOR_STATUS_ACTIVE,
    HONOR_STATUS_ARCHIVED,
    HonorCategory,
    HonorRecipient,
    HonorRecord,
)


# ---- 类别 ----
async def list_categories(db: AsyncSession) -> list[HonorCategory]:
    stmt = (
        select(HonorCategory)
        .where(HonorCategory.is_active.is_(True))
        .order_by(HonorCategory.sort_order.asc(), HonorCategory.id.asc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def upsert_category(db: AsyncSession, payload: dict[str, Any]) -> HonorCategory:
    stmt = select(HonorCategory).where(HonorCategory.code == payload["code"])
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        row = HonorCategory(**payload)
        db.add(row)
    else:
        for k, v in payload.items():
            setattr(row, k, v)
    await db.flush()
    return row


# ---- 荣誉条目 ----
async def create_record(db: AsyncSession, payload: dict[str, Any]) -> HonorRecord:
    row = HonorRecord(**payload)
    db.add(row)
    await db.flush()
    return row


async def get_record(db: AsyncSession, record_id: int) -> HonorRecord | None:
    stmt = (
        select(HonorRecord)
        .where(HonorRecord.id == record_id)
        .options(selectinload(HonorRecord.recipients))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_records(
    db: AsyncSession,
    *,
    category_code: str | None = None,
    level: str | None = None,
    status: str | None = HONOR_STATUS_ACTIVE,
    year: int | None = None,
    q: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[HonorRecord], int]:
    stmt = select(HonorRecord).options(selectinload(HonorRecord.recipients))
    conds = []
    if category_code:
        conds.append(HonorRecord.category_code == category_code)
    if level:
        conds.append(HonorRecord.level == level)
    if status:
        conds.append(HonorRecord.status == status)
    if year:
        conds.append(func.extract("year", HonorRecord.announced_at) == year)
    if q:
        like = f"%{q}%"
        conds.append((HonorRecord.title.ilike(like)) | (HonorRecord.awarded_by.ilike(like)))
    if conds:
        stmt = stmt.where(and_(*conds))
    total = (await db.execute(
        select(func.count()).select_from(stmt.subquery())
    )).scalar_one()
    stmt = (
        stmt.order_by(HonorRecord.announced_at.desc(), HonorRecord.id.desc())
        .offset((page - 1) * size).limit(size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), total


async def set_recipients(
    db: AsyncSession, record_id: int, recipients: list[dict[str, Any]]
) -> list[HonorRecipient]:
    existing = (await db.execute(
        select(HonorRecipient).where(HonorRecipient.record_id == record_id)
    )).scalars().all()
    for r in existing:
        await db.delete(r)
    created: list[HonorRecipient] = []
    for item in recipients:
        row = HonorRecipient(record_id=record_id, **item)
        db.add(row)
        created.append(row)
    await db.flush()
    return created


async def archive_record(
    db: AsyncSession, record: HonorRecord, *, new_status: str,
    reason: str | None, actor_user_id: int | None,
) -> HonorRecord:
    record.status = new_status
    record.archive_reason = reason
    record.archived_at = datetime.utcnow()
    record.archived_by = actor_user_id
    return record


async def increment_view_count(db: AsyncSession, record: HonorRecord) -> None:
    record.view_count = (record.view_count or 0) + 1
