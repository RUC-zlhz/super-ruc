"""report 路由 — FR-014 学业缺口 / FR-016 运营看板。

学生侧：
- GET /report/academic-gap            当前学生的学业缺口

管理侧：
- GET /admin/report/overview          学院运营看板
- GET /admin/report/academic-gap/{student_id}  针对指定学生
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUserDep, DBDep, require_role
from app.core.exceptions import BizError
from app.core.response import ApiResponse, PageMeta, Paginated, ok
from app.report import service
from app.report.schemas import (
    AcademicGapAggregateItem,
    AcademicGapResult,
    OverviewResult,
)

_LEADER_ROLES = (
    "SUPER_ADMIN",
    "COLLEGE_LEADER",
    "COUNSELOR",
    "HEAD_TEACHER",
    "YOUTH_LEAGUE_TEACHER",
    "PARTY_BUILD_TEACHER",
)
_LeaderRole = require_role(*_LEADER_ROLES)

router = APIRouter(tags=["report"])


@router.get(
    "/report/academic-gap",
    response_model=ApiResponse[AcademicGapResult],
)
async def my_academic_gap(
    db: DBDep, user: CurrentUserDep
) -> ApiResponse[AcademicGapResult]:
    if user.student_id is None:
        raise BizError("仅学生可查看本人学业缺口", code=40305, http_status=403)
    result = await service.compute_academic_gap(db, user.student_id)
    return ok(result)


@router.get(
    "/admin/report/overview",
    response_model=ApiResponse[OverviewResult],
)
async def admin_overview(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_LeaderRole)],
) -> ApiResponse[OverviewResult]:
    return ok(await service.build_overview(db))


@router.get(
    "/admin/report/academic-gap",
    response_model=ApiResponse[Paginated[AcademicGapAggregateItem]],
)
async def admin_academic_gap_list(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_LeaderRole)],
    keyword: str | None = None,
    grade_code: str | None = None,
    major_code: str | None = None,
    risk_level: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ApiResponse[Paginated[AcademicGapAggregateItem]]:
    items, total = await service.list_academic_gap_overview(
        db,
        keyword=keyword,
        grade_code=grade_code,
        major_code=major_code,
        risk_level=risk_level,
        page=page,
        page_size=page_size,
    )
    return ok(
        Paginated[AcademicGapAggregateItem](
            items=items,
            meta=PageMeta(page=page, size=page_size, total=total),
        )
    )


@router.get(
    "/admin/report/academic-gap/{student_id}",
    response_model=ApiResponse[AcademicGapResult],
)
async def admin_academic_gap(
    student_id: int,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_LeaderRole)],
) -> ApiResponse[AcademicGapResult]:
    return ok(await service.compute_academic_gap(db, student_id))
