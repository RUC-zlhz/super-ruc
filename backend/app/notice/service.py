"""notice 业务服务层 — 发布 / 目标解析 / 多通道发送（mock）。

发送策略：
- IN_APP: 直接在 notice_deliveries 插记录，学生端拉取即可。
- EMAIL: 调用 SMTP（此处预留接口，失败写 error_*）。
- SMS: 仅在 settings.SMS_ENABLED=True 时尝试；否则标记为 SKIPPED。
"""
from __future__ import annotations

import logging
import smtplib
import uuid
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_action
from app.core.config import settings
from app.core.exceptions import BizError, ConflictError, NotFoundError
from app.notice import repository as repo
from app.notice.models import (
    CHANNEL_EMAIL,
    CHANNEL_IN_APP,
    CHANNEL_SMS,
    DELIVERY_STATUS_FAILED,
    DELIVERY_STATUS_SENT,
    DELIVERY_STATUS_SKIPPED,
    NOTICE_STATUS_ARCHIVED,
    NOTICE_STATUS_DRAFT,
    NOTICE_STATUS_PUBLISHED,
    Notice,
    NoticeDeliveryBatch,
)
from app.notice.schemas import (
    NoticeBrief,
    NoticeIn,
    NoticeOut,
    StudentNoticeItem,
    TargetPreviewResult,
    TargetRule,
)

logger = logging.getLogger(__name__)


def _channels_to_str(items: list[str]) -> str:
    return ",".join([c.strip().upper() for c in items if c and c.strip()])


def _str_to_channels(s: str | None) -> list[str]:
    if not s:
        return []
    return [c.strip().upper() for c in s.split(",") if c.strip()]


def notice_to_out(notice: Notice) -> NoticeOut:
    return NoticeOut(
        id=notice.id,
        title=notice.title,
        body_md=notice.body_md,
        summary=notice.summary,
        category=notice.category,
        status=notice.status,
        source_type=notice.source_type,
        source_url=notice.source_url,
        channels=notice.channels,
        target_rule=notice.target_rule,
        target_summary=notice.target_summary,
        effective_start=notice.effective_start,
        effective_end=notice.effective_end,
        is_pinned=notice.is_pinned,
        published_at=notice.published_at,
        updated_at=notice.updated_at,
        tags=[t.tag for t in (notice.tags or [])],
    )


def notice_to_brief(notice: Notice) -> NoticeBrief:
    return NoticeBrief(
        id=notice.id,
        title=notice.title,
        summary=notice.summary,
        category=notice.category,
        status=notice.status,
        source_type=notice.source_type,
        channels=notice.channels,
        target_summary=notice.target_summary,
        is_pinned=notice.is_pinned,
        published_at=notice.published_at,
        updated_at=notice.updated_at,
        tags=[t.tag for t in (notice.tags or [])],
    )


# ---------- Target preview ----------
async def preview_target(
    db: AsyncSession, rule: TargetRule | None
) -> TargetPreviewResult:
    rule_dict = rule.model_dump() if rule else None
    students = await repo.resolve_target_students(db, rule_dict)
    return TargetPreviewResult(
        target_count=len(students),
        sample_student_nos=[s.student_no for s in students[:10]],
    )


# ---------- CRUD ----------
async def create_notice(
    db: AsyncSession, payload: NoticeIn, operator_id: int, operator_role: str | None
) -> NoticeOut:
    row = await repo.create_notice(
        db,
        title=payload.title,
        body_md=payload.body_md,
        summary=payload.summary,
        category=payload.category,
        status=NOTICE_STATUS_DRAFT,
        source_type=payload.source_type,
        source_url=payload.source_url,
        target_rule=payload.target_rule.model_dump() if payload.target_rule else None,
        target_summary=payload.target_summary,
        channels=_channels_to_str(payload.channels) or CHANNEL_IN_APP,
        effective_start=payload.effective_start,
        effective_end=payload.effective_end,
        is_pinned=payload.is_pinned,
        created_by=operator_id,
        updated_by=operator_id,
    )
    await repo.set_notice_tags(db, row.id, payload.tags)
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE",
        action="CREATE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return notice_to_out(row)


async def update_notice(
    db: AsyncSession,
    notice_id: int,
    payload: NoticeIn,
    operator_id: int,
    operator_role: str | None,
) -> NoticeOut:
    row = await repo.get_notice(db, notice_id)
    if row is None:
        raise NotFoundError("通知不存在")
    if row.status == NOTICE_STATUS_ARCHIVED:
        raise BizError("已归档通知不可编辑", code=40030)

    row.title = payload.title
    row.body_md = payload.body_md
    row.summary = payload.summary
    row.category = payload.category
    row.source_type = payload.source_type
    row.source_url = payload.source_url
    row.target_rule = payload.target_rule.model_dump() if payload.target_rule else None
    row.target_summary = payload.target_summary
    row.channels = _channels_to_str(payload.channels) or row.channels
    row.effective_start = payload.effective_start
    row.effective_end = payload.effective_end
    row.is_pinned = payload.is_pinned
    row.updated_by = operator_id

    await repo.set_notice_tags(db, row.id, payload.tags)
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE",
        action="UPDATE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return notice_to_out(row)


async def publish_notice(
    db: AsyncSession, notice_id: int, operator_id: int, operator_role: str | None
) -> NoticeOut:
    row = await repo.get_notice(db, notice_id)
    if row is None:
        raise NotFoundError("通知不存在")
    if row.status == NOTICE_STATUS_PUBLISHED:
        raise ConflictError("通知已发布")
    if row.status == NOTICE_STATUS_ARCHIVED:
        raise BizError("已归档通知不可重新发布", code=40031)

    row.status = NOTICE_STATUS_PUBLISHED
    row.published_at = datetime.now(timezone.utc)
    row.published_by = operator_id
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE",
        action="PUBLISH",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return notice_to_out(row)


async def archive_notice(
    db: AsyncSession, notice_id: int, operator_id: int, operator_role: str | None
) -> NoticeOut:
    row = await repo.get_notice(db, notice_id)
    if row is None:
        raise NotFoundError("通知不存在")
    if row.status == NOTICE_STATUS_ARCHIVED:
        return notice_to_out(row)
    row.status = NOTICE_STATUS_ARCHIVED
    row.archived_at = datetime.now(timezone.utc)
    row.archived_by = operator_id
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE",
        action="ARCHIVE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return notice_to_out(row)


# ---------- Dispatch ----------
def _send_email(to_addr: str, subject: str, body: str) -> tuple[bool, str | None]:
    """简化：直接 SMTP。生产环境应走任务队列。"""
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_addr
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
            if settings.SMTP_USER:
                s.starttls()
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.sendmail(settings.SMTP_FROM, [to_addr], msg.as_string())
        return True, None
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:256]


def _send_sms(_to_number: str, _body: str) -> tuple[bool, str | None]:
    """SMS 网关占位。实际集成按甲方选择的运营商。"""
    if not settings.SMS_ENABLED:
        return False, "SMS_DISABLED"
    # 生产集成点：阿里云/腾讯云/中兴/玄武等 SMS 网关
    logger.info("[SMS mock] to=%s body_len=%d", _to_number, len(_body))
    return True, None


async def dispatch_notice(
    db: AsyncSession,
    notice_id: int,
    *,
    override_channels: list[str] | None,
    note: str | None,
    operator_id: int,
    operator_role: str | None,
) -> NoticeDeliveryBatch:
    notice = await repo.get_notice(db, notice_id)
    if notice is None:
        raise NotFoundError("通知不存在")
    if notice.status != NOTICE_STATUS_PUBLISHED:
        raise BizError("通知未发布，不能发送", code=40032)

    channels = override_channels or _str_to_channels(notice.channels)
    if not channels:
        raise BizError("未指定发送渠道", code=40033)

    students = await repo.resolve_target_students(db, notice.target_rule)
    batch = await repo.create_batch(
        db,
        notice_id=notice.id,
        batch_no=f"NB-{datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
        channels=",".join(channels),
        target_rule_snapshot=notice.target_rule,
        target_count=len(students),
        note=note,
        created_by=operator_id,
    )

    success = 0
    failed = 0
    for stu in students:
        user = await repo.find_user_by_student_id(db, stu.id)
        for ch in channels:
            sent_ok = False
            err_code: str | None = None
            err_msg: str | None = None
            target_handle: str | None = None

            if ch == CHANNEL_IN_APP:
                sent_ok = True  # 入库即送达
            elif ch == CHANNEL_EMAIL:
                if not stu.email:
                    err_code = "NO_EMAIL"
                else:
                    target_handle = stu.email
                    ok_, err = _send_email(stu.email, notice.title, notice.summary or notice.title)
                    sent_ok = ok_
                    if not ok_:
                        err_code = "SMTP_ERROR"
                        err_msg = err
            elif ch == CHANNEL_SMS:
                if not settings.SMS_ENABLED:
                    err_code = "SMS_DISABLED"
                else:
                    # phone 解密能力后续接入；此处仅 mock 使用 user phone email 字段
                    target_handle = (user.email if user else stu.email) or ""
                    ok_, err = _send_sms(target_handle, notice.summary or notice.title)
                    sent_ok = ok_
                    if not ok_:
                        err_code = "SMS_ERROR"
                        err_msg = err
            else:
                err_code = "UNSUPPORTED_CHANNEL"

            status = DELIVERY_STATUS_SENT if sent_ok else (
                DELIVERY_STATUS_SKIPPED if err_code in ("NO_EMAIL", "SMS_DISABLED", "UNSUPPORTED_CHANNEL")
                else DELIVERY_STATUS_FAILED
            )
            if sent_ok:
                success += 1
            elif status == DELIVERY_STATUS_FAILED:
                failed += 1

            await repo.add_delivery(
                db,
                batch_id=batch.id,
                notice_id=notice.id,
                student_id=stu.id,
                user_id=user.id if user else None,
                channel=ch,
                status=status,
                target_handle=target_handle,
                sent_at=datetime.now(timezone.utc) if sent_ok else None,
                error_code=err_code,
                error_message=err_msg,
            )

    batch.success_count = success
    batch.failed_count = failed
    batch.finished_at = datetime.now(timezone.utc)
    if failed == 0:
        batch.status = "COMPLETED"
    elif success == 0:
        batch.status = "FAILED"
    else:
        batch.status = "PARTIAL"

    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE_BATCH",
        action="DISPATCH",
        entity_id=batch.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={
            "notice_id": notice.id,
            "channels": channels,
            "target": len(students),
            "success": success,
            "failed": failed,
        },
    )
    await db.commit()
    await db.refresh(batch)
    return batch


# ---------- Student inbox ----------
async def list_student_inbox(
    db: AsyncSession,
    user_id: int,
    student_id: int,
    *,
    unread_only: bool,
    page: int,
    size: int,
) -> tuple[list[StudentNoticeItem], int]:
    rows, total = await repo.list_notices_for_student(
        db, user_id, student_id, unread_only=unread_only, page=page, size=size
    )
    items: list[StudentNoticeItem] = []
    for notice, delivery in rows:
        items.append(
            StudentNoticeItem(
                id=notice.id,
                title=notice.title,
                summary=notice.summary,
                category=notice.category,
                is_pinned=notice.is_pinned,
                published_at=notice.published_at,
                read_at=delivery.read_at if delivery else None,
                delivery_id=delivery.id if delivery else None,
            )
        )
    return items, total


async def mark_read(
    db: AsyncSession, delivery_id: int, student_id: int
) -> None:
    d = await repo.mark_delivery_read(db, delivery_id, student_id)
    if d is None:
        raise NotFoundError("投递记录不存在")
    await db.commit()
