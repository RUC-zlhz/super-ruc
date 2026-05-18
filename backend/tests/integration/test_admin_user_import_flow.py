"""Backend-account bulk import flow and permission boundaries."""
from __future__ import annotations

import io
import json

from httpx import AsyncClient
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.auth.models import User, UserRole
from app.core.security import create_token, hash_password, verify_password


def _build_admin_user_xlsx(rows: list[dict]) -> bytes:
    headers = [
        "work_no",
        "display_name",
        "email",
        "role_code",
        "scope_type",
        "scope_code",
        "is_active",
    ]
    wb = Workbook()
    ws = wb.active
    ws.title = "admin_users"
    ws.append(headers)
    for row in rows:
        ws.append([row.get(header) for header in headers])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _build_xlsx_with_header(headers: list[str], rows: list[dict]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append([row.get(header) for header in headers])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


async def _create_headers(
    db: AsyncSession,
    *,
    role_code: str,
    work_no: str,
    scope_code: str | None = None,
) -> dict[str, str]:
    user = User(work_no=work_no, display_name=work_no, is_active=True)
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_code=role_code, scope_code=scope_code))
    await db.commit()
    token = create_token(str(user.id), "access", extra_claims={"roles": [role_code], "ver": 0})
    return {"Authorization": f"Bearer {token}"}


async def _preview(
    client: AsyncClient,
    headers: dict[str, str],
    rows: list[dict],
) -> dict:
    resp = await client.post(
        "/api/v1/admin/users/import-preview",
        headers=headers,
        files={
            "file": (
                "admin-users.xlsx",
                _build_admin_user_xlsx(rows),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _commit(client: AsyncClient, headers: dict[str, str], batch_id: int) -> dict:
    resp = await client.post(
        "/api/v1/admin/users/import-commit",
        headers=headers,
        json={"batch_id": batch_id},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def test_super_admin_import_creates_account_and_requires_password_change(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    headers = await _create_headers(db, role_code="SUPER_ADMIN", work_no="SA-IMPORTER")
    preview = await _preview(
        client,
        headers,
        [
            {
                "work_no": "T9001",
                "display_name": "批量辅导员",
                "email": "teacher9001@example.edu.cn",
                "role_code": "COUNSELOR",
                "scope_type": "GLOBAL",
                "is_active": "true",
            }
        ],
    )
    assert preview["batch"]["fatal_rows"] == 0

    commit = await _commit(client, headers, preview["batch"]["id"])
    assert commit["batch"]["status"] == "COMMITTED"
    assert commit["credentials"][0]["work_no"] == "T9001"
    initial_password = commit["credentials"][0]["initial_password"]

    user = (await db.execute(select(User).where(User.work_no == "T9001"))).scalar_one()
    assert user.must_change_password is True
    assert verify_password(initial_password, user.password_hash or "")

    login = await client.post(
        "/api/v1/auth/login",
        json={"work_no": "T9001", "password": initial_password},
    )
    assert login.status_code == 200, login.text
    assert login.json()["data"]["user"]["must_change_password"] is True
    token = login.json()["data"]["access_token"]

    change = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"old_password": initial_password, "new_password": "Teacher9001!"},
    )
    assert change.status_code == 200, change.text
    assert change.json()["data"]["must_change_password"] is False


async def test_college_leader_and_l3_role_import_boundaries(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    leader_headers = await _create_headers(db, role_code="COLLEGE_LEADER", work_no="LEADER-IMPORTER")
    leader_preview = await _preview(
        client,
        leader_headers,
        [
            {
                "work_no": "T9101",
                "display_name": "L3 老师",
                "role_code": "COUNSELOR",
                "scope_type": "GLOBAL",
                "is_active": "true",
            },
            {
                "work_no": "T9102",
                "display_name": "非法领导",
                "role_code": "COLLEGE_LEADER",
                "scope_type": "GLOBAL",
                "is_active": "true",
            },
        ],
    )
    assert leader_preview["batch"]["fatal_rows"] == 1
    assert any(row["field_name"] == "role_code" for row in leader_preview["rows"])

    l3_headers = await _create_headers(db, role_code="COUNSELOR", work_no="L3-IMPORTER")
    l3_preview = await _preview(
        client,
        l3_headers,
        [
            {
                "work_no": "T9201",
                "display_name": "无范围骨干",
                "role_code": "CLASS_MONITOR",
                "scope_type": "GLOBAL",
                "is_active": "true",
            },
            {
                "work_no": "T9202",
                "display_name": "带范围骨干",
                "role_code": "CLASS_MONITOR",
                "scope_type": "GRADE",
                "scope_code": "2024",
                "is_active": "true",
            },
            {
                "work_no": "T9203",
                "display_name": "非法教师",
                "role_code": "HEAD_TEACHER",
                "scope_type": "CLASS",
                "scope_code": "CS2401",
                "is_active": "true",
            },
        ],
    )
    assert l3_preview["batch"]["fatal_rows"] == 2
    valid_row = next(row for row in l3_preview["rows"] if row["work_no"] == "T9202")
    assert valid_row["scope_code"] == "GRADE:2024"


async def test_l4_and_student_cannot_access_import_endpoints(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    l4_headers = await _create_headers(db, role_code="CLASS_MONITOR", work_no="L4-IMPORTER")
    student_headers = await _create_headers(db, role_code="STUDENT", work_no="STU-IMPORTER")
    for headers in (l4_headers, student_headers):
        resp = await client.get(
            "/api/v1/admin/users/import-template?format=csv",
            headers=headers,
        )
        assert resp.status_code == 403


async def test_preview_marks_validation_failures_as_fatal(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    headers = await _create_headers(db, role_code="SUPER_ADMIN", work_no="SA-VALIDATOR")
    preview = await _preview(
        client,
        headers,
        [
            {
                "work_no": "DUP001",
                "display_name": "重复 1",
                "role_code": "COUNSELOR",
                "scope_type": "GLOBAL",
                "is_active": "true",
            },
            {
                "work_no": "DUP001",
                "display_name": "重复 2",
                "role_code": "COUNSELOR",
                "scope_type": "GLOBAL",
                "is_active": "true",
            },
            {
                "work_no": "BADROLE",
                "display_name": "未知角色",
                "role_code": "NO_SUCH_ROLE",
                "scope_type": "GLOBAL",
                "is_active": "true",
            },
            {
                "work_no": "BADSCOPE",
                "display_name": "非法范围",
                "role_code": "COUNSELOR",
                "scope_type": "CLASS",
                "is_active": "true",
            },
            {
                "work_no": "",
                "display_name": "缺工号",
                "role_code": "COUNSELOR",
                "scope_type": "GLOBAL",
                "is_active": "true",
            },
        ],
    )
    assert preview["batch"]["fatal_rows"] == 4
    assert preview["batch"]["status"] == "FAILED"

    bad_header = _build_xlsx_with_header(
        [
            "work_no",
            "display_name",
            "email",
            "role_code",
            "scope_type",
            "scope_code",
            "is_active",
            "password",
        ],
        [],
    )
    resp = await client.post(
        "/api/v1/admin/users/import-preview",
        headers=headers,
        files={"file": ("admin-users.xlsx", bad_header, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["batch"]["fatal_rows"] == 1
    assert resp.json()["data"]["rows"][0]["field_name"] == "password"


async def test_existing_account_import_is_idempotent_and_does_not_reset_password(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    headers = await _create_headers(db, role_code="SUPER_ADMIN", work_no="SA-IDEMPOTENT")
    existing = User(
        work_no="T9301",
        display_name="已有账号",
        password_hash=hash_password("OldPass9301!"),
        must_change_password=False,
        is_active=True,
    )
    db.add(existing)
    await db.flush()
    db.add(UserRole(user_id=existing.id, role_code="COUNSELOR"))
    await db.commit()

    preview = await _preview(
        client,
        headers,
        [
            {
                "work_no": "T9301",
                "display_name": "已有账号新名",
                "role_code": "CLASS_MONITOR",
                "scope_type": "CLASS",
                "scope_code": "CS2401",
                "is_active": "true",
            }
        ],
    )
    assert preview["batch"]["fatal_rows"] == 0
    assert preview["batch"]["warn_rows"] == 1

    commit = await _commit(client, headers, preview["batch"]["id"])
    assert commit["credentials"] == []
    assert commit["batch"]["existing_rows"] == 1
    assert commit["batch"]["role_granted_rows"] == 1

    refreshed = (await db.execute(select(User).where(User.work_no == "T9301"))).scalar_one()
    assert refreshed.display_name == "已有账号"
    assert verify_password("OldPass9301!", refreshed.password_hash or "")
    role = (
        await db.execute(
            select(UserRole).where(
                UserRole.user_id == refreshed.id,
                UserRole.role_code == "CLASS_MONITOR",
                UserRole.scope_code == "CLASS:CS2401",
            )
        )
    ).scalar_one_or_none()
    assert role is not None


async def test_import_audit_does_not_store_plain_initial_password(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    headers = await _create_headers(db, role_code="SUPER_ADMIN", work_no="SA-AUDIT")
    preview = await _preview(
        client,
        headers,
        [
            {
                "work_no": "T9401",
                "display_name": "审计账号",
                "role_code": "HEAD_TEACHER",
                "scope_type": "GLOBAL",
                "is_active": "true",
            }
        ],
    )
    commit = await _commit(client, headers, preview["batch"]["id"])
    password = commit["credentials"][0]["initial_password"]

    logs = (await db.execute(select(AuditLog))).scalars().all()
    payload = "\n".join(
        f"{log.message or ''}\n{json.dumps(log.detail or {}, ensure_ascii=False)}"
        for log in logs
    )
    assert password not in payload
