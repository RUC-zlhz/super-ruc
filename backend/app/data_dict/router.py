"""data_dict 路由。

- GET  /api/v1/data-dicts?dict_type=xxx         查询选项列表（所有已登录用户）
- POST /api/v1/admin/data-dicts                  新增选项（L3+）
- DELETE /api/v1/admin/data-dicts/{id}           删除选项（L1/L2）
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentUserDep, DBDep, require_role
from app.core.response import ApiResponse, ok
from app.data_dict import repository as repo
from app.data_dict.schemas import DataDictIn, DataDictOut

router = APIRouter(tags=["data-dict"])
admin_router = APIRouter(prefix="/admin/data-dicts", tags=["data-dict-admin"])

_AdminRole = require_role("SUPER_ADMIN", "COLLEGE_LEADER", "COUNSELOR", "HEAD_TEACHER")


@router.get("/data-dicts", response_model=ApiResponse[list[DataDictOut]])
async def list_data_dicts(
    dict_type: str = Query(..., min_length=1, max_length=64),
    db: DBDep = ...,
    _user: CurrentUserDep = ...,
):
    """按类型查询字典选项列表。"""
    items = await repo.list_by_type(db, dict_type)
    return ok([DataDictOut.model_validate(i) for i in items])


@admin_router.post("", response_model=ApiResponse[DataDictOut])
async def create_data_dict(
    body: DataDictIn,
    db: DBDep = ...,
    _user: CurrentUserDep = _AdminRole,
):
    """新增字典选项（幂等）。"""
    item = await repo.create_item(db, body.dict_type, body.value, body.label, body.sort_order)
    await db.commit()
    return ok(DataDictOut.model_validate(item))


@admin_router.delete("/{item_id}", response_model=ApiResponse[dict])
async def delete_data_dict(
    item_id: int,
    db: DBDep = ...,
    _user: CurrentUserDep = _AdminRole,
):
    """删除字典选项。"""
    found = await repo.delete_item(db, item_id)
    if not found:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("字典条目不存在")
    await db.commit()
    return ok({"deleted": True})
