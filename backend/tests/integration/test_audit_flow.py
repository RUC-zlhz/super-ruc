"""audit S4 集成测试：HTTP 查询、归档与角色策略权限矩阵。"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog, AuditLogHistory
from app.auth.models import User, UserRole
from app.core.security import create_token


async def _create_headers(
    db: AsyncSession,
    *,
    work_no: str,
    display_name: str,
    roles: list[str],
) -> tuple[dict[str, str], User]:
    user = User(
        work_no=work_no,
        display_name=display_name,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    for role_code in roles:
        db.add(UserRole(user_id=user.id, role_code=role_code))
    await db.commit()
    await db.refresh(user)
    token = create_token(str(user.id), "access", extra_claims={"roles": roles})
    return {"Authorization": f"Bearer {token}"}, user


async def _create_audit_log(
    db: AsyncSession,
    *,
    event_type: str,
    entity_code: str,
    action: str,
    result_code: str = "SUCCESS",
    occurred_at: datetime | None = None,
    actor_user_id: int | None = None,
    actor_role: str | None = None,
    detail: dict | None = None,
) -> AuditLog:
    row = AuditLog(
        event_type=event_type,
        entity_code=entity_code,
        entity_id=101,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action=action,
        result_code=result_code,
        ip_address="127.0.0.1",
        detail=detail or {"scope": "integration"},
        message=f"{action} message",
        occurred_at=occurred_at or datetime.now(UTC),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def _create_history_log(
    db: AsyncSession,
    *,
    event_type: str,
    entity_code: str,
    action: str,
    result_code: str = "SUCCESS",
    occurred_at: datetime | None = None,
    actor_user_id: int | None = None,
    actor_role: str | None = None,
) -> AuditLogHistory:
    row = AuditLogHistory(
        id=9001,
        event_type=event_type,
        entity_code=entity_code,
        entity_id=202,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action=action,
        result_code=result_code,
        ip_address="127.0.0.1",
        detail={"scope": "history"},
        message=f"{action} history",
        occurred_at=occurred_at or datetime.now(UTC) - timedelta(days=400),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def test_audit_logs_list_supports_scope_filters_and_viewer_roles(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    admin_headers, admin_user = await _create_headers(
        db,
        work_no="A9001",
        display_name="Audit Admin",
        roles=["SUPER_ADMIN"],
    )
    leader_headers, leader_user = await _create_headers(
        db,
        work_no="A9002",
        display_name="Audit Leader",
        roles=["COLLEGE_LEADER"],
    )
    counselor_headers, _ = await _create_headers(
        db,
        work_no="A9003",
        display_name="Audit Counselor",
        roles=["COUNSELOR"],
    )

    active_log = await _create_audit_log(
        db,
        event_type="REQUEST",
        entity_code="REQUEST",
        action="READ_DETAIL",
        actor_user_id=admin_user.id,
        actor_role="SUPER_ADMIN",
        detail={"scope": "active"},
    )
    history_log = await _create_history_log(
        db,
        event_type="EXPORT",
        entity_code="STUDENT",
        action="EXPORT_STUDENTS",
        actor_user_id=leader_user.id,
        actor_role="COLLEGE_LEADER",
    )

    anonymous = await client.get("/api/v1/admin/audit-logs")
    assert anonymous.status_code == 401

    forbidden = await client.get(
        "/api/v1/admin/audit-logs",
        headers=counselor_headers,
    )
    assert forbidden.status_code == 403

    history_only = await client.get(
        "/api/v1/admin/audit-logs",
        params={"storage_scope": "history", "action": "EXPORT_STUDENTS"},
        headers=leader_headers,
    )
    assert history_only.status_code == 200, history_only.text
    history_items = history_only.json()["data"]["items"]
    assert len(history_items) == 1
    assert history_items[0]["id"] == history_log.id
    assert history_items[0]["storage_scope"] == "HISTORY"

    merged = await client.get(
        "/api/v1/admin/audit-logs",
        params={"storage_scope": "all", "size": 10},
        headers=admin_headers,
    )
    assert merged.status_code == 200, merged.text
    payload = merged.json()["data"]
    ids = {item["id"] for item in payload["items"]}
    scopes = {item["storage_scope"] for item in payload["items"]}
    assert active_log.id in ids
    assert history_log.id in ids
    assert {"ACTIVE", "HISTORY"}.issubset(scopes)
    assert payload["meta"]["total"] >= 2


async def test_audit_archive_endpoint_moves_expired_logs_and_restricts_roles(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    admin_headers, _ = await _create_headers(
        db,
        work_no="A9101",
        display_name="Archive Admin",
        roles=["SUPER_ADMIN"],
    )
    leader_headers, _ = await _create_headers(
        db,
        work_no="A9102",
        display_name="Archive Leader",
        roles=["COLLEGE_LEADER"],
    )

    old_log = await _create_audit_log(
        db,
        event_type="PROFILE",
        entity_code="STUDENT_PROFILE",
        action="EXPORT_SNAPSHOT",
        occurred_at=datetime.now(UTC) - timedelta(days=240),
    )
    await _create_audit_log(
        db,
        event_type="PROFILE",
        entity_code="STUDENT_PROFILE",
        action="READ_DETAIL",
    )

    anonymous = await client.post("/api/v1/admin/audit-logs/archive")
    assert anonymous.status_code == 401

    forbidden = await client.post(
        "/api/v1/admin/audit-logs/archive",
        headers=leader_headers,
    )
    assert forbidden.status_code == 403

    archived = await client.post(
        "/api/v1/admin/audit-logs/archive",
        params={"retention_days": 180, "batch_size": 1000},
        headers=admin_headers,
    )
    assert archived.status_code == 200, archived.text
    summary = archived.json()["data"]
    assert summary["moved"] >= 1
    assert summary["retention_days"] == 180

    remaining_old = await db.scalar(select(AuditLog).where(AuditLog.id == old_log.id))
    archived_old = await db.scalar(
        select(AuditLogHistory).where(AuditLogHistory.id == old_log.id)
    )
    assert remaining_old is None
    assert archived_old is not None


async def test_role_policies_endpoint_requires_super_admin_and_supports_filter(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    admin_headers, _ = await _create_headers(
        db,
        work_no="A9201",
        display_name="Policy Admin",
        roles=["SUPER_ADMIN"],
    )
    leader_headers, _ = await _create_headers(
        db,
        work_no="A9202",
        display_name="Policy Leader",
        roles=["COLLEGE_LEADER"],
    )

    anonymous = await client.get("/api/v1/admin/role-policies")
    assert anonymous.status_code == 401

    forbidden = await client.get(
        "/api/v1/admin/role-policies",
        headers=leader_headers,
    )
    assert forbidden.status_code == 403

    resp = await client.get(
        "/api/v1/admin/role-policies",
        params={"role_code": "COUNSELOR"},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert items
    assert {item["role_code"] for item in items} == {"COUNSELOR"}
    assert {"can_read", "can_write", "mask_strategy"}.issubset(items[0])
