"""honor 服务层 — FR-017。"""
from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_action
from app.auth import repository as auth_repo
from app.core.exceptions import BizError, NotFoundError
from app.honor import repository as repo
from app.honor.models import (
    HONOR_LEVEL_MINISTERIAL,
    HONOR_LEVEL_NATIONAL,
    HONOR_LEVEL_PROVINCIAL,
    HONOR_LEVEL_SCHOOL,
    HONOR_STATUS_ACTIVE,
    HONOR_STATUS_ARCHIVED,
    HONOR_STATUS_REVOKED,
    HonorRecord,
)
from app.honor.schemas import (
    AdminHonorRecordBrief,
    AdminHonorRecordDetail,
    PublicHonorRecordBrief,
    PublicHonorRecordDetail,
)

_ALLOWED_LEVELS = {
    HONOR_LEVEL_NATIONAL,
    HONOR_LEVEL_PROVINCIAL,
    HONOR_LEVEL_MINISTERIAL,
    HONOR_LEVEL_SCHOOL,
}


def _history_meta(record: HonorRecord) -> tuple[bool, str | None]:
    today = date.today()
    if record.status == HONOR_STATUS_ARCHIVED:
        return True, "已归档"
    if record.status == HONOR_STATUS_ACTIVE and record.effective_to and record.effective_to < today:
        return True, "公示期已结束"
    return False, None


async def _category_name_map(db: AsyncSession, records: list[HonorRecord]) -> dict[str, str]:
    categories = await repo.get_categories_by_codes(
        db, {record.category_code for record in records if record.category_code}
    )
    return {code: row.name for code, row in categories.items()}


async def _user_name_map(db: AsyncSession, user_ids: set[int]) -> dict[int, str]:
    rows = await auth_repo.get_users_by_ids(db, user_ids)
    return {user_id: row.display_name for user_id, row in rows.items()}


def build_public_brief(
    record: HonorRecord, *, category_name: str | None
) -> PublicHonorRecordBrief:
    is_historical, history_reason = _history_meta(record)
    return PublicHonorRecordBrief(
        id=record.id,
        category_code=record.category_code,
        category_name=category_name,
        title=record.title,
        level=record.level,
        awarded_by=record.awarded_by,
        announced_at=record.announced_at,
        status=record.status,
        is_collective=record.is_collective,
        cover_image_url=record.cover_image_url,
        summary=record.summary,
        effective_to=record.effective_to,
        recipient_names=[row.display_name for row in (record.recipients or [])],
        is_historical=is_historical,
        history_reason=history_reason,
    )


def build_public_detail(
    record: HonorRecord, *, category_name: str | None
) -> PublicHonorRecordDetail:
    is_historical, history_reason = _history_meta(record)
    return PublicHonorRecordDetail(
        id=record.id,
        category_code=record.category_code,
        category_name=category_name,
        title=record.title,
        level=record.level,
        awarded_by=record.awarded_by,
        document_no=record.document_no,
        announced_at=record.announced_at,
        effective_from=record.effective_from,
        effective_to=record.effective_to,
        is_collective=record.is_collective,
        summary=record.summary,
        story_md=record.story_md,
        acceptance_speech=record.acceptance_speech,
        cover_image_url=record.cover_image_url,
        media=record.media,
        status=record.status,
        view_count=record.view_count,
        recipients=record.recipients or [],
        updated_at=record.updated_at,
        is_historical=is_historical,
        history_reason=history_reason,
    )


def build_admin_brief(
    record: HonorRecord,
    *,
    category_name: str | None,
    updated_by_name: str | None,
) -> AdminHonorRecordBrief:
    is_historical, history_reason = _history_meta(record)
    return AdminHonorRecordBrief(
        id=record.id,
        category_code=record.category_code,
        category_name=category_name,
        title=record.title,
        level=record.level,
        awarded_by=record.awarded_by,
        announced_at=record.announced_at,
        status=record.status,
        is_collective=record.is_collective,
        cover_image_url=record.cover_image_url,
        summary=record.summary,
        effective_to=record.effective_to,
        recipient_names=[row.display_name for row in (record.recipients or [])],
        consent_flag=record.consent_flag,
        updated_at=record.updated_at,
        updated_by_name=updated_by_name,
        is_historical=is_historical,
        history_reason=history_reason,
    )


def build_admin_detail(
    record: HonorRecord,
    *,
    category_name: str | None,
    updated_by_name: str | None,
) -> AdminHonorRecordDetail:
    is_historical, history_reason = _history_meta(record)
    return AdminHonorRecordDetail(
        id=record.id,
        category_code=record.category_code,
        category_name=category_name,
        title=record.title,
        level=record.level,
        awarded_by=record.awarded_by,
        document_no=record.document_no,
        announced_at=record.announced_at,
        effective_from=record.effective_from,
        effective_to=record.effective_to,
        is_collective=record.is_collective,
        summary=record.summary,
        story_md=record.story_md,
        acceptance_speech=record.acceptance_speech,
        cover_image_url=record.cover_image_url,
        media=record.media,
        status=record.status,
        consent_flag=record.consent_flag,
        view_count=record.view_count,
        archived_at=record.archived_at,
        archive_reason=record.archive_reason,
        recipients=record.recipients or [],
        updated_at=record.updated_at,
        updated_by_name=updated_by_name,
        is_historical=is_historical,
        history_reason=history_reason,
    )


async def build_public_briefs(
    db: AsyncSession, records: list[HonorRecord]
) -> list[PublicHonorRecordBrief]:
    category_names = await _category_name_map(db, records)
    return [
        build_public_brief(record, category_name=category_names.get(record.category_code))
        for record in records
    ]


async def build_admin_briefs(
    db: AsyncSession, records: list[HonorRecord]
) -> list[AdminHonorRecordBrief]:
    category_names = await _category_name_map(db, records)
    user_names = await _user_name_map(
        db, {record.updated_by for record in records if record.updated_by}
    )
    return [
        build_admin_brief(
            record,
            category_name=category_names.get(record.category_code),
            updated_by_name=user_names.get(record.updated_by or 0),
        )
        for record in records
    ]


async def build_public_detail_for_record(
    db: AsyncSession, record: HonorRecord
) -> PublicHonorRecordDetail:
    category_names = await _category_name_map(db, [record])
    return build_public_detail(record, category_name=category_names.get(record.category_code))


async def build_admin_detail_for_record(
    db: AsyncSession, record: HonorRecord
) -> AdminHonorRecordDetail:
    category_names = await _category_name_map(db, [record])
    user_names = await _user_name_map(
        db, {record.updated_by} if record.updated_by else set()
    )
    return build_admin_detail(
        record,
        category_name=category_names.get(record.category_code),
        updated_by_name=user_names.get(record.updated_by or 0),
    )


async def create_record(
    db: AsyncSession,
    payload: dict[str, Any],
    *,
    operator_id: int,
    operator_role: str | None,
) -> HonorRecord:
    level = payload.get("level")
    if level not in _ALLOWED_LEVELS:
        raise BizError(f"不支持的荣誉级别：{level}（仅限校级及以上）", code=40170)
    recipients = payload.pop("recipients", []) or []
    payload.setdefault("status", HONOR_STATUS_ACTIVE)
    payload["created_by"] = operator_id
    payload["updated_by"] = operator_id
    row = await repo.create_record(db, payload)
    await repo.set_recipients(db, row.id, recipients)
    await log_action(
        db,
        event_type="HONOR",
        entity_code="HONOR_RECORD",
        action="CREATE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    refreshed = await repo.get_record(db, row.id)
    if refreshed is None:
        raise NotFoundError("荣誉记录不存在")
    return refreshed


async def update_record(
    db: AsyncSession,
    record_id: int,
    payload: dict[str, Any],
    *,
    operator_id: int,
    operator_role: str | None,
) -> HonorRecord:
    row = await repo.get_record(db, record_id)
    if row is None:
        raise NotFoundError("荣誉记录不存在")
    recipients = payload.pop("recipients", None)
    level = payload.get("level")
    if level and level not in _ALLOWED_LEVELS:
        raise BizError(f"不支持的荣誉级别：{level}", code=40170)
    for k, v in payload.items():
        setattr(row, k, v)
    row.updated_by = operator_id
    if recipients is not None:
        await repo.set_recipients(db, row.id, recipients)
    await log_action(
        db,
        event_type="HONOR",
        entity_code="HONOR_RECORD",
        action="UPDATE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    refreshed = await repo.get_record(db, row.id)
    if refreshed is None:
        raise NotFoundError("荣誉记录不存在")
    return refreshed


async def archive_record(
    db: AsyncSession,
    record_id: int,
    *,
    new_status: str,
    reason: str | None,
    operator_id: int,
    operator_role: str | None,
) -> HonorRecord:
    if new_status not in (HONOR_STATUS_ARCHIVED, HONOR_STATUS_REVOKED):
        raise BizError(f"无效的归档状态 {new_status}", code=40171)
    row = await repo.get_record(db, record_id)
    if row is None:
        raise NotFoundError("荣誉记录不存在")
    await repo.archive_record(
        db, row, new_status=new_status, reason=reason, actor_user_id=operator_id
    )
    row.updated_by = operator_id
    await log_action(
        db,
        event_type="HONOR",
        entity_code="HONOR_RECORD",
        action="ARCHIVE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"new_status": new_status, "reason": reason},
    )
    await db.commit()
    refreshed = await repo.get_record(db, row.id)
    if refreshed is None:
        raise NotFoundError("荣誉记录不存在")
    return refreshed


async def view_record_public(db: AsyncSession, record_id: int) -> HonorRecord:
    row = await repo.get_record(db, record_id)
    if row is None or not row.consent_flag:
        raise NotFoundError("荣誉记录不存在")
    if row.status == HONOR_STATUS_REVOKED:
        raise NotFoundError("荣誉记录已撤销")
    await repo.increment_view_count(db, row)
    await db.commit()
    refreshed = await repo.get_record(db, record_id)
    if refreshed is None:
        raise NotFoundError("荣誉记录不存在")
    return refreshed
