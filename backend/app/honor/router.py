"""honor 路由 — FR-017 奖励荣誉展示。

学生侧（/honors）：
- GET /honors                  荣誉榜（分类/学年/级别筛选）
- GET /honors/{id}             详情（增加浏览量）
- GET /honors/categories       类别列表

管理侧（/admin/honors）：
- GET / POST /admin/honors
- GET/PATCH/archive /admin/honors/{id}
- GET /admin/honors/categories / POST upsert
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentUserDep, DBDep, require_role
from app.core.exceptions import NotFoundError
from app.core.response import ApiResponse, PageMeta, Paginated, ok
from app.honor import repository as repo
from app.honor import service
from app.honor.schemas import (
    HonorArchiveIn,
    HonorCategoryOut,
    HonorRecordBrief,
    HonorRecordDetail,
    HonorRecordIn,
)

_HONOR_EDITOR_ROLES = (
    "SUPER_ADMIN",
    "COLLEGE_LEADER",
    "COUNSELOR",
    "HEAD_TEACHER",
    "YOUTH_LEAGUE_TEACHER",
    "PARTY_BUILD_TEACHER",
)
_EditorRole = require_role(*_HONOR_EDITOR_ROLES)

router = APIRouter(prefix="/honors", tags=["honor"])
admin_router = APIRouter(prefix="/admin/honors", tags=["honor-admin"])


# ============================================================
# 学生/公开侧
# ============================================================
@router.get("/categories", response_model=ApiResponse[list[HonorCategoryOut]])
async def list_categories(
    db: DBDep, _user: CurrentUserDep
) -> ApiResponse[list[HonorCategoryOut]]:
    rows = await repo.list_categories(db)
    return ok([HonorCategoryOut.model_validate(r) for r in rows])


@router.get("", response_model=ApiResponse[Paginated[HonorRecordBrief]])
async def list_public_honors(
    db: DBDep,
    _user: CurrentUserDep,
    category_code: str | None = None,
    level: str | None = None,
    year: int | None = None,
    q: str | None = None,
    include_archived: bool = False,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[HonorRecordBrief]]:
    status = None if include_archived else "ACTIVE"
    rows, total = await repo.list_records(
        db,
        category_code=category_code,
        level=level,
        year=year,
        q=q,
        status=status,
        page=page,
        size=size,
    )
    items = [service.record_to_brief(r) for r in rows]
    return ok(Paginated[HonorRecordBrief](
        items=items, meta=PageMeta(page=page, size=size, total=total)
    ))


@router.get("/{record_id}", response_model=ApiResponse[HonorRecordDetail])
async def get_public_honor(
    record_id: int, db: DBDep, _user: CurrentUserDep
) -> ApiResponse[HonorRecordDetail]:
    row = await service.view_record_public(db, record_id)
    return ok(service.record_to_detail(row))


# ============================================================
# 管理侧
# ============================================================
@admin_router.get(
    "/categories", response_model=ApiResponse[list[HonorCategoryOut]]
)
async def admin_list_categories(
    db: DBDep, _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[list[HonorCategoryOut]]:
    rows = await repo.list_categories(db)
    return ok([HonorCategoryOut.model_validate(r) for r in rows])


@admin_router.post(
    "/categories", response_model=ApiResponse[HonorCategoryOut]
)
async def admin_upsert_category(
    payload: HonorCategoryOut,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[HonorCategoryOut]:
    # 允许 payload 携带 id（更新）或不携带（新建）
    data = payload.model_dump()
    data.pop("id", None)
    row = await repo.upsert_category(db, data)
    await db.commit()
    await db.refresh(row)
    return ok(HonorCategoryOut.model_validate(row))


@admin_router.get("", response_model=ApiResponse[Paginated[HonorRecordBrief]])
async def admin_list_records(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
    category_code: str | None = None,
    level: str | None = None,
    status: str | None = None,
    year: int | None = None,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[HonorRecordBrief]]:
    rows, total = await repo.list_records(
        db, category_code=category_code, level=level, status=status,
        year=year, q=q, page=page, size=size,
    )
    items = [service.record_to_brief(r) for r in rows]
    return ok(Paginated[HonorRecordBrief](
        items=items, meta=PageMeta(page=page, size=size, total=total)
    ))


@admin_router.post("", response_model=ApiResponse[HonorRecordDetail])
async def admin_create_record(
    payload: HonorRecordIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[HonorRecordDetail]:
    row = await service.create_record(
        db, payload.model_dump(),
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(service.record_to_detail(row))


@admin_router.get(
    "/{record_id}", response_model=ApiResponse[HonorRecordDetail]
)
async def admin_get_record(
    record_id: int,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[HonorRecordDetail]:
    row = await repo.get_record(db, record_id)
    if row is None:
        raise NotFoundError("荣誉记录不存在")
    return ok(service.record_to_detail(row))


@admin_router.patch(
    "/{record_id}", response_model=ApiResponse[HonorRecordDetail]
)
async def admin_update_record(
    record_id: int,
    payload: HonorRecordIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[HonorRecordDetail]:
    row = await service.update_record(
        db, record_id, payload.model_dump(),
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(service.record_to_detail(row))


@admin_router.post(
    "/{record_id}/archive", response_model=ApiResponse[HonorRecordDetail]
)
async def admin_archive_record(
    record_id: int,
    payload: HonorArchiveIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[HonorRecordDetail]:
    row = await service.archive_record(
        db, record_id,
        new_status=payload.new_status,
        reason=payload.reason,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(service.record_to_detail(row))
