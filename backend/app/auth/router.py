"""auth 路由：微信登录、工号登录、刷新、当前用户信息。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.auth import service
from app.auth.schemas import (
    ChangePasswordRequest,
    EnrollmentStatusUpdate,
    LogoutRequest,
    RefreshTokenRequest,
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
        db,
        code=payload.code,
        student_no=payload.student_no,
        full_name=payload.full_name,
        id_card_tail=payload.id_card_tail,
        ip=_client_ip(request),
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


@router.post("/logout", response_model=ApiResponse[dict], summary="退出登录并失效当前账号令牌")
async def logout(
    db: DBDep,
    user: CurrentUserDep,
    request: Request,
    payload: LogoutRequest | None = None,
) -> ApiResponse[dict]:
    await service.logout(
        db,
        user_id=user.user_id,
        refresh_token=payload.refresh_token if payload else None,
        ip=_client_ip(request),
    )
    return ok({"revoked": True})


@router.post("/change-password", response_model=ApiResponse[UserInfo], summary="修改当前账号密码")
async def change_password(
    payload: ChangePasswordRequest,
    db: DBDep,
    user: CurrentUserDep,
    request: Request,
) -> ApiResponse[UserInfo]:
    info = await service.change_password(
        db,
        user_id=user.user_id,
        old_password=payload.old_password,
        new_password=payload.new_password,
        ip=_client_ip(request),
    )
    return ok(info)


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
    return ok(await service.build_user_info(db, row))
