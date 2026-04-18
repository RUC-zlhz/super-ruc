"""honor 服务层 — FR-017。

业务规则：
- 仅允许校级及以上（SCHOOL/MINISTERIAL/PROVINCIAL/NATIONAL）级别的荣誉。
- 学生侧默认展示仍在有效期且 status=ACTIVE 的条目，且 consent_flag=True。
  展示范围默认仅限"在读学生"：若 recipient 链接到 students 且其 graduation_flag=True，则隐藏联系方式等敏感字段（本模块 recipient 不存手机号，故默认已合规）。
- 归档/撤销：写入 archived_at / archive_reason / archived_by，状态转为 ARCHIVED 或 REVOKED。
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_action
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
from app.honor.schemas import HonorRecordBrief, HonorRecordDetail

_ALLOWED_LEVELS = {
    HONOR_LEVEL_NATIONAL, HONOR_LEVEL_PROVINCIAL,
    HONOR_LEVEL_MINISTERIAL, HONOR_LEVEL_SCHOOL,
}


def record_to_detail(record: HonorRecord) -> HonorRecordDetail:
    return HonorRecordDetail.model_validate(record)


def record_to_brief(record: HonorRecord) -> HonorRecordBrief:
    return HonorRecordBrief(
        id=record.id,
        category_code=record.category_code,
        title=record.title,
        level=record.level,
        awarded_by=record.awarded_by,
        announced_at=record.announced_at,
        status=record.status,
        is_collective=record.is_collective,
        cover_image_url=record.cover_image_url,
        summary=record.summary,
        effective_to=record.effective_to,
        recipient_names=[r.display_name for r in (record.recipients or [])],
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
        db, event_type="HONOR", entity_code="HONOR_RECORD",
        action="CREATE", entity_id=row.id,
        actor_user_id=operator_id, actor_role=operator_role,
    )
    await db.commit()
    refreshed = await repo.get_record(db, row.id)
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
        db, event_type="HONOR", entity_code="HONOR_RECORD",
        action="UPDATE", entity_id=row.id,
        actor_user_id=operator_id, actor_role=operator_role,
    )
    await db.commit()
    refreshed = await repo.get_record(db, row.id)
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
        db, row, new_status=new_status, reason=reason, actor_user_id=operator_id,
    )
    await log_action(
        db, event_type="HONOR", entity_code="HONOR_RECORD",
        action="ARCHIVE", entity_id=row.id,
        actor_user_id=operator_id, actor_role=operator_role,
        detail={"new_status": new_status, "reason": reason},
    )
    await db.commit()
    refreshed = await repo.get_record(db, row.id)
    return refreshed


async def view_record_public(
    db: AsyncSession, record_id: int
) -> HonorRecord:
    row = await repo.get_record(db, record_id)
    if row is None:
        raise NotFoundError("荣誉记录不存在")
    if row.status != HONOR_STATUS_ACTIVE and row.status != HONOR_STATUS_ARCHIVED:
        raise NotFoundError("荣誉记录已撤销")
    await repo.increment_view_count(db, row)
    await db.commit()
    return row
