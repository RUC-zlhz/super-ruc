"""审计日志写入服务。

所有敏感操作（登录、审批、导出、权限变更、敏感字段访问）
必须显式调用 log_action()，由后端统一落库。

v1.5 新增：`archive_expired_logs()` 定时将超期日志搬迁到 `audit_log_history`，
防止 `audit_logs` 主表膨胀拖慢 Kingbase 查询（NFR-002 / 4.2 设计约束）。
"""
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog, AuditLogHistory
from app.core.config import settings
from app.core.sensitive_fields import sanitize_sensitive_data

logger = logging.getLogger(__name__)

AUDIT_RESULT_SUCCESS = "SUCCESS"
AUDIT_RESULT_DENIED = "DENIED"
AUDIT_RESULT_FAILED = "FAILED"

_RESULT_CODE_ALIASES = {
    "SUCCESS": AUDIT_RESULT_SUCCESS,
    "OK": AUDIT_RESULT_SUCCESS,
    "VISIBLE": AUDIT_RESULT_SUCCESS,
    "EDITABLE": AUDIT_RESULT_SUCCESS,
    "DENIED": AUDIT_RESULT_DENIED,
    "FORBIDDEN": AUDIT_RESULT_DENIED,
    "BLOCKED": AUDIT_RESULT_DENIED,
    "FAILED": AUDIT_RESULT_FAILED,
    "FAIL": AUDIT_RESULT_FAILED,
    "ERROR": AUDIT_RESULT_FAILED,
}
_DETAIL_KEYS = (
    "scope",
    "target",
    "refs",
    "changes",
    "masked_fields",
    "reason",
    "metrics",
)
_NUMERIC_DETAIL_KEYS = {
    "count",
    "ok",
    "warn",
    "fatal",
    "rows",
    "target",
    "success",
    "failed",
    "module_count",
    "nodes",
    "total",
}
_CHANGE_HINT_KEYS = {"before", "after", "decision", "comment", "note", "contact", "apply"}


def normalize_result_code(result_code: str | None) -> str:
    if not result_code:
        return AUDIT_RESULT_SUCCESS
    return _RESULT_CODE_ALIASES.get(result_code.strip().upper(), result_code.strip().upper())


def _stringify_reason(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _coerce_refs(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [dict(value)]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        refs: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, Mapping):
                refs.append(dict(item))
            else:
                refs.append({"value": item})
        return refs
    return [{"value": value}]


def _coerce_changes(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [dict(value)]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        changes: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, Mapping):
                changes.append(dict(item))
            else:
                changes.append({"value": item})
        return changes
    return [{"value": value}]


def _coerce_masked_fields(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [str(item) for item in value if item not in (None, "")]
    return [str(value)]


def _coerce_metrics(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    return {"value": value}


def build_audit_detail(
    *,
    scope: str | dict[str, Any] | None = None,
    target: dict[str, Any] | None = None,
    refs: Sequence[dict[str, Any]] | dict[str, Any] | None = None,
    changes: Sequence[dict[str, Any]] | dict[str, Any] | None = None,
    masked_fields: Sequence[str] | str | None = None,
    reason: str | None = None,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "scope": scope,
        "target": dict(target) if isinstance(target, Mapping) else target,
        "refs": _coerce_refs(refs),
        "changes": _coerce_changes(changes),
        "masked_fields": _coerce_masked_fields(masked_fields),
        "reason": _stringify_reason(reason),
        "metrics": dict(metrics or {}),
    }


def normalize_audit_detail(detail: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if detail is None:
        return None

    raw = dict(sanitize_sensitive_data(detail))
    normalized = build_audit_detail(
        scope=raw.pop("scope", None),
        target=raw.pop("target", None),
        refs=raw.pop("refs", None),
        changes=raw.pop("changes", None),
        masked_fields=raw.pop("masked_fields", None),
        reason=raw.pop("reason", None),
        metrics=raw.pop("metrics", None),
    )

    change_payload: dict[str, Any] = {}
    for key in tuple(raw.keys()):
        if key in {"field_name", "before", "after"}:
            change_payload[key] = raw.pop(key)
    if change_payload:
        field_name = change_payload.pop("field_name", None)
        if field_name:
            change_payload["field"] = field_name
        normalized["changes"].append(change_payload)

    for key in tuple(raw.keys()):
        if key in _CHANGE_HINT_KEYS:
            value = raw.pop(key)
            if key == "comment" and normalized["reason"] is None:
                normalized["reason"] = _stringify_reason(value)
            else:
                normalized["changes"].append({key: value})

    for key in tuple(raw.keys()):
        if key in _NUMERIC_DETAIL_KEYS:
            normalized["metrics"][key] = raw.pop(key)

    extra_refs: list[dict[str, Any]] = []
    for key in tuple(raw.keys()):
        extra_refs.append({"key": key, "value": raw.pop(key)})
    if extra_refs:
        normalized["refs"].extend(extra_refs)

    return normalized


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
        result_code=normalize_result_code(result_code),
        ip_address=ip_address,
        user_agent=user_agent,
        detail=normalize_audit_detail(detail),
        message=message,
    )
    db.add(row)
    if auto_flush:
        await db.flush()
    return row


# 留存期：默认 1 个学期 ≈ 180 天，可按部署需要调整或从 settings 注入
DEFAULT_RETENTION_DAYS = settings.AUDIT_ARCHIVE_RETENTION_DAYS


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
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
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
