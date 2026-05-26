"""report 路由 — FR-014 学业缺口 / FR-016 运营看板。

学生侧：
- GET /report/academic-gap            当前学生的学业缺口
- POST /report/transcript-pdf         上传成绩单 PDF，生成待人工核验记录

管理侧：
- GET /admin/report/overview          学院运营看板
- GET /admin/report/academic-gap/{student_id}  针对指定学生
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.core.dependencies import ActiveStudentDep, CurrentUserDep, DBDep, require_role
from app.core.exceptions import BizError
from app.core.response import ApiResponse, PageMeta, Paginated, ok
from app.core.uploads import read_upload_file_limited
from app.report import service
from app.report.schemas import (
    AcademicGapAggregateItem,
    AcademicGapResult,
    OverviewResult,
    TranscriptPdfReviewCommitIn,
    TranscriptPdfReviewCommitResult,
    TranscriptPdfUploadResult,
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


@router.post(
    "/report/transcript-pdf",
    response_model=ApiResponse[TranscriptPdfUploadResult],
)
async def upload_my_transcript_pdf(
    db: DBDep,
    user: ActiveStudentDep,
    file: Annotated[UploadFile, File()],
) -> ApiResponse[TranscriptPdfUploadResult]:
    if user.student_id is None:
        raise BizError("仅学生可上传本人成绩单 PDF", code=40305, http_status=403)
    content = await read_upload_file_limited(file)
    result = await service.upload_transcript_pdf_for_review(
        db,
        student_id=user.student_id,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
        filename=file.filename,
        content=content,
        content_type=file.content_type,
    )
    return ok(result)


@router.get(
    "/admin/report/overview",
    response_model=ApiResponse[OverviewResult],
)
async def admin_overview(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_LeaderRole)],
    term_code: str | None = None,
) -> ApiResponse[OverviewResult]:
    return ok(await service.build_overview(db, term_code=term_code))


@router.get(
    "/admin/report/academic-gap",
    response_model=ApiResponse[Paginated[AcademicGapAggregateItem]],
)
async def admin_academic_gap_list(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_LeaderRole)],
    keyword: str | None = None,
    grade_code: str | None = None,
    major_code: str | None = None,
    risk_level: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[AcademicGapAggregateItem]]:
    items, total = await service.list_academic_gap_overview(
        db,
        keyword=keyword,
        grade_code=grade_code,
        major_code=major_code,
        risk_level=risk_level,
        page=page,
        page_size=page_size,
        viewer_user_id=user.user_id,
        viewer_roles=user.roles,
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
    user: Annotated[CurrentUserDep, Depends(_LeaderRole)],
) -> ApiResponse[AcademicGapResult]:
    await service.ensure_academic_gap_student_visible(
        db,
        student_id=student_id,
        viewer_user_id=user.user_id,
        viewer_roles=user.roles,
    )
    return ok(await service.compute_academic_gap(db, student_id))


@router.post(
    "/admin/report/transcript-pdf-reviews/{batch_id}/commit",
    response_model=ApiResponse[TranscriptPdfReviewCommitResult],
)
async def admin_commit_transcript_pdf_review(
    batch_id: int,
    payload: TranscriptPdfReviewCommitIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_LeaderRole)],
) -> ApiResponse[TranscriptPdfReviewCommitResult]:
    result = await service.commit_transcript_pdf_review(
        db,
        batch_id,
        payload,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(result)
