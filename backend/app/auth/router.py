"""auth 路由：微信登录、工号登录、刷新、当前用户信息。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.auth import service
from app.auth.schemas import (
    EnrollmentStatusUpdate,
    RefreshTokenRequest,
    RoleInfo,
    TokenResponse,
    UserInfo,
    WorkNoLoginRequest,
    WxLoginRequest,
)
from app.core.dependencies import CurrentUserDep, DBDep, require_role
from app.core.response import ApiResponse, ok

router = APIRouter(prefix="/auth", tags=["auth"])
admin_router = APIRouter(prefix="/admin/auth", tags=["auth-admin"])

_LIFECYCLE_ROLES = ("SUPER_ADMIN", "COLLEGE_LEADER", "COUNSELOR")
_LifecycleRole = require_role(*_LIFECYCLE_ROLES)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/wx-login", response_model=ApiResponse[TokenResponse], summary="微信小程序登录/绑定")
async def wx_login(
    payload: WxLoginRequest, db: DBDep, request: Request
) -> ApiResponse[TokenResponse]:
    token = await service.login_with_wechat(
        db, code=payload.code, student_no=payload.student_no, ip=_client_ip(request)
    )
    return ok(token)


@router.post("/login", response_model=ApiResponse[TokenResponse], summary="教师工号 + 密码登录")
async def login(
    payload: WorkNoLoginRequest, db: DBDep, request: Request
) -> ApiResponse[TokenResponse]:
    token = await service.login_with_work_no(
        db, work_no=payload.work_no, password=payload.password, ip=_client_ip(request)
    )
    return ok(token)


@router.post("/refresh", response_model=ApiResponse[TokenResponse], summary="刷新访问令牌")
async def refresh(payload: RefreshTokenRequest, db: DBDep) -> ApiResponse[TokenResponse]:
    token = await service.refresh_access_token(db, payload.refresh_token)
    return ok(token)


@admin_router.patch(
    "/students/{student_id}/enrollment-status",
    response_model=ApiResponse[dict],
    summary="v1.5 更新学生学籍生命周期状态",
)
async def admin_update_enrollment_status(
    student_id: int,
    payload: EnrollmentStatusUpdate,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_LifecycleRole)],
) -> ApiResponse[dict]:
    await service.update_enrollment_status(
        db,
        student_id,
        status_code=payload.status,
        reason=payload.reason,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok({"student_id": student_id, "status": payload.status})


@router.get("/me", response_model=ApiResponse[UserInfo], summary="获取当前用户信息")
async def me(user: CurrentUserDep, db: DBDep) -> ApiResponse[UserInfo]:
    from app.auth import repository as repo

    row = await repo.get_user_by_id(db, user.user_id)
    if row is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("用户不存在")
    roles = await repo.list_user_roles(db, row.id)
    info = UserInfo(
        id=row.id,
        display_name=row.display_name,
        avatar_url=row.avatar_url,
        email=row.email,
        work_no=row.work_no,
        student_id=row.student_id,
        student_no=row.student.student_no if row.student else None,
        roles=[RoleInfo(code=r.role_code, scope_code=r.scope_code) for r in roles],
    )
    return ok(info)
