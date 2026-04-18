"""审计模块仓储层。"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog, RoleFieldPolicy


async def list_audit_logs(
    db: AsyncSession,
    *,
    page: int = 1,
    size: int = 20,
    event_type: str | None = None,
    entity_code: str | None = None,
    actor_user_id: int | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> tuple[Sequence[AuditLog], int]:
    stmt = select(AuditLog)
    if event_type:
        stmt = stmt.where(AuditLog.event_type == event_type)
    if entity_code:
        stmt = stmt.where(AuditLog.entity_code == entity_code)
    if actor_user_id:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    if since:
        stmt = stmt.where(AuditLog.occurred_at >= since)
    if until:
        stmt = stmt.where(AuditLog.occurred_at <= until)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(AuditLog.occurred_at.desc()).offset((page - 1) * size).limit(size)
    rows = (await db.execute(stmt)).scalars().all()
    return rows, total


async def list_role_policies(db: AsyncSession, role_code: str | None = None) -> Sequence[RoleFieldPolicy]:
    stmt = select(RoleFieldPolicy)
    if role_code:
        stmt = stmt.where(RoleFieldPolicy.role_code == role_code)
    return (await db.execute(stmt)).scalars().all()
