"""honor 路由 — FR-017 奖励荣誉展示。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.auth.role_codes import ROLE_CODE_COLLABORATOR_ROLES
from app.core.dependencies import CurrentUserDep, DBDep, require_role
from app.core.exceptions import NotFoundError
from app.core.response import ApiResponse, PageMeta, Paginated, ok
from app.honor import repository as repo
from app.honor import service
from app.honor.schemas import (
    AdminHonorRecordBrief,
    AdminHonorRecordDetail,
    HonorArchiveIn,
    HonorCategoryIn,
    HonorCategoryOut,
    HonorRecordIn,
    PublicHonorRecordBrief,
    PublicHonorRecordDetail,
)

_HONOR_EDITOR_ROLES = (
    "SUPER_ADMIN",
    "COLLEGE_LEADER",
    "COUNSELOR",
    "HEAD_TEACHER",
    "YOUTH_LEAGUE_TEACHER",
    "PARTY_BUILD_TEACHER",
    *ROLE_CODE_COLLABORATOR_ROLES,
)
_EditorRole = require_role(*_HONOR_EDITOR_ROLES)

router = APIRouter(prefix="/honors", tags=["honor"])
admin_router = APIRouter(prefix="/admin/honors", tags=["honor-admin"])


@router.get("/categories", response_model=ApiResponse[list[HonorCategoryOut]])
async def list_categories(
    db: DBDep, _user: CurrentUserDep
) -> ApiResponse[list[HonorCategoryOut]]:
    rows = await repo.list_categories(db, include_inactive=False)
    return ok([HonorCategoryOut.model_validate(row) for row in rows])


@router.get("", response_model=ApiResponse[Paginated[PublicHonorRecordBrief]])
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
) -> ApiResponse[Paginated[PublicHonorRecordBrief]]:
    rows, total = await repo.list_public_records(
        db,
        category_code=category_code,
        level=level,
        year=year,
        q=q,
        include_historical=include_archived,
        page=page,
        size=size,
    )
    items = await service.build_public_briefs(db, rows)
    return ok(
        Paginated[PublicHonorRecordBrief](
            items=items,
            meta=PageMeta(page=page, size=size, total=total),
        )
    )


@router.get("/{record_id}", response_model=ApiResponse[PublicHonorRecordDetail])
async def get_public_honor(
    record_id: int, db: DBDep, _user: CurrentUserDep
) -> ApiResponse[PublicHonorRecordDetail]:
    row = await service.view_record_public(db, record_id)
    return ok(await service.build_public_detail_for_record(db, row))


@admin_router.get(
    "/categories", response_model=ApiResponse[list[HonorCategoryOut]]
)
async def admin_list_categories(
    db: DBDep, _user: Annotated[CurrentUserDep, Depends(_EditorRole)]
) -> ApiResponse[list[HonorCategoryOut]]:
    rows = await repo.list_categories(db, include_inactive=True)
    return ok([HonorCategoryOut.model_validate(row) for row in rows])


@admin_router.post(
    "/categories", response_model=ApiResponse[HonorCategoryOut]
)
async def admin_upsert_category(
    payload: HonorCategoryIn,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[HonorCategoryOut]:
    data = payload.model_dump()
    data.pop("id", None)
    row = await repo.upsert_category(db, data)
    await db.commit()
    await db.refresh(row)
    return ok(HonorCategoryOut.model_validate(row))


@admin_router.get("", response_model=ApiResponse[Paginated[AdminHonorRecordBrief]])
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
) -> ApiResponse[Paginated[AdminHonorRecordBrief]]:
    rows, total = await repo.list_records(
        db,
        category_code=category_code,
        level=level,
        status=status,
        year=year,
        q=q,
        page=page,
        size=size,
    )
    items = await service.build_admin_briefs(db, rows)
    return ok(
        Paginated[AdminHonorRecordBrief](
            items=items,
            meta=PageMeta(page=page, size=size, total=total),
        )
    )


@admin_router.post("", response_model=ApiResponse[AdminHonorRecordDetail])
async def admin_create_record(
    payload: HonorRecordIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[AdminHonorRecordDetail]:
    row = await service.create_record(
        db,
        payload.model_dump(),
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(await service.build_admin_detail_for_record(db, row))


@admin_router.get(
    "/{record_id}", response_model=ApiResponse[AdminHonorRecordDetail]
)
async def admin_get_record(
    record_id: int,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[AdminHonorRecordDetail]:
    row = await repo.get_record(db, record_id)
    if row is None:
        raise NotFoundError("荣誉记录不存在")
    return ok(await service.build_admin_detail_for_record(db, row))


@admin_router.patch(
    "/{record_id}", response_model=ApiResponse[AdminHonorRecordDetail]
)
async def admin_update_record(
    record_id: int,
    payload: HonorRecordIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[AdminHonorRecordDetail]:
    row = await service.update_record(
        db,
        record_id,
        payload.model_dump(),
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(await service.build_admin_detail_for_record(db, row))


@admin_router.post(
    "/{record_id}/archive", response_model=ApiResponse[AdminHonorRecordDetail]
)
async def admin_archive_record(
    record_id: int,
    payload: HonorArchiveIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[AdminHonorRecordDetail]:
    row = await service.archive_record(
        db,
        record_id,
        new_status=payload.new_status,
        reason=payload.reason,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(await service.build_admin_detail_for_record(db, row))
