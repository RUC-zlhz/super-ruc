"""Repository helpers for backend-account import batches."""
from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin_users.models import (
    BATCH_STATUS_COMMITTED,
    AdminUserImportBatch,
    AdminUserImportRow,
)
from app.auth.models import Role, User, UserRole


async def create_batch(
    db: AsyncSession,
    *,
    batch_no: str,
    filename: str,
    file_size: int | None,
    mime_type: str | None,
    operator_id: int,
    operator_role: str | None,
) -> AdminUserImportBatch:
    batch = AdminUserImportBatch(
        batch_no=batch_no,
        filename=filename,
        file_size=file_size,
        mime_type=mime_type,
        operator_id=operator_id,
        operator_role=operator_role,
    )
    db.add(batch)
    await db.flush()
    return batch


async def add_batch_row(
    db: AsyncSession,
    *,
    batch_id: int,
    row_no: int,
    work_no: str | None = None,
    role_code: str | None = None,
    scope_code: str | None = None,
    raw_data: dict | None = None,
    normalized_data: dict | None = None,
    severity: str,
    result: str,
    field_name: str | None = None,
    message: str | None = None,
) -> AdminUserImportRow:
    row = AdminUserImportRow(
        batch_id=batch_id,
        row_no=row_no,
        work_no=work_no,
        role_code=role_code,
        scope_code=scope_code,
        raw_data=raw_data,
        normalized_data=normalized_data,
        severity=severity,
        result=result,
        field_name=field_name,
        message=message,
    )
    db.add(row)
    await db.flush()
    return row


async def get_batch(db: AsyncSession, batch_id: int) -> AdminUserImportBatch | None:
    return await db.get(AdminUserImportBatch, batch_id)


async def get_batch_by_no(db: AsyncSession, batch_no: str) -> AdminUserImportBatch | None:
    stmt = select(AdminUserImportBatch).where(AdminUserImportBatch.batch_no == batch_no)
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_batches(
    db: AsyncSession,
    *,
    page: int,
    size: int,
) -> tuple[list[AdminUserImportBatch], int]:
    stmt = select(AdminUserImportBatch)
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    rows = (
        await db.execute(
            stmt.order_by(AdminUserImportBatch.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
    ).scalars().all()
    return list(rows), total


async def list_batch_rows(
    db: AsyncSession,
    batch_id: int,
    *,
    limit: int = 100000,
) -> list[AdminUserImportRow]:
    stmt = (
        select(AdminUserImportRow)
        .where(AdminUserImportRow.batch_id == batch_id)
        .order_by(AdminUserImportRow.row_no.asc(), AdminUserImportRow.id.asc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def finalize_preview(
    db: AsyncSession,
    batch: AdminUserImportBatch,
    *,
    status: str,
    total_rows: int,
    ok_rows: int,
    warn_rows: int,
    fatal_rows: int,
    summary: dict,
) -> None:
    batch.status = status
    batch.total_rows = total_rows
    batch.ok_rows = ok_rows
    batch.warn_rows = warn_rows
    batch.fatal_rows = fatal_rows
    batch.summary = summary
    batch.finished_at = datetime.now(UTC)
    await db.flush()


async def mark_committed(
    db: AsyncSession,
    batch: AdminUserImportBatch,
    *,
    created_rows: int,
    existing_rows: int,
    role_granted_rows: int,
    unchanged_rows: int,
    summary: dict,
) -> None:
    batch.status = BATCH_STATUS_COMMITTED
    batch.created_rows = created_rows
    batch.existing_rows = existing_rows
    batch.role_granted_rows = role_granted_rows
    batch.unchanged_rows = unchanged_rows
    batch.summary = summary
    batch.committed_at = datetime.now(UTC)
    await db.flush()


async def list_roles_by_codes(db: AsyncSession, role_codes: set[str]) -> dict[str, Role]:
    if not role_codes:
        return {}
    rows = (
        await db.execute(select(Role).where(Role.code.in_(sorted(role_codes))))
    ).scalars().all()
    return {row.code: row for row in rows}


async def list_users_by_work_no(db: AsyncSession, work_nos: set[str]) -> dict[str, User]:
    if not work_nos:
        return {}
    rows = (
        await db.execute(
            select(User).where(User.work_no.in_(sorted(work_nos)), User.deleted_at.is_(None))
        )
    ).scalars().all()
    return {row.work_no: row for row in rows if row.work_no}


async def list_roles_for_user(db: AsyncSession, user_id: int) -> Sequence[UserRole]:
    rows = (
        await db.execute(select(UserRole).where(UserRole.user_id == user_id))
    ).scalars().all()
    return rows
