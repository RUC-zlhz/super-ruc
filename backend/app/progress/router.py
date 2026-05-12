"""S12 统一进度中心路由。"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.dependencies import CurrentUserDep, DBDep
from app.core.exceptions import BizError
from app.core.response import ApiResponse, ok
from app.progress import service
from app.progress.schemas import ProgressMyResult

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/my", response_model=ApiResponse[ProgressMyResult])
async def my_progress(
    db: DBDep,
    user: CurrentUserDep,
) -> ApiResponse[ProgressMyResult]:
    if user.student_id is None:
        raise BizError("仅学生可查看统一进度中心", code=40305, http_status=403)
    return ok(
        await service.build_my_progress(
            db,
            user_id=user.user_id,
            student_id=user.student_id,
        )
    )
