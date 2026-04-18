"""profile 路由 — FR-018 学生画像与信息管理。

学生侧（/profile）：
- GET /profile/me                       本人画像
- POST /profile/me/corrections          提交纠错申诉
- GET /profile/me/corrections           我的申诉列表

管理侧（/admin/profile）：
- GET /admin/profile/students           搜索学生
- GET /admin/profile/{student_id}       查看学生画像
- POST /admin/profile/{student_id}/facts         新增画像事实
- PATCH /admin/profile/facts/{fact_id}           修改
- DELETE /admin/profile/facts/{fact_id}          删除
- GET /admin/profile/corrections                 申诉列表
- POST /admin/profile/corrections/{id}/decision  审批申诉
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentUserDep, DBDep, require_role
from app.core.exceptions import BizError, NotFoundError
from app.core.response import ApiResponse, PageMeta, Paginated, ok
from app.profile import repository as repo
from app.profile import service
from app.profile.schemas import (
    CorrectionDecisionIn,
    CorrectionIn,
    CorrectionOut,
    ProfileFactIn,
    ProfileFactOut,
    ProfileStudentSelfView,
    ProfileSummary,
    StudentBasic,
)

_ADMIN_ROLES = (
    "SUPER_ADMIN",
    "COLLEGE_LEADER",
    "COUNSELOR",
    "HEAD_TEACHER",
)
_AdminRole = require_role(*_ADMIN_ROLES)

router = APIRouter(prefix="/profile", tags=["profile"])
admin_router = APIRouter(prefix="/admin/profile", tags=["profile-admin"])


# ============================================================
# 学生侧
# ============================================================
@router.get("/me", response_model=ApiResponse[ProfileStudentSelfView])
async def my_profile(db: DBDep, user: CurrentUserDep) -> ApiResponse[ProfileStudentSelfView]:
    if user.student_id is None:
        raise BizError("仅学生有画像查看权限", code=40305, http_status=403)
    result = await service.build_summary_self(
        db, user.student_id,
        viewer_user_id=user.user_id,
        viewer_role=",".join(user.roles) or None,
    )
    return ok(result)


@router.post("/me/corrections", response_model=ApiResponse[CorrectionOut])
async def submit_my_correction(
    payload: CorrectionIn, db: DBDep, user: CurrentUserDep,
) -> ApiResponse[CorrectionOut]:
    if user.student_id is None:
        raise BizError("仅学生可提交申诉", code=40305, http_status=403)
    row = await service.submit_correction(
        db, user.student_id, payload.model_dump(),
        viewer_user_id=user.user_id,
    )
    return ok(CorrectionOut.model_validate(row))


@router.get("/me/corrections", response_model=ApiResponse[Paginated[CorrectionOut]])
async def list_my_corrections(
    db: DBDep,
    user: CurrentUserDep,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[CorrectionOut]]:
    if user.student_id is None:
        raise BizError("仅学生可查看本人申诉", code=40305, http_status=403)
    rows, total = await repo.list_corrections(
        db, student_id=user.student_id, status=status, page=page, size=size,
    )
    items = [CorrectionOut.model_validate(r) for r in rows]
    return ok(Paginated[CorrectionOut](
        items=items, meta=PageMeta(page=page, size=size, total=total)
    ))


# ============================================================
# 管理侧
# ============================================================
@admin_router.get(
    "/students", response_model=ApiResponse[Paginated[StudentBasic]]
)
async def admin_search_students(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    q: str | None = None,
    grade_code: str | None = None,
    major_code: str | None = None,
    class_code: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[StudentBasic]]:
    rows, total = await repo.search_students(
        db, q=q, grade_code=grade_code, major_code=major_code,
        class_code=class_code, page=page, size=size,
    )
    items = [StudentBasic.model_validate(r) for r in rows]
    return ok(Paginated[StudentBasic](
        items=items, meta=PageMeta(page=page, size=size, total=total)
    ))


@admin_router.get(
    "/{student_id}", response_model=ApiResponse[ProfileSummary]
)
async def admin_get_profile(
    student_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[ProfileSummary]:
    result = await service.build_summary_admin(
        db, student_id,
        viewer_user_id=user.user_id,
        viewer_role=",".join(user.roles) or None,
    )
    return ok(result)


@admin_router.post(
    "/{student_id}/facts", response_model=ApiResponse[ProfileFactOut]
)
async def admin_add_fact(
    student_id: int,
    payload: ProfileFactIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[ProfileFactOut]:
    row = await service.create_fact(
        db, student_id, payload.model_dump(),
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(ProfileFactOut.model_validate(row))


@admin_router.patch(
    "/facts/{fact_id}", response_model=ApiResponse[ProfileFactOut]
)
async def admin_update_fact(
    fact_id: int,
    payload: ProfileFactIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[ProfileFactOut]:
    row = await service.update_fact(
        db, fact_id, payload.model_dump(),
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(ProfileFactOut.model_validate(row))


@admin_router.delete(
    "/facts/{fact_id}", response_model=ApiResponse[dict]
)
async def admin_delete_fact(
    fact_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[dict]:
    await service.delete_fact(
        db, fact_id,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok({"id": fact_id, "deleted": True})


@admin_router.get(
    "/corrections", response_model=ApiResponse[Paginated[CorrectionOut]]
)
async def admin_list_corrections(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    student_id: int | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[CorrectionOut]]:
    rows, total = await repo.list_corrections(
        db, student_id=student_id, status=status, page=page, size=size,
    )
    items = [CorrectionOut.model_validate(r) for r in rows]
    return ok(Paginated[CorrectionOut](
        items=items, meta=PageMeta(page=page, size=size, total=total)
    ))


@admin_router.post(
    "/corrections/{correction_id}/decision",
    response_model=ApiResponse[CorrectionOut],
)
async def admin_decide_correction(
    correction_id: int,
    payload: CorrectionDecisionIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[CorrectionOut]:
    row = await service.decide_correction(
        db, correction_id,
        decision=payload.decision,
        comment=payload.comment,
        apply_to_fact=payload.apply_to_fact,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(CorrectionOut.model_validate(row))
