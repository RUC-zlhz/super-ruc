"""审计模块仓储层。"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import func, literal, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog, AuditLogHistory, RoleFieldPolicy
from app.audit.policies import iter_default_role_field_policies
from app.auth.role_codes import expand_role_codes_for_lookup, normalize_role_code

_AUDIT_SCOPE_ACTIVE = "active"
_AUDIT_SCOPE_HISTORY = "history"
_AUDIT_SCOPE_ALL = "all"


def _audit_log_select(model, *, storage_scope: str):
    return select(
        model.id.label("id"),
        model.event_type.label("event_type"),
        model.entity_code.label("entity_code"),
        model.entity_id.label("entity_id"),
        model.actor_user_id.label("actor_user_id"),
        model.actor_role.label("actor_role"),
        model.action.label("action"),
        model.result_code.label("result_code"),
        model.ip_address.label("ip_address"),
        model.detail.label("detail"),
        model.message.label("message"),
        model.occurred_at.label("occurred_at"),
        literal(storage_scope.upper()).label("storage_scope"),
    )


def _effective_audit_scope(storage_scope: str | None) -> str:
    normalized = (storage_scope or _AUDIT_SCOPE_ALL).strip().lower()
    if normalized in {_AUDIT_SCOPE_ACTIVE, _AUDIT_SCOPE_HISTORY, _AUDIT_SCOPE_ALL}:
        return normalized
    return _AUDIT_SCOPE_ALL


async def list_audit_logs(
    db: AsyncSession,
    *,
    page: int = 1,
    size: int = 20,
    event_type: str | None = None,
    entity_code: str | None = None,
    entity_id: int | None = None,
    action: str | None = None,
    actor_user_id: int | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    storage_scope: str = _AUDIT_SCOPE_ALL,
) -> tuple[Sequence[dict[str, Any]], int]:
    scope = _effective_audit_scope(storage_scope)
    selects = []
    if scope in {_AUDIT_SCOPE_ACTIVE, _AUDIT_SCOPE_ALL}:
        selects.append(_audit_log_select(AuditLog, storage_scope=_AUDIT_SCOPE_ACTIVE))
    if scope in {_AUDIT_SCOPE_HISTORY, _AUDIT_SCOPE_ALL}:
        selects.append(_audit_log_select(AuditLogHistory, storage_scope=_AUDIT_SCOPE_HISTORY))
    if not selects:
        return [], 0

    audit_rows = selects[0].subquery() if len(selects) == 1 else union_all(*selects).subquery()
    stmt = select(audit_rows)
    if event_type:
        stmt = stmt.where(audit_rows.c.event_type == event_type)
    if entity_code:
        stmt = stmt.where(audit_rows.c.entity_code == entity_code)
    if entity_id is not None:
        stmt = stmt.where(audit_rows.c.entity_id == entity_id)
    if action:
        stmt = stmt.where(audit_rows.c.action == action)
    if actor_user_id is not None:
        stmt = stmt.where(audit_rows.c.actor_user_id == actor_user_id)
    if since:
        stmt = stmt.where(audit_rows.c.occurred_at >= since)
    if until:
        stmt = stmt.where(audit_rows.c.occurred_at <= until)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        stmt.order_by(audit_rows.c.occurred_at.desc(), audit_rows.c.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = (await db.execute(stmt)).mappings().all()
    return [dict(row) for row in rows], total


async def list_role_policies(
    db: AsyncSession,
    role_code: str | None = None,
) -> Sequence[dict[str, Any]]:
    normalized_role_code = normalize_role_code(role_code)
    defaults = {
        (
            normalize_role_code(row["role_code"]),
            row["entity_code"],
            row["field_name"],
        ): {
            **dict(row),
            "role_code": normalize_role_code(row["role_code"]),
        }
        for row in iter_default_role_field_policies()
        if normalized_role_code is None
        or normalize_role_code(row["role_code"]) == normalized_role_code
    }
    stmt = select(RoleFieldPolicy)
    if normalized_role_code:
        stmt = stmt.where(
            RoleFieldPolicy.role_code.in_(
                expand_role_codes_for_lookup([normalized_role_code])
            )
        )
    rows = (await db.execute(stmt)).scalars().all()
    for row in rows:
        canonical_role_code = normalize_role_code(row.role_code)
        defaults[(canonical_role_code, row.entity_code, row.field_name)] = {
            "id": row.id,
            "role_code": canonical_role_code,
            "entity_code": row.entity_code,
            "field_name": row.field_name,
            "can_read": row.can_read,
            "can_write": row.can_write,
            "mask_strategy": row.mask_strategy,
        }

    result: list[dict[str, Any]] = []
    for index, key in enumerate(sorted(defaults)):
        payload = dict(defaults[key])
        payload.setdefault("id", -(index + 1))
        result.append(payload)
    return result
