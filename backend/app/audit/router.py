"""审计路由 — FR-012, FR-013。"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.audit import repository as repo
from app.audit import schemas
from app.audit import service as audit_service
from app.core.dependencies import CurrentUserDep, DBDep, require_role
from app.core.response import ApiResponse, PageMeta, Paginated, ok

router = APIRouter(prefix="/admin", tags=["audit"])

# 仅超级管理员/学院领导可查看审计日志
_AuditViewerRole = require_role("SUPER_ADMIN", "COLLEGE_LEADER")


@router.get("/audit-logs", response_model=ApiResponse[Paginated[schemas.AuditLogOut]])
async def list_audit_logs(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_AuditViewerRole)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    event_type: str | None = None,
    entity_code: str | None = None,
    actor_user_id: int | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> ApiResponse[Paginated[schemas.AuditLogOut]]:
    rows, total = await repo.list_audit_logs(
        db,
        page=page,
        size=size,
        event_type=event_type,
        entity_code=entity_code,
        actor_user_id=actor_user_id,
        since=since,
        until=until,
    )
    return ok(
        Paginated[schemas.AuditLogOut](
            items=[schemas.AuditLogOut.model_validate(r) for r in rows],
            meta=PageMeta(page=page, size=size, total=total),
        )
    )


@router.post(
    "/audit-logs/archive",
    response_model=ApiResponse[dict],
    summary="v1.5 手动触发：将超期日志搬迁至冷备份表",
)
async def archive_audit_logs(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(require_role("SUPER_ADMIN"))],
    retention_days: int = Query(
        default=audit_service.DEFAULT_RETENTION_DAYS, ge=30, le=3650,
        description="留存天数（默认 180 天 ≈ 1 学期）",
    ),
    batch_size: int = Query(default=1000, ge=100, le=10000),
) -> ApiResponse[dict]:
    summary = await audit_service.archive_expired_logs(
        db, retention_days=retention_days, batch_size=batch_size
    )
    return ok(summary)


@router.get("/role-policies", response_model=ApiResponse[list[schemas.RoleFieldPolicyOut]])
async def list_policies(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(require_role("SUPER_ADMIN"))],
    role_code: str | None = None,
) -> ApiResponse[list[schemas.RoleFieldPolicyOut]]:
    rows = await repo.list_role_policies(db, role_code=role_code)
    return ok([schemas.RoleFieldPolicyOut.model_validate(r) for r in rows])
