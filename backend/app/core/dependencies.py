"""FastAPI 依赖：鉴权、角色校验、Session。

权限判定必须在后端执行（C-03）。所有 `require_role` 失败返回 403。
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.role_codes import normalize_role_codes
from app.core.database import get_db
from app.core.exceptions import AuthError, PermissionError
from app.core.security import decode_token

_bearer = HTTPBearer(auto_error=False)


class CurrentUser:
    """请求上下文中解析出的当前用户（从 JWT payload）。"""

    __slots__ = ("user_id", "student_id", "roles", "raw_claims")

    def __init__(
        self,
        user_id: int,
        student_id: int | None,
        roles: list[str],
        raw_claims: dict,
    ) -> None:
        self.user_id = user_id
        self.student_id = student_id
        self.roles = roles
        self.raw_claims = raw_claims

    def has_role(self, *required: str) -> bool:
        return bool(set(self.roles) & set(normalize_role_codes(required)))

    def __repr__(self) -> str:
        return f"CurrentUser(user_id={self.user_id}, roles={self.roles})"


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise AuthError("缺少 Authorization Bearer token")
    try:
        claims = decode_token(credentials.credentials)
    except Exception as e:  # jose.JWTError 等
        raise AuthError(f"Token 无效：{e}") from e
    if claims.get("typ") != "access":
        raise AuthError("Token 类型错误，需要 access token")
    try:
        user_id = int(claims["sub"])
    except (KeyError, ValueError) as e:
        raise AuthError("Token 主体缺失") from e
    row = await db.get(User, user_id)
    if row is None or row.deleted_at is not None or not row.is_active:
        raise AuthError("用户不存在或已停用")
    try:
        claim_token_version = int(claims.get("ver", 0))
    except (TypeError, ValueError) as e:
        raise AuthError("Token 版本无效") from e
    if claim_token_version != row.token_version:
        raise AuthError("Token 已失效，请重新登录")
    roles = normalize_role_codes(claims.get("roles", []))
    student_id = claims.get("sid")
    cu = CurrentUser(
        user_id=user_id,
        student_id=student_id,
        roles=roles,
        raw_claims=claims,
    )
    request.state.current_user = cu
    return cu


def require_role(*required: str) -> Callable[[CurrentUser], Awaitable[CurrentUser]]:
    """生成一个依赖，校验当前用户是否属于指定角色之一。"""

    async def _dep(
        user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if not user.has_role(*required):
            raise PermissionError(
                f"需要以下角色之一：{', '.join(required)}",
            )
        return user

    return _dep


# 便捷别名
DBDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


async def require_active_enrollment(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurrentUser:
    """v1.5 账号生命周期拦截器。

    仅用于学生端的"写"操作（提交申请、画像申诉、补录等）。
    非在读学生（休学 / 毕业 / 转出 / 归档）只保留只读能力。
    未绑定学生主档的账号不能执行学生侧写操作。
    """
    from app.auth.models import ENROLLMENT_ACTIVE, Student

    if user.student_id is None:
        raise PermissionError("仅绑定学生可执行该学生端操作", code=40305)
    student = await db.get(Student, user.student_id)
    if student is None:
        raise PermissionError("学生档案缺失，无法继续操作", code=40310)
    if student.enrollment_status != ENROLLMENT_ACTIVE:
        raise PermissionError(
            f"当前学籍状态 {student.enrollment_status} 为只读，"
            "仅支持查询历史；如需变更请联系学院老师",
            code=40311,
        )
    return user


ActiveStudentDep = Annotated[CurrentUser, Depends(require_active_enrollment)]
