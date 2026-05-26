"""Integration tests for auth happy path, mock WeChat login, and token lifecycle."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.models import Student, User, UserRole
from app.core.exceptions import AuthError, BizError


class _FakeWechatResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _FakeWechatClient:
    def __init__(self, response: _FakeWechatResponse) -> None:
        self.response = response

    async def __aenter__(self) -> _FakeWechatClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def get(self, *_: object, **__: object) -> _FakeWechatResponse:
        return self.response


def _mock_openid(student_no: str | None = None, *, code: str | None = None) -> str:
    if student_no:
        return f"mock_student_{student_no}"
    assert code is not None
    return f"mock_{code}"


async def test_wx_login_creates_user_and_binds_student(
    client: AsyncClient, db: AsyncSession
) -> None:
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

    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": "wx_code_alpha",
            "student_no": "2022110101",
            "full_name": "测试学生A",
        },
    )

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
    assert any(role["code"] == "STUDENT" for role in user["roles"])


async def test_me_returns_current_user(
    client: AsyncClient, db: AsyncSession
) -> None:
    db.add(Student(student_no="2022110102", full_name="测试学生B"))
    await db.commit()
    login_resp = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": "wx_code_beta",
            "student_no": "2022110102",
            "full_name": "测试学生B",
        },
    )
    token = login_resp.json()["data"]["access_token"]

    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["student_no"] == "2022110102"
    assert any(role["code"] == "STUDENT" for role in body["data"]["roles"])


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
        json={
            "code": "wx_code_gamma",
            "student_no": "2022110103",
            "full_name": "测试学生C",
        },
    )
    refresh_token = login.json()["data"]["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["access_token"]


async def test_default_admin_login_requires_password_change(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"work_no": "admin", "password": "admin123"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 0
    user = body["data"]["user"]
    assert user["work_no"] == "admin"
    assert user["must_change_password"] is True
    assert any(role["code"] == "SUPER_ADMIN" for role in user["roles"])


async def test_change_password_clears_default_admin_reminder(client: AsyncClient) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"work_no": "admin", "password": "admin123"},
    )
    token = login.json()["data"]["access_token"]

    change = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"old_password": "admin123", "new_password": "Admin12345"},
    )

    assert change.status_code == 200, change.text
    assert change.json()["data"]["must_change_password"] is False

    old_login = await client.post(
        "/api/v1/auth/login",
        json={"work_no": "admin", "password": "admin123"},
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"work_no": "admin", "password": "Admin12345"},
    )
    assert new_login.status_code == 200, new_login.text
    assert new_login.json()["data"]["user"]["must_change_password"] is False


async def test_wx_login_without_student_no_returns_guest_session(
    client: AsyncClient,
) -> None:
    resp = await client.post(
        "/api/v1/auth/wx-login", json={"code": "wx_code_unbound"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 0
    user = body["data"]["user"]
    assert user["student_id"] is None
    assert user["student_no"] is None
    assert any(role["code"] == "GUEST" for role in user["roles"])
    assert not any(role["code"] == "STUDENT" for role in user["roles"])


async def test_wx_login_without_student_no_requires_guest_dev_switch(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service.settings, "WECHAT_GUEST_LOGIN_ENABLED", False)

    resp = await client.post(
        "/api/v1/auth/wx-login", json={"code": "wx_code_guest_disabled"}
    )

    assert resp.status_code == 403


async def test_bound_wx_login_without_student_no_works_when_guest_disabled(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service.settings, "WECHAT_GUEST_LOGIN_ENABLED", False)

    async def _bound_code2session(_code: str, *, student_no: str | None = None) -> dict:
        assert student_no is None
        return {"openid": "wx_bound_openid", "unionid": "wx_bound_unionid"}

    monkeypatch.setattr(service, "wx_code2session", _bound_code2session)
    student = Student(student_no="2022110110", full_name="测试学生J")
    db.add(student)
    await db.flush()
    user = User(openid="wx_bound_openid", display_name="测试学生J", student_id=student.id)
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_code="STUDENT"))
    await db.commit()

    resp = await client.post("/api/v1/auth/wx-login", json={"code": "wx_code_bound"})

    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["user"]["student_no"] == "2022110110"
    assert not any(role["code"] == "GUEST" for role in data["user"]["roles"])


async def test_guest_wx_login_can_bind_student_later(
    client: AsyncClient, db: AsyncSession
) -> None:
    db.add(Student(student_no="2022110104", full_name="测试学生D"))
    await db.commit()

    guest_resp = await client.post(
        "/api/v1/auth/wx-login", json={"code": "wx_code_guest_bind"}
    )
    assert guest_resp.status_code == 200, guest_resp.text
    assert guest_resp.json()["data"]["user"]["student_id"] is None

    bind_resp = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": "wx_code_guest_bind",
            "student_no": "2022110104",
            "full_name": "测试学生D",
        },
    )

    assert bind_resp.status_code == 200, bind_resp.text
    user = bind_resp.json()["data"]["user"]
    assert user["student_no"] == "2022110104"
    assert user["display_name"] == "测试学生D"
    assert any(role["code"] == "STUDENT" for role in user["roles"])
    assert not any(role["code"] == "GUEST" for role in user["roles"])


async def test_wx_login_rejects_student_no_only_binding(
    client: AsyncClient, db: AsyncSession
) -> None:
    db.add(Student(student_no="2022110105", full_name="测试学生E"))
    await db.commit()

    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={"code": "wx_code_student_no_only", "student_no": "2022110105"},
    )

    assert resp.status_code == 400


async def test_wx_login_allows_same_student_to_sign_in_again_in_mock_mode(
    client: AsyncClient, db: AsyncSession
) -> None:
    db.add(Student(student_no="2022110106", full_name="测试学生F"))
    await db.commit()

    first = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": "wx_code_bind_first",
            "student_no": "2022110106",
            "full_name": "测试学生F",
        },
    )
    assert first.status_code == 200, first.text

    second = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": "wx_code_bind_second",
            "student_no": "2022110106",
            "full_name": "测试学生F",
        },
    )

    assert second.status_code == 200, second.text
    user = second.json()["data"]["user"]
    assert user["student_no"] == "2022110106"
    row = (
        await db.execute(select(User).where(User.openid == _mock_openid("2022110106")))
    ).scalar_one()
    assert row.student_id is not None


async def test_wx_login_rebinds_legacy_mock_student_binding_to_stable_openid(
    client: AsyncClient, db: AsyncSession
) -> None:
    student = Student(student_no="2022110109", full_name="测试学生I")
    db.add(student)
    await db.flush()
    db.add(User(openid="mock_legacy_code", display_name="legacy", student_id=student.id))
    await db.commit()

    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": "wx_code_rebind_legacy",
            "student_no": "2022110109",
            "full_name": "测试学生I",
        },
    )

    assert resp.status_code == 200, resp.text
    rebound = (
        await db.execute(select(User).where(User.openid == _mock_openid("2022110109")))
    ).scalar_one()
    assert rebound.student_id == student.id


async def test_wx_login_rejects_inactive_account(
    client: AsyncClient, db: AsyncSession
) -> None:
    db.add(Student(student_no="2022110107", full_name="测试学生G"))
    await db.commit()
    login = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": "wx_code_inactive",
            "student_no": "2022110107",
            "full_name": "测试学生G",
        },
    )
    assert login.status_code == 200, login.text
    user = (
        await db.execute(select(User).where(User.openid == _mock_openid("2022110107")))
    ).scalar_one()
    user.is_active = False
    await db.commit()

    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": "wx_code_inactive",
            "student_no": "2022110107",
            "full_name": "测试学生G",
        },
    )

    assert resp.status_code == 401


async def test_logout_revokes_refresh_and_access_token(
    client: AsyncClient, db: AsyncSession
) -> None:
    db.add(Student(student_no="2022110108", full_name="测试学生H"))
    await db.commit()
    login = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": "wx_code_logout",
            "student_no": "2022110108",
            "full_name": "测试学生H",
        },
    )
    assert login.status_code == 200, login.text
    data = login.json()["data"]
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    logout = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert logout.status_code == 200, logout.text

    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me.status_code == 401

    refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh.status_code == 401


async def test_wx_login_with_unknown_student_no_returns_404(
    client: AsyncClient,
) -> None:
    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={"code": "wx_code_nobody", "student_no": "NOSUCH"},
    )
    assert resp.status_code == 404


async def test_wx_code2session_requires_real_secret_when_mock_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service.settings, "WECHAT_MOCK_ENABLED", False)
    monkeypatch.setattr(service.settings, "WECHAT_APPID", "wx_test")
    monkeypatch.setattr(service.settings, "WECHAT_SECRET", "")

    with pytest.raises(BizError, match="WECHAT_APPID / WECHAT_SECRET"):
        await service.wx_code2session("wx_code_missing_secret")


async def test_wx_code2session_maps_wechat_invalid_code_to_auth_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service.settings, "WECHAT_MOCK_ENABLED", False)
    monkeypatch.setattr(service.settings, "WECHAT_APPID", "wx_test")
    monkeypatch.setattr(service.settings, "WECHAT_SECRET", "secret")
    response = _FakeWechatResponse(
        200,
        {"errcode": 40029, "errmsg": "invalid code"},
    )
    monkeypatch.setattr(
        service.httpx,
        "AsyncClient",
        lambda **_: _FakeWechatClient(response),
    )

    with pytest.raises(AuthError, match="微信登录凭证无效或已过期"):
        await service.wx_code2session("wx_code_bad")


async def test_wx_code2session_returns_official_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(service.settings, "WECHAT_MOCK_ENABLED", False)
    monkeypatch.setattr(service.settings, "WECHAT_APPID", "wx_test")
    monkeypatch.setattr(service.settings, "WECHAT_SECRET", "secret")
    response = _FakeWechatResponse(
        200,
        {
            "openid": "openid_real",
            "unionid": "unionid_real",
            "session_key": "session_key_real",
        },
    )
    monkeypatch.setattr(
        service.httpx,
        "AsyncClient",
        lambda **_: _FakeWechatClient(response),
    )

    data = await service.wx_code2session("wx_code_real")

    assert data["openid"] == "openid_real"
    assert data["unionid"] == "unionid_real"
    assert data["session_key"] == "session_key_real"
