"""Authentication service logic for WeChat login, account binding, and JWT issuance."""
from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_action
from app.auth import repository as repo
from app.auth.bootstrap import INITIAL_ADMIN_PLAIN, INITIAL_ADMIN_WORK_NO
from app.auth.models import User
from app.auth.role_codes import normalize_role_code, normalize_role_codes
from app.auth.schemas import RoleInfo, TokenResponse, UserInfo
from app.core.config import settings
from app.core.exceptions import AuthError, BizError, NotFoundError
from app.core.security import create_token, decrypt_field, hash_password, verify_password

logger = logging.getLogger(__name__)

WX_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"
ROLE_STUDENT = "STUDENT"
ROLE_GUEST = "GUEST"


def _is_initial_admin_password(user: User) -> bool:
    return (
        user.work_no == INITIAL_ADMIN_WORK_NO
        and bool(user.password_hash)
        and verify_password(INITIAL_ADMIN_PLAIN, user.password_hash)
    )


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _is_mock_openid(value: str | None) -> bool:
    return bool(value and value.startswith("mock_"))


def _build_mock_openid(code: str, student_no: str | None = None) -> str:
    if student_no:
        return f"mock_student_{student_no}"
    return f"mock_{code}"


def _claims_token_version(claims: dict) -> int:
    try:
        return int(claims.get("ver", 0))
    except (TypeError, ValueError) as exc:
        raise AuthError("令牌版本无效") from exc


def _validate_student_binding_factor(
    student,
    *,
    full_name: str | None,
    id_card_tail: str | None,
) -> None:
    if not full_name and not id_card_tail:
        raise BizError("绑定学号需填写学生姓名或身份证号后 6 位", code=40072)

    if full_name and full_name != student.full_name.strip():
        raise AuthError("学生绑定信息不匹配")

    if student.id_card_enc:
        if not id_card_tail:
            raise BizError("该学生主档已配置身份证号，绑定时需填写身份证号后 6 位", code=40072)
        raw_id_card = decrypt_field(student.id_card_enc)
        if not raw_id_card or not raw_id_card.endswith(id_card_tail):
            raise AuthError("学生绑定信息不匹配")
        return

    if id_card_tail and not full_name:
        raise BizError("该学生主档未配置身份证号，请填写学生姓名完成绑定", code=40072)


async def wx_code2session(code: str, *, student_no: str | None = None) -> dict:
    if not code or not code.strip():
        raise AuthError("微信登录凭证不能为空")

    if settings.WECHAT_MOCK_ENABLED:
        return {
            "openid": _build_mock_openid(code, student_no),
            "unionid": None,
            "session_key": "mock",
        }

    if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
        raise BizError("未配置 WECHAT_APPID / WECHAT_SECRET", code=50001, http_status=500)

    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(WX_CODE2SESSION_URL, params=params)
    except httpx.RequestError as exc:
        logger.warning("wechat code2session request failed: %s", exc)
        raise BizError(
            "微信登录服务暂不可用，请稍后重试",
            code=50201,
            http_status=502,
        ) from exc
    if resp.status_code != 200:
        logger.warning("wechat code2session returned HTTP %s", resp.status_code)
        raise BizError(
            "微信登录服务暂不可用，请稍后重试",
            code=50201,
            http_status=502,
        )
    try:
        data = resp.json()
    except ValueError as exc:
        logger.warning("wechat code2session returned non-json payload")
        raise BizError(
            "微信登录服务暂不可用，请稍后重试",
            code=50201,
            http_status=502,
        ) from exc

    errcode = data.get("errcode")
    if errcode:
        logger.info(
            "wechat code2session rejected code: errcode=%s errmsg=%s",
            errcode,
            data.get("errmsg"),
        )
        if errcode in {40029, 40163}:
            raise AuthError("微信登录凭证无效或已过期，请重新登录")
        raise AuthError("微信登录失败，请稍后重试")
    if not data.get("openid"):
        logger.warning("wechat code2session response missing openid")
        raise AuthError("微信登录失败，请稍后重试")
    return data


async def build_user_info(db: AsyncSession, user: User) -> UserInfo:
    roles_rows = await repo.list_user_roles(db, user.id)
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
        normalized_roles.append(RoleInfo(code=normalized_code, scope_code=row.scope_code))
    return UserInfo(
        id=user.id,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        email=user.email,
        work_no=user.work_no,
        student_id=user.student_id,
        student_no=user.student.student_no if user.student else None,
        roles=normalized_roles,
        must_change_password=bool(user.must_change_password) or _is_initial_admin_password(user),
    )


async def _build_token_response(db: AsyncSession, user: User) -> TokenResponse:
    roles_rows = await repo.list_user_roles(db, user.id)
    role_codes = normalize_role_codes(r.role_code for r in roles_rows)
    claims: dict = {"roles": role_codes, "ver": user.token_version}
    if user.student_id:
        claims["sid"] = user.student_id
    access = create_token(str(user.id), "access", extra_claims=claims)
    refresh = create_token(str(user.id), "refresh", extra_claims={"ver": user.token_version})
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=await build_user_info(db, user),
    )


async def login_with_wechat(
    db: AsyncSession,
    *,
    code: str,
    student_no: str | None = None,
    full_name: str | None = None,
    id_card_tail: str | None = None,
    ip: str | None = None,
) -> TokenResponse:
    normalized_student_no = _clean_optional(student_no)
    normalized_full_name = _clean_optional(full_name)
    normalized_id_card_tail = _clean_optional(id_card_tail)
    guest_login_requested = normalized_student_no is None
    if guest_login_requested and not settings.WECHAT_GUEST_LOGIN_ENABLED:
        raise BizError(
            "访客登录仅在开发模式开关开启时可用，请填写学号完成绑定",
            code=40320,
            http_status=403,
        )
    session_data = await wx_code2session(code, student_no=normalized_student_no)
    openid = session_data["openid"]

    user = await repo.get_user_by_openid(db, openid)
    if user is not None and not user.is_active:
        await log_action(
            db,
            event_type="AUTH",
            entity_code="USER",
            action="LOGIN_WX",
            entity_id=user.id,
            actor_user_id=user.id,
            result_code="FAIL",
            ip_address=ip,
            message="账号已停用",
        )
        await db.commit()
        raise AuthError("账号已停用")

    student = None
    if normalized_student_no:
        student = await repo.get_student_by_no(db, normalized_student_no)
        if student is None:
            raise NotFoundError(f"学号 {normalized_student_no} 未在学生主档中，无法绑定")
        _validate_student_binding_factor(
            student,
            full_name=normalized_full_name,
            id_card_tail=normalized_id_card_tail,
        )
        bound_user = await repo.get_user_by_student_id(db, student.id)
        if bound_user is not None and (user is None or bound_user.id != user.id):
            if settings.WECHAT_MOCK_ENABLED and user is None and _is_mock_openid(bound_user.openid):
                bound_user.openid = openid
                bound_user.unionid = session_data.get("unionid")
                bound_user.token_version += 1
                await db.flush()
                user = bound_user
            else:
                raise BizError("该学生已绑定其他微信账号，请联系学院老师处理", code=40901, http_status=409)

    if user is None:
        user = await repo.create_user_from_wechat(
            db, openid=openid, unionid=session_data.get("unionid")
        )

    if user.student_id is None:
        if student is not None:
            user.student_id = student.id
            user.student = student
            user.display_name = student.full_name or user.display_name
            user.token_version += 1
            await db.flush()
            await repo.ensure_user_role(db, user_id=user.id, role_code=ROLE_STUDENT)
            await repo.remove_user_role(db, user_id=user.id, role_code=ROLE_GUEST)
            await log_action(
                db,
                event_type="AUTH",
                entity_code="USER",
                action="BIND_STUDENT",
                entity_id=user.id,
                actor_user_id=user.id,
                ip_address=ip,
                detail={"student_no": normalized_student_no},
                auto_flush=False,
            )
        else:
            if normalized_full_name or normalized_id_card_tail:
                raise BizError("绑定学生时请同时填写学号", code=40072)
            await repo.ensure_user_role(db, user_id=user.id, role_code=ROLE_GUEST)
    else:
        if student is not None and user.student_id != student.id:
            raise BizError("当前微信已绑定其他学号，不能重复绑定", code=40902, http_status=409)
        await repo.ensure_user_role(db, user_id=user.id, role_code=ROLE_STUDENT)
        await repo.remove_user_role(db, user_id=user.id, role_code=ROLE_GUEST)

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


async def change_password(
    db: AsyncSession,
    *,
    user_id: int,
    old_password: str,
    new_password: str,
    ip: str | None = None,
) -> UserInfo:
    user = await repo.get_user_by_id(db, user_id)
    if user is None or user.deleted_at is not None:
        raise AuthError("用户不存在")
    if not user.password_hash or not verify_password(old_password, user.password_hash):
        await log_action(
            db,
            event_type="AUTH",
            entity_code="USER",
            action="CHANGE_PASSWORD",
            entity_id=user_id,
            actor_user_id=user_id,
            result_code="FAIL",
            ip_address=ip,
            message="旧密码错误",
            auto_flush=False,
        )
        await db.commit()
        raise AuthError("旧密码错误")
    if verify_password(new_password, user.password_hash):
        raise BizError("新密码不能与旧密码相同", code=40070)
    if user.work_no == INITIAL_ADMIN_WORK_NO and new_password == INITIAL_ADMIN_PLAIN:
        raise BizError("新密码不能继续使用默认管理员密码", code=40071)

    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    await log_action(
        db,
        event_type="AUTH",
        entity_code="USER",
        action="CHANGE_PASSWORD",
        entity_id=user.id,
        actor_user_id=user.id,
        ip_address=ip,
        auto_flush=False,
    )
    await db.commit()
    await db.refresh(user)
    return await build_user_info(db, user)


async def logout(
    db: AsyncSession,
    *,
    user_id: int,
    refresh_token: str | None = None,
    ip: str | None = None,
) -> None:
    user = await repo.get_user_by_id(db, user_id)
    if user is None or user.deleted_at is not None:
        raise AuthError("用户不存在")
    user.token_version += 1
    await log_action(
        db,
        event_type="AUTH",
        entity_code="USER",
        action="LOGOUT",
        entity_id=user.id,
        actor_user_id=user.id,
        ip_address=ip,
        detail={
            "refresh_token_present": bool(refresh_token),
            "revoked_account_tokens": True,
        },
        auto_flush=False,
    )
    await db.commit()


async def update_enrollment_status(
    db: AsyncSession,
    student_id: int,
    *,
    status_code: str,
    reason: str | None,
    operator_id: int,
    operator_role: str | None,
) -> None:
    """Update student enrollment lifecycle state."""
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
        raise BizError(f"学籍状态非法：{status_code}", code=40060)

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
    except Exception as exc:  # noqa: BLE001
        raise AuthError(f"刷新令牌无效：{exc}") from exc
    if claims.get("typ") != "refresh":
        raise AuthError("令牌类型错误")
    try:
        user_id = int(claims["sub"])
    except (KeyError, ValueError) as exc:
        raise AuthError("令牌主体无效") from exc

    user = await repo.get_user_by_id(db, user_id)
    if user is None or user.deleted_at is not None or not user.is_active:
        raise AuthError("用户不存在或已停用")
    if _claims_token_version(claims) != user.token_version:
        raise AuthError("刷新令牌版本已失效，请重新登录")
    return await _build_token_response(db, user)
