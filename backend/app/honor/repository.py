"""honor 模块 repository — FR-017。"""
from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.honor.models import (
    HONOR_STATUS_ACTIVE,
    HONOR_STATUS_ARCHIVED,
    HONOR_STATUS_REVOKED,
    HonorCategory,
    HonorRecipient,
    HonorRecord,
)


async def list_categories(
    db: AsyncSession, *, include_inactive: bool = False
) -> list[HonorCategory]:
    stmt = select(HonorCategory)
    if not include_inactive:
        stmt = stmt.where(HonorCategory.is_active.is_(True))
    stmt = stmt.order_by(HonorCategory.sort_order.asc(), HonorCategory.id.asc())
    return list((await db.execute(stmt)).scalars().all())


async def get_categories_by_codes(
    db: AsyncSession, category_codes: set[str]
) -> dict[str, HonorCategory]:
    codes = sorted(code for code in category_codes if code)
    if not codes:
        return {}
    rows = (
        await db.execute(select(HonorCategory).where(HonorCategory.code.in_(codes)))
    ).scalars().all()
    return {row.code: row for row in rows}


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


def _apply_common_filters(
    stmt,
    *,
    category_code: str | None,
    level: str | None,
    year: int | None,
    q: str | None,
    is_collective: bool | None,
):
    conds = []
    if category_code:
        conds.append(HonorRecord.category_code == category_code)
    if level:
        conds.append(HonorRecord.level == level)
    if year:
        conds.append(func.extract("year", HonorRecord.announced_at) == year)
    if q:
        like = f"%{q}%"
        conds.append(
            or_(
                HonorRecord.title.ilike(like),
                HonorRecord.awarded_by.ilike(like),
                HonorRecord.recipients.any(HonorRecipient.display_name.ilike(like)),
            )
        )
    if is_collective is not None:
        conds.append(HonorRecord.is_collective.is_(is_collective))
    if conds:
        stmt = stmt.where(and_(*conds))
    return stmt


async def list_public_records(
    db: AsyncSession,
    *,
    category_code: str | None = None,
    level: str | None = None,
    year: int | None = None,
    q: str | None = None,
    is_collective: bool | None = None,
    include_historical: bool = False,
    page: int = 1,
    size: int = 20,
) -> tuple[list[HonorRecord], int]:
    today = date.today()
    stmt = (
        select(HonorRecord)
        .options(selectinload(HonorRecord.recipients))
        .where(HonorRecord.consent_flag.is_(True))
        .where(HonorRecord.status != HONOR_STATUS_REVOKED)
    )
    stmt = _apply_common_filters(
        stmt,
        category_code=category_code,
        level=level,
        year=year,
        q=q,
        is_collective=is_collective,
    )
    if include_historical:
        stmt = stmt.where(
            or_(
                HonorRecord.status == HONOR_STATUS_ARCHIVED,
                and_(
                    HonorRecord.status == HONOR_STATUS_ACTIVE,
                    HonorRecord.effective_to.is_not(None),
                    HonorRecord.effective_to < today,
                ),
                and_(
                    HonorRecord.status == HONOR_STATUS_ACTIVE,
                    or_(HonorRecord.effective_to.is_(None), HonorRecord.effective_to >= today),
                ),
            )
        )
    else:
        stmt = stmt.where(HonorRecord.status == HONOR_STATUS_ACTIVE).where(
            or_(HonorRecord.effective_to.is_(None), HonorRecord.effective_to >= today)
        )
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    stmt = (
        stmt.order_by(
            HonorRecord.display_order.asc(),
            HonorRecord.announced_at.desc(),
            HonorRecord.id.desc(),
        )
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), total


async def list_records(
    db: AsyncSession,
    *,
    category_code: str | None = None,
    level: str | None = None,
    status: str | None = None,
    year: int | None = None,
    q: str | None = None,
    is_collective: bool | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[HonorRecord], int]:
    stmt = select(HonorRecord).options(selectinload(HonorRecord.recipients))
    stmt = _apply_common_filters(
        stmt,
        category_code=category_code,
        level=level,
        year=year,
        q=q,
        is_collective=is_collective,
    )
    if status:
        stmt = stmt.where(HonorRecord.status == status)
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    stmt = (
        stmt.order_by(
            HonorRecord.display_order.asc(),
            HonorRecord.announced_at.desc(),
            HonorRecord.id.desc(),
        )
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), total


async def set_recipients(
    db: AsyncSession, record_id: int, recipients: list[dict[str, Any]]
) -> list[HonorRecipient]:
    existing = (
        await db.execute(select(HonorRecipient).where(HonorRecipient.record_id == record_id))
    ).scalars().all()
    for row in existing:
        await db.delete(row)
    created: list[HonorRecipient] = []
    for item in recipients:
        row = HonorRecipient(record_id=record_id, **item)
        db.add(row)
        created.append(row)
    await db.flush()
    return created


async def archive_record(
    db: AsyncSession,
    record: HonorRecord,
    *,
    new_status: str,
    reason: str | None,
    actor_user_id: int | None,
) -> HonorRecord:
    record.status = new_status
    record.archive_reason = reason
    record.archived_at = datetime.now(UTC)
    record.archived_by = actor_user_id
    return record


async def increment_view_count(db: AsyncSession, record: HonorRecord) -> None:
    record.view_count = (record.view_count or 0) + 1
