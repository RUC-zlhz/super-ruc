"""auth 闭环 happy-path：微信 mock 登录 → 绑定学号 → /me 返回绑定态。

涉及：FR-018（enrollment_status 默认 ACTIVE）、C-03（后端鉴权）、
WECHAT_MOCK_ENABLED=true（code 直接作为 mock openid）。
"""
from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student


async def test_wx_login_creates_user_and_binds_student(
    client: AsyncClient, db: AsyncSession
) -> None:
    # Arrange: 提前写入学生主档
    db.add(
        Student(
            student_no="2022110101",
            full_name="测试学生A",
            grade_code="2022",
            major_code="CS",
            class_code="CS2201",
        )
    )
    await db.commit()

    # Act: 首次微信登录 + 学号绑定
    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={"code": "wx_code_alpha", "student_no": "2022110101"},
    )

    # Assert: token + 用户信息 + STUDENT 角色
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["token_type"] == "Bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    user = data["user"]
    assert user["student_no"] == "2022110101"
    assert user["display_name"] == "测试学生A"
    assert any(r["code"] == "STUDENT" for r in user["roles"])


async def test_me_returns_current_user(
    client: AsyncClient, db: AsyncSession
) -> None:
    db.add(Student(student_no="2022110102", full_name="测试学生B"))
    await db.commit()
    login_resp = await client.post(
        "/api/v1/auth/wx-login",
        json={"code": "wx_code_beta", "student_no": "2022110102"},
    )
    token = login_resp.json()["data"]["access_token"]

    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["student_no"] == "2022110102"
    assert any(r["code"] == "STUDENT" for r in body["data"]["roles"])


async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_refresh_token_returns_new_access(
    client: AsyncClient, db: AsyncSession
) -> None:
    db.add(Student(student_no="2022110103", full_name="测试学生C"))
    await db.commit()
    login = await client.post(
        "/api/v1/auth/wx-login",
        json={"code": "wx_code_gamma", "student_no": "2022110103"},
    )
    refresh_token = login.json()["data"]["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["access_token"]


async def test_wx_login_without_student_no_still_works(
    client: AsyncClient,
) -> None:
    """首次登录可不传 student_no（后续再绑）。"""
    resp = await client.post(
        "/api/v1/auth/wx-login", json={"code": "wx_code_unbound"}
    )
    assert resp.status_code == 200, resp.text
    user = resp.json()["data"]["user"]
    assert user["student_no"] is None
    # 已授予 STUDENT 角色
    assert any(r["code"] == "STUDENT" for r in user["roles"])


async def test_wx_login_with_unknown_student_no_returns_404(
    client: AsyncClient,
) -> None:
    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={"code": "wx_code_nobody", "student_no": "NOSUCH"},
    )
    assert resp.status_code == 404
