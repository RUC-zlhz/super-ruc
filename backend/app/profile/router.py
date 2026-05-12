"""profile 路由 — FR-018 学生画像与信息管理。"""
from __future__ import annotations

from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.dependencies import ActiveStudentDep, CurrentUserDep, DBDep, require_role
from app.core.exceptions import BizError
from app.core.response import ApiResponse, PageMeta, Paginated, ok
from app.profile import repository as repo
from app.profile import service
from app.profile.schemas import (
    AcademicCorrectionIn,
    CorrectionDecisionIn,
    CorrectionIn,
    CorrectionOut,
    ProfileFactDecisionIn,
    ProfileFactIn,
    ProfileFactOut,
    ProfileFactSubmissionOut,
    ProfileFullViewDecisionIn,
    ProfileFullViewRequestIn,
    ProfileFullViewRequestOut,
    ProfileStudentSelfView,
    ProfileSummary,
    StudentAcademicInfoPatch,
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
student_admin_router = APIRouter(prefix="/admin/students", tags=["students-admin"])


def _file_response(data: bytes, filename: str, media_type: str) -> StreamingResponse:
    return StreamingResponse(
        BytesIO(data),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/me", response_model=ApiResponse[ProfileStudentSelfView])
async def my_profile(db: DBDep, user: CurrentUserDep) -> ApiResponse[ProfileStudentSelfView]:
    if user.student_id is None:
        raise BizError("仅学生有画像查看权限", code=40305, http_status=403)
    result = await service.build_summary_self(
        db,
        user.student_id,
        viewer_user_id=user.user_id,
        viewer_role=",".join(user.roles) or None,
    )
    return ok(result)


@router.post("/me/corrections", response_model=ApiResponse[CorrectionOut])
async def submit_my_correction(
    payload: CorrectionIn,
    db: DBDep,
    user: ActiveStudentDep,
) -> ApiResponse[CorrectionOut]:
    if user.student_id is None:
        raise BizError("仅学生可提交申诉", code=40305, http_status=403)
    row = await service.submit_correction(
        db,
        user.student_id,
        payload.model_dump(),
        viewer_user_id=user.user_id,
    )
    return ok(CorrectionOut.model_validate(row))


@router.post("/academic-corrections", response_model=ApiResponse[CorrectionOut])
async def submit_my_academic_correction(
    payload: AcademicCorrectionIn,
    db: DBDep,
    user: ActiveStudentDep,
) -> ApiResponse[CorrectionOut]:
    if user.student_id is None:
        raise BizError("仅学生可提交学籍纠错", code=40305, http_status=403)
    row = await service.submit_correction(
        db,
        user.student_id,
        {
            "fact_id": None,
            "field_name": payload.field_name,
            "proposed_value": payload.proposed_value,
            "reason": payload.reason,
        },
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
        db,
        student_id=user.student_id,
        status=status,
        page=page,
        size=size,
    )
    items = [CorrectionOut.model_validate(row) for row in rows]
    return ok(Paginated[CorrectionOut](items=items, meta=PageMeta(page=page, size=size, total=total)))


@router.post("/me/facts", response_model=ApiResponse[ProfileFactSubmissionOut])
async def submit_my_fact(
    payload: ProfileFactIn,
    db: DBDep,
    user: ActiveStudentDep,
) -> ApiResponse[ProfileFactSubmissionOut]:
    if user.student_id is None:
        raise BizError("仅学生可提交补录", code=40305, http_status=403)
    row = await service.submit_fact(
        db,
        user.student_id,
        payload.model_dump(),
        viewer_user_id=user.user_id,
    )
    return ok(service._build_fact_submission_view(row))


@router.get(
    "/me/fact-submissions",
    response_model=ApiResponse[Paginated[ProfileFactSubmissionOut]],
)
async def list_my_fact_submissions(
    db: DBDep,
    user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[ProfileFactSubmissionOut]]:
    if user.student_id is None:
        raise BizError("仅学生可查看本人补录", code=40305, http_status=403)
    rows, total = await service.list_my_fact_submissions(
        db,
        student_id=user.student_id,
        page=page,
        size=size,
    )
    items = [service._build_fact_submission_view(row) for row in rows]
    return ok(
        Paginated[ProfileFactSubmissionOut](
            items=items,
            meta=PageMeta(page=page, size=size, total=total),
        )
    )


@router.post(
    "/me/full-view-requests",
    response_model=ApiResponse[ProfileFullViewRequestOut],
)
async def submit_my_full_view_request(
    payload: ProfileFullViewRequestIn,
    db: DBDep,
    user: ActiveStudentDep,
) -> ApiResponse[ProfileFullViewRequestOut]:
    if user.student_id is None:
        raise BizError("仅学生可提交完整查看申请", code=40305, http_status=403)
    row = await service.submit_full_view_request(
        db,
        user.student_id,
        payload.model_dump(),
        requester_user_id=user.user_id,
        requester_role=",".join(user.roles) or None,
    )
    names = await service._load_full_view_request_user_names(db, [row])
    return ok(service._build_full_view_request_out(row, names))


@router.get(
    "/me/full-view-requests",
    response_model=ApiResponse[Paginated[ProfileFullViewRequestOut]],
)
async def list_my_full_view_requests(
    db: DBDep,
    user: CurrentUserDep,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[ProfileFullViewRequestOut]]:
    if user.student_id is None:
        raise BizError("仅学生可查看本人完整查看申请", code=40305, http_status=403)
    rows, total = await service.list_full_view_requests_self(
        db,
        student_id=user.student_id,
        requester_user_id=user.user_id,
        status=status,
        page=page,
        size=size,
    )
    names = await service._load_full_view_request_user_names(db, rows)
    items = [service._build_full_view_request_out(row, names) for row in rows]
    return ok(
        Paginated[ProfileFullViewRequestOut](
            items=items,
            meta=PageMeta(page=page, size=size, total=total),
        )
    )


@admin_router.get(
    "/students", response_model=ApiResponse[Paginated[StudentBasic]]
)
async def admin_search_students(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    q: str | None = None,
    grade_code: str | None = None,
    major_code: str | None = None,
    class_code: str | None = None,
    include_non_active: bool = Query(default=False),
    enrollment_status: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[StudentBasic]]:
    rows, total = await service.search_students_admin(
        db,
        q=q,
        grade_code=grade_code,
        major_code=major_code,
        class_code=class_code,
        include_non_active=include_non_active,
        enrollment_status=enrollment_status,
        page=page,
        size=size,
        viewer_user_id=user.user_id,
        viewer_role=",".join(user.roles) or None,
    )
    return ok(Paginated[StudentBasic](items=rows, meta=PageMeta(page=page, size=size, total=total)))


@admin_router.get(
    "/full-view-requests",
    response_model=ApiResponse[Paginated[ProfileFullViewRequestOut]],
)
async def admin_list_full_view_requests(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    student_id: int | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[ProfileFullViewRequestOut]]:
    rows, total = await service.list_full_view_requests_admin(
        db,
        student_id=student_id,
        status=status,
        page=page,
        size=size,
        viewer_user_id=user.user_id,
        viewer_role=",".join(user.roles) or None,
    )
    names = await service._load_full_view_request_user_names(db, rows)
    items = [service._build_full_view_request_out(row, names) for row in rows]
    return ok(
        Paginated[ProfileFullViewRequestOut](
            items=items,
            meta=PageMeta(page=page, size=size, total=total),
        )
    )


@admin_router.post(
    "/full-view-requests/{request_id}/decision",
    response_model=ApiResponse[ProfileFullViewRequestOut],
)
async def admin_decide_full_view_request(
    request_id: int,
    payload: ProfileFullViewDecisionIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[ProfileFullViewRequestOut]:
    row = await service.decide_full_view_request(
        db,
        request_id,
        decision=payload.decision,
        comment=payload.comment,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    names = await service._load_full_view_request_user_names(db, [row])
    return ok(service._build_full_view_request_out(row, names))


@admin_router.get("/{student_id}", response_model=ApiResponse[ProfileSummary])
async def admin_get_profile(
    student_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[ProfileSummary]:
    result = await service.build_summary_admin(
        db,
        student_id,
        viewer_user_id=user.user_id,
        viewer_role=",".join(user.roles) or None,
    )
    return ok(result)


@admin_router.post(
    "/{student_id}/full-view-requests",
    response_model=ApiResponse[ProfileFullViewRequestOut],
)
async def admin_submit_full_view_request(
    student_id: int,
    payload: ProfileFullViewRequestIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[ProfileFullViewRequestOut]:
    row = await service.submit_full_view_request(
        db,
        student_id,
        payload.model_dump(),
        requester_user_id=user.user_id,
        requester_role=",".join(user.roles) or None,
        enforce_student_scope=True,
    )
    names = await service._load_full_view_request_user_names(db, [row])
    return ok(service._build_full_view_request_out(row, names))


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
        db,
        student_id,
        payload.model_dump(),
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    names = await service._load_user_name_map(
        db,
        {value for value in (row.created_by, row.updated_by) if value is not None},
    )
    return ok(service._build_fact_admin_view(row, names))


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
        db,
        fact_id,
        payload.model_dump(),
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    names = await service._load_user_name_map(
        db,
        {value for value in (row.created_by, row.updated_by) if value is not None},
    )
    return ok(service._build_fact_admin_view(row, names))


@admin_router.delete(
    "/facts/{fact_id}", response_model=ApiResponse[dict]
)
async def admin_delete_fact(
    fact_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[dict]:
    await service.delete_fact(
        db,
        fact_id,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok({"id": fact_id, "deleted": True})


@admin_router.get(
    "/corrections", response_model=ApiResponse[Paginated[CorrectionOut]]
)
async def admin_list_corrections(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    student_id: int | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[CorrectionOut]]:
    rows, total = await service.list_corrections_admin(
        db,
        student_id=student_id,
        status=status,
        page=page,
        size=size,
        viewer_user_id=user.user_id,
        viewer_role=",".join(user.roles) or None,
    )
    items = [CorrectionOut.model_validate(row) for row in rows]
    return ok(Paginated[CorrectionOut](items=items, meta=PageMeta(page=page, size=size, total=total)))


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
        db,
        correction_id,
        decision=payload.decision,
        comment=payload.comment,
        apply_to_fact=payload.apply_to_fact,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(CorrectionOut.model_validate(row))


@admin_router.get(
    "/facts/pending", response_model=ApiResponse[Paginated[ProfileFactOut]]
)
async def admin_list_pending_facts(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    student_id: int | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[ProfileFactOut]]:
    rows, total = await service.list_pending_facts_admin(
        db,
        student_id=student_id,
        page=page,
        size=size,
        viewer_user_id=user.user_id,
        viewer_role=",".join(user.roles) or None,
    )
    names = await service._load_user_name_map(
        db,
        {
            value
            for row in rows
            for value in (row.created_by, row.updated_by)
            if value is not None
        },
    )
    items = [service._build_fact_admin_view(row, names) for row in rows]
    return ok(Paginated[ProfileFactOut](items=items, meta=PageMeta(page=page, size=size, total=total)))


@admin_router.post(
    "/facts/{fact_id}/decision", response_model=ApiResponse[ProfileFactOut]
)
async def admin_decide_fact(
    fact_id: int,
    payload: ProfileFactDecisionIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[ProfileFactOut]:
    row = await service.decide_fact(
        db,
        fact_id,
        decision=payload.decision,
        comment=payload.comment,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    names = await service._load_user_name_map(
        db,
        {value for value in (row.created_by, row.updated_by) if value is not None},
    )
    return ok(service._build_fact_admin_view(row, names))


@admin_router.get("/{student_id}/snapshot.pdf")
async def admin_profile_snapshot_pdf(
    student_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> StreamingResponse:
    data, filename = await service.generate_snapshot_pdf(
        db,
        student_id,
        viewer_user_id=user.user_id,
        viewer_role=",".join(user.roles) or None,
    )
    return _file_response(data, filename, "application/pdf")


@admin_router.get("/{student_id}/snapshot.xlsx")
async def admin_profile_snapshot_xlsx(
    student_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> StreamingResponse:
    data, filename = await service.generate_snapshot_xlsx(
        db,
        student_id,
        viewer_user_id=user.user_id,
        viewer_role=",".join(user.roles) or None,
    )
    return _file_response(
        data,
        filename,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@student_admin_router.patch(
    "/{student_id}/academic-info",
    response_model=ApiResponse[StudentBasic],
)
async def admin_update_student_academic_info(
    student_id: int,
    payload: StudentAcademicInfoPatch,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[StudentBasic]:
    row = await service.update_student_academic_info(
        db,
        student_id,
        payload.model_dump(exclude_unset=True),
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(StudentBasic.model_validate(row))
