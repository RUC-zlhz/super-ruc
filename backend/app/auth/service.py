"""auth 业务逻辑：微信登录、学号绑定、教师账号登录、JWT 签发。

微信部分提供两种模式：
1. 真实模式：调用 jscode2session，需 WECHAT_APPID / WECHAT_SECRET
2. Mock 模式：WECHAT_MOCK_ENABLED=true 时，用 code 自身作为 mock openid，便于开发调试
"""
from __future__ import annotations

import logging
from datetime import UTC

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_action
from app.auth import repository as repo
from app.auth.models import User
from app.auth.role_codes import normalize_role_code, normalize_role_codes
from app.auth.schemas import RoleInfo, TokenResponse, UserInfo
from app.core.config import settings
from app.core.exceptions import AuthError, BizError, NotFoundError
from app.core.security import create_token, verify_password

logger = logging.getLogger(__name__)

WX_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


# ---------- 微信 ----------
async def wx_code2session(code: str) -> dict:
    if settings.WECHAT_MOCK_ENABLED:
        # 开发模式：code 直接当作 openid，便于测试
        return {"openid": f"mock_{code}", "unionid": None, "session_key": "mock"}

    if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
        raise BizError("未配置 WECHAT_APPID / WECHAT_SECRET", code=50001, http_status=500)

    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(WX_CODE2SESSION_URL, params=params)
    if resp.status_code != 200:
        raise AuthError(f"微信接口异常 HTTP {resp.status_code}")
    data = resp.json()
    if "errcode" in data and data.get("errcode"):
        raise AuthError(f"微信登录失败：{data.get('errmsg', data)}")
    return data


# ---------- Token 构建 ----------
async def _build_token_response(db: AsyncSession, user: User) -> TokenResponse:
    roles_rows = await repo.list_user_roles(db, user.id)
    role_codes = normalize_role_codes(r.role_code for r in roles_rows)
    claims: dict = {"roles": role_codes}
    if user.student_id:
        claims["sid"] = user.student_id
    access = create_token(str(user.id), "access", extra_claims=claims)
    refresh = create_token(str(user.id), "refresh")
    normalized_roles: list[RoleInfo] = []
    seen_role_scope: set[tuple[str, str | None]] = set()
    for row in roles_rows:
        normalized_code = normalize_role_code(row.role_code)
        if normalized_code is None:
            continue
        dedupe_key = (normalized_code, row.scope_code)
        if dedupe_key in seen_role_scope:
            continue
        seen_role_scope.add(dedupe_key)
        normalized_roles.append(
            RoleInfo(code=normalized_code, scope_code=row.scope_code)
        )
    user_info = UserInfo(
        id=user.id,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        email=user.email,
        work_no=user.work_no,
        student_id=user.student_id,
        student_no=user.student.student_no if user.student else None,
        roles=normalized_roles,
    )
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_info,
    )


# ---------- 登录入口 ----------
async def login_with_wechat(
    db: AsyncSession,
    *,
    code: str,
    student_no: str | None = None,
    ip: str | None = None,
) -> TokenResponse:
    session_data = await wx_code2session(code)
    openid = session_data["openid"]

    user = await repo.get_user_by_openid(db, openid)
    if user is None:
        user = await repo.create_user_from_wechat(
            db, openid=openid, unionid=session_data.get("unionid")
        )
        # 默认授予学生角色；若通过 student_no 绑定成功会保持该角色
        await repo.add_user_role(db, user_id=user.id, role_code="STUDENT")

    # 学号绑定：若本次请求带 student_no 且 user 尚未绑定，尝试绑定
    if student_no and user.student_id is None:
        student = await repo.get_student_by_no(db, student_no)
        if student is None:
            raise NotFoundError(f"学号 {student_no} 未在学生主档中，无法绑定")
        user.student_id = student.id
        user.display_name = student.full_name or user.display_name
        await db.flush()
        await log_action(
            db,
            event_type="AUTH",
            entity_code="USER",
            action="BIND_STUDENT",
            entity_id=user.id,
            actor_user_id=user.id,
            ip_address=ip,
            detail={"student_no": student_no},
            auto_flush=False,
        )

    await repo.update_last_login(db, user)
    await log_action(
        db,
        event_type="AUTH",
        entity_code="USER",
        action="LOGIN_WX",
        entity_id=user.id,
        actor_user_id=user.id,
        ip_address=ip,
        auto_flush=False,
    )
    await db.commit()
    await db.refresh(user)
    return await _build_token_response(db, user)


async def login_with_work_no(
    db: AsyncSession,
    *,
    work_no: str,
    password: str,
    ip: str | None = None,
) -> TokenResponse:
    user = await repo.get_user_by_work_no(db, work_no)
    if user is None or not user.password_hash or not verify_password(password, user.password_hash):
        # 记录失败登录，便于审计
        await log_action(
            db,
            event_type="AUTH",
            entity_code="USER",
            action="LOGIN_PWD",
            result_code="FAIL",
            ip_address=ip,
            detail={"work_no": work_no},
            message="工号或密码错误",
        )
        await db.commit()
        raise AuthError("工号或密码错误")
    if not user.is_active:
        raise AuthError("账号已停用")

    await repo.update_last_login(db, user)
    await log_action(
        db,
        event_type="AUTH",
        entity_code="USER",
        action="LOGIN_PWD",
        entity_id=user.id,
        actor_user_id=user.id,
        ip_address=ip,
        auto_flush=False,
    )
    await db.commit()
    return await _build_token_response(db, user)


async def update_enrollment_status(
    db: AsyncSession,
    student_id: int,
    *,
    status_code: str,
    reason: str | None,
    operator_id: int,
    operator_role: str | None,
) -> None:
    """v1.5 账号生命周期变更 — 写 Student.enrollment_status + 审计。"""
    from datetime import datetime

    from app.auth.models import (
        ENROLLMENT_ACTIVE,
        ENROLLMENT_ARCHIVED,
        ENROLLMENT_GRADUATED,
        ENROLLMENT_SUSPENDED,
        ENROLLMENT_TRANSFERRED,
        Student,
    )

    valid = {
        ENROLLMENT_ACTIVE,
        ENROLLMENT_SUSPENDED,
        ENROLLMENT_TRANSFERRED,
        ENROLLMENT_GRADUATED,
        ENROLLMENT_ARCHIVED,
    }
    if status_code not in valid:
        raise BizError(f"无效的学籍状态：{status_code}", code=40060)

    student = await db.get(Student, student_id)
    if student is None:
        raise NotFoundError("学生不存在")
    before = student.enrollment_status
    student.enrollment_status = status_code
    student.enrollment_status_reason = reason
    student.enrollment_status_updated_at = datetime.now(UTC)
    await log_action(
        db,
        event_type="AUTH",
        entity_code="STUDENT",
        action="ENROLLMENT_STATUS",
        entity_id=student_id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"before": before, "after": status_code, "reason": reason},
        auto_flush=False,
    )
    await db.commit()


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    from app.core.security import decode_token

    try:
        claims = decode_token(refresh_token)
    except Exception as e:
        raise AuthError(f"刷新令牌无效：{e}") from e
    if claims.get("typ") != "refresh":
        raise AuthError("令牌类型错误")
    try:
        user_id = int(claims["sub"])
    except (KeyError, ValueError) as e:
        raise AuthError("令牌主体缺失") from e
    user = await repo.get_user_by_id(db, user_id)
    if user is None or user.deleted_at is not None or not user.is_active:
        raise AuthError("用户不存在或已停用")
    return await _build_token_response(db, user)
