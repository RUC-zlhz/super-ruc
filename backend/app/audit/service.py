"""审计日志写入服务。

所有敏感操作（登录、审批、导出、权限变更、敏感字段访问）
必须显式调用 log_action()，由后端统一落库。

v1.5 新增：`archive_expired_logs()` 定时将超期日志搬迁到 `audit_log_history`，
防止 `audit_logs` 主表膨胀拖慢 Kingbase 查询（NFR-002 / 4.2 设计约束）。
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog, AuditLogHistory

logger = logging.getLogger(__name__)


async def log_action(
    db: AsyncSession,
    *,
    event_type: str,
    entity_code: str,
    action: str,
    entity_id: int | None = None,
    actor_user_id: int | None = None,
    actor_role: str | None = None,
    result_code: str = "SUCCESS",
    ip_address: str | None = None,
    user_agent: str | None = None,
    detail: dict[str, Any] | None = None,
    message: str | None = None,
    auto_flush: bool = True,
) -> AuditLog:
    row = AuditLog(
        event_type=event_type,
        entity_code=entity_code,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action=action,
        result_code=result_code,
        ip_address=ip_address,
        user_agent=user_agent,
        detail=detail,
        message=message,
    )
    db.add(row)
    if auto_flush:
        await db.flush()
    return row


# 留存期：默认 1 个学期 ≈ 180 天，可按部署需要调整或从 settings 注入
DEFAULT_RETENTION_DAYS = 180


async def archive_expired_logs(
    db: AsyncSession,
    *,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    batch_size: int = 1000,
) -> dict[str, int]:
    """将 `audit_logs` 中早于 cutoff 的记录迁移至 `audit_log_history`。

    * 单批处理 batch_size 条，避免 Kingbase 长事务锁表。
    * 迁移成功后才从主表删除，由同一事务保证原子。
    * 建议由定时任务（每日凌晨）调度；可手工触发用于运维。
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    total_moved = 0
    total_kept = 0

    while True:
        rows = (
            await db.execute(
                select(AuditLog)
                .where(AuditLog.occurred_at < cutoff)
                .order_by(AuditLog.occurred_at.asc())
                .limit(batch_size)
            )
        ).scalars().all()
        if not rows:
            break

        payload = [
            {
                "id": r.id,
                "event_type": r.event_type,
                "entity_code": r.entity_code,
                "entity_id": r.entity_id,
                "actor_user_id": r.actor_user_id,
                "actor_role": r.actor_role,
                "action": r.action,
                "result_code": r.result_code,
                "ip_address": r.ip_address,
                "user_agent": r.user_agent,
                "detail": r.detail,
                "message": r.message,
                "occurred_at": r.occurred_at,
            }
            for r in rows
        ]
        ids = [r.id for r in rows]
        await db.execute(insert(AuditLogHistory), payload)
        await db.execute(delete(AuditLog).where(AuditLog.id.in_(ids)))
        await db.commit()
        total_moved += len(rows)
        if len(rows) < batch_size:
            break

    total_kept = (
        await db.scalar(select(AuditLog.id).limit(1))
    ) is not None
    summary = {
        "cutoff": int(cutoff.timestamp()),
        "retention_days": retention_days,
        "moved": total_moved,
        "has_remaining": int(bool(total_kept)),
    }
    logger.info("audit archive done | %s", summary)
    return summary
