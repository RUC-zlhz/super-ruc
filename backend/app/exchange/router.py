"""exchange 路由 — FR-009 文件导入导出 / FR-015 培养方案维护。

管理侧（所有路由均 L1~L3 角色可操作）：
- POST /admin/exchange/imports/{type}  上传 Excel，返回校验批次
- POST /admin/exchange/imports/{batch_id}/commit  提交（整批入库）
- GET  /admin/exchange/imports                     批次列表
- GET  /admin/exchange/imports/{batch_id}          批次详情 + 校验行
- GET  /admin/exchange/exports/students            学生导出
- GET  /admin/exchange/exports/transcripts         成绩导出
- GET  /admin/exchange/exports/curriculum          培养方案导出

培养方案 CRUD：
- GET  /admin/curriculum/plans
- POST /admin/curriculum/plans
- GET  /admin/curriculum/plans/{id}
- PATCH/admin/curriculum/plans/{id}
- DELETE /admin/curriculum/plans/{id}
- GET  /admin/curriculum/offerings
- POST /admin/curriculum/offerings
- GET  /admin/curriculum/equivalences
- POST /admin/curriculum/equivalences
"""
from __future__ import annotations

from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.audit.enforcement import ensure_export_permission, sanitize_student_mapping
from app.audit.policies import (
    EXPORT_CURRICULUM_SUMMARY,
    EXPORT_ERROR_REPORT,
    EXPORT_STUDENTS_DETAIL,
    EXPORT_TRANSCRIPTS_DETAIL,
)
from app.audit.service import build_audit_detail, log_action
from app.core.dependencies import CurrentUserDep, DBDep, require_role
from app.core.exceptions import BizError, NotFoundError
from app.core.response import ApiResponse, PageMeta, Paginated, ok
from app.exchange import default_imports, service
from app.exchange import repository as repo
from app.exchange.models import (
    IMPORT_TYPE_COURSE_EQUIV,
    IMPORT_TYPE_COURSE_OFFERING,
    IMPORT_TYPE_CURRICULUM_MODULE,
    IMPORT_TYPE_HONOR,
    IMPORT_TYPE_STUDENT,
    IMPORT_TYPE_TRANSCRIPT,
)
from app.exchange.schemas import (
    CourseEquivalenceIn,
    CourseEquivalenceOut,
    CourseOfferingIn,
    CourseOfferingOut,
    CurriculumPlanBrief,
    CurriculumPlanDetail,
    CurriculumPlanIn,
    DefaultImportAllResult,
    DefaultImportResult,
    ImportBatchBrief,
    ImportBatchDetail,
    ImportBatchRowOut,
    ImportCommitIn,
    ImportPreviewResult,
)

_ADMIN_ROLES = ("SUPER_ADMIN", "COLLEGE_LEADER", "COUNSELOR", "HEAD_TEACHER")
_AdminRole = require_role(*_ADMIN_ROLES)

_VALID_IMPORT_TYPES = {
    "student": IMPORT_TYPE_STUDENT,
    "transcript": IMPORT_TYPE_TRANSCRIPT,
    "curriculum-module": IMPORT_TYPE_CURRICULUM_MODULE,
    "course-equiv": IMPORT_TYPE_COURSE_EQUIV,
    "course-offering": IMPORT_TYPE_COURSE_OFFERING,
    "honor": IMPORT_TYPE_HONOR,
}

_MAX_UPLOAD_BYTES = 30 * 1024 * 1024

router = APIRouter(prefix="/admin", tags=["exchange"])


@router.post(
    "/default-imports/students",
    response_model=ApiResponse[DefaultImportResult],
)
async def import_default_students(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[DefaultImportResult]:
    result = await default_imports.import_default_students(
        db,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(result)


@router.post(
    "/default-imports/curriculum",
    response_model=ApiResponse[DefaultImportResult],
)
async def import_default_curriculum(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[DefaultImportResult]:
    result = await default_imports.import_default_curriculum(
        db,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(result)


@router.post(
    "/default-imports/all",
    response_model=ApiResponse[DefaultImportAllResult],
)
async def import_all_defaults(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[DefaultImportAllResult]:
    students = await default_imports.import_default_students(
        db,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    curriculum = await default_imports.import_default_curriculum(
        db,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(DefaultImportAllResult(students=students, curriculum=curriculum))


# ============================================================
# 导入
# ============================================================
@router.post(
    "/exchange/imports/{type_slug}",
    response_model=ApiResponse[ImportPreviewResult],
)
async def upload_import(
    type_slug: str,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    file: Annotated[UploadFile, File()],
) -> ApiResponse[ImportPreviewResult]:
    import_type = _VALID_IMPORT_TYPES.get(type_slug.lower())
    if import_type is None:
        raise BizError(f"不支持的导入类型：{type_slug}", code=40050)
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise BizError("文件超过 30MB 上限", code=40051)
    if not content:
        raise BizError("空文件", code=40052)

    batch = await service.validate_excel_batch(
        db,
        import_type=import_type,
        filename=file.filename or "unnamed.xlsx",
        file_bytes=content,
        object_bucket=None,
        object_key=None,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    rows = await repo.list_batch_rows(db, batch.id, limit=200)
    return ok(ImportPreviewResult(
        batch=ImportBatchDetail.model_validate(batch),
        rows=[ImportBatchRowOut.model_validate(r) for r in rows],
    ))


@router.post(
    "/exchange/imports/{batch_id}/commit",
    response_model=ApiResponse[ImportBatchDetail],
)
async def commit_import(
    batch_id: int,
    payload: ImportCommitIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[ImportBatchDetail]:
    batch = await service.commit_batch(
        db, batch_id,
        note=payload.note,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(ImportBatchDetail.model_validate(batch))


@router.get(
    "/exchange/imports",
    response_model=ApiResponse[Paginated[ImportBatchBrief]],
)
async def list_imports(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    import_type: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[ImportBatchBrief]]:
    rows, total = await repo.list_batches(
        db, import_type=import_type, status=status, page=page, size=size
    )
    items = [ImportBatchBrief.model_validate(r) for r in rows]
    return ok(Paginated[ImportBatchBrief](
        items=items, meta=PageMeta(page=page, size=size, total=total)
    ))


@router.get(
    "/exchange/imports/{batch_id}/error-report",
    summary='v1.5 下载行级错误报告 Excel（追加"错误原因"列）',
)
async def download_error_report(
    batch_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> StreamingResponse:
    await ensure_export_permission(
        db,
        roles=user.roles,
        export_code=EXPORT_ERROR_REPORT,
        actor_user_id=user.user_id,
        actor_role=",".join(user.roles) or None,
        event_type="IMPORT",
        entity_code="IMPORT_BATCH",
        action="DOWNLOAD_ERROR_REPORT_DENIED",
        entity_id=batch_id,
        message="当前角色无权下载导入错误报告",
        detail=build_audit_detail(
            target={"batch_id": batch_id},
        ),
    )
    data, filename = await service.build_error_report(db, batch_id)
    await log_action(
        db,
        event_type="IMPORT",
        entity_code="IMPORT_BATCH",
        action="DOWNLOAD_ERROR_REPORT",
        entity_id=batch_id,
        actor_user_id=user.user_id,
        actor_role=",".join(user.roles) or None,
        detail=build_audit_detail(
            target={"batch_id": batch_id},
        ),
    )
    await db.commit()
    return _xlsx_response(data, filename)


@router.get(
    "/exchange/imports/{batch_id}",
    response_model=ApiResponse[ImportPreviewResult],
)
async def get_import(
    batch_id: int,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    severity: str | None = Query(default=None),
) -> ApiResponse[ImportPreviewResult]:
    batch = await repo.get_batch(db, batch_id)
    if batch is None:
        raise NotFoundError("批次不存在")
    rows = await repo.list_batch_rows(db, batch_id, severity=severity, limit=500)
    return ok(ImportPreviewResult(
        batch=ImportBatchDetail.model_validate(batch),
        rows=[ImportBatchRowOut.model_validate(r) for r in rows],
    ))


# ============================================================
# 导出（Excel 下载）
# ============================================================
def _xlsx_response(data: bytes, filename: str) -> StreamingResponse:
    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/exchange/exports/students")
async def export_students(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    grade_code: str | None = None,
    major_code: str | None = None,
) -> StreamingResponse:
    actor_role = ",".join(user.roles) or None
    await ensure_export_permission(
        db,
        roles=user.roles,
        export_code=EXPORT_STUDENTS_DETAIL,
        actor_user_id=user.user_id,
        actor_role=actor_role,
        event_type="EXPORT",
        entity_code="STUDENT",
        action="EXPORT_STUDENTS_DENIED",
        message="当前角色无权导出学生明细",
        detail=build_audit_detail(
            refs=[{"grade_code": grade_code, "major_code": major_code}],
        ),
    )
    students = await repo.list_all_students(
        db, grade_code=grade_code, major_code=major_code, limit=10000
    )
    headers = [
        "student_no", "full_name", "gender", "grade_code", "major_code",
        "class_code", "political_status", "enrollment_year",
        "expected_graduation_year", "email", "status",
    ]
    rows: list[list[object | None]] = []
    masked_fields: set[str] = set()
    for student in students:
        sanitized, current_masked = await sanitize_student_mapping(
            db,
            roles=user.roles,
            data={
                "student_no": student.student_no,
                "full_name": student.full_name,
                "gender": student.gender,
                "grade_code": student.grade_code,
                "major_code": student.major_code,
                "class_code": student.class_code,
                "political_status": student.political_status,
                "enrollment_year": student.enrollment_year,
                "expected_graduation_year": student.expected_graduation_year,
                "email": student.email,
                "status": student.status,
                "enrollment_status": student.enrollment_status,
                "enrollment_status_reason": student.enrollment_status_reason,
                "enrollment_status_updated_at": student.enrollment_status_updated_at,
            },
        )
        masked_fields.update(current_masked)
        rows.append(
            [
                sanitized.get("student_no"),
                sanitized.get("full_name"),
                sanitized.get("gender"),
                sanitized.get("grade_code"),
                sanitized.get("major_code"),
                sanitized.get("class_code"),
                sanitized.get("political_status"),
                sanitized.get("enrollment_year"),
                sanitized.get("expected_graduation_year"),
                sanitized.get("email"),
                sanitized.get("status"),
            ]
        )
    data = service.export_workbook(headers, rows, sheet_name="students")
    await log_action(
        db,
        event_type="EXPORT",
        entity_code="STUDENT",
        action="EXPORT_STUDENTS",
        actor_user_id=user.user_id,
        actor_role=actor_role,
        detail=build_audit_detail(
            refs=[{"grade_code": grade_code, "major_code": major_code}],
            masked_fields=sorted(masked_fields),
            metrics={"count": len(rows)},
        ),
    )
    await db.commit()
    return _xlsx_response(data, "students.xlsx")


@router.get("/exchange/exports/transcripts")
async def export_transcripts(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    student_no: str | None = None,
    term_code: str | None = None,
) -> StreamingResponse:
    actor_role = ",".join(user.roles) or None
    await ensure_export_permission(
        db,
        roles=user.roles,
        export_code=EXPORT_TRANSCRIPTS_DETAIL,
        actor_user_id=user.user_id,
        actor_role=actor_role,
        event_type="EXPORT",
        entity_code="TRANSCRIPT",
        action="EXPORT_TRANSCRIPTS_DENIED",
        message="当前角色无权导出成绩明细",
        detail=build_audit_detail(
            refs=[{"student_no": student_no, "term_code": term_code}],
        ),
    )
    records, _ = await repo.list_student_records(
        db, student_no=student_no, term_code=term_code, page=1, size=10000
    )
    headers = [
        "student_id", "term_code", "course_code", "course_name",
        "credits", "course_type", "score", "grade_letter", "pass_flag",
    ]
    rows = [
        [r.student_id, r.term_code, r.course_code, r.course_name,
         r.credits, r.course_type, r.score, r.grade_letter, r.pass_flag]
        for r in records
    ]
    data = service.export_workbook(headers, rows, sheet_name="transcripts")
    await log_action(
        db,
        event_type="EXPORT",
        entity_code="TRANSCRIPT",
        action="EXPORT_TRANSCRIPTS",
        actor_user_id=user.user_id,
        actor_role=actor_role,
        detail=build_audit_detail(
            refs=[{"student_no": student_no, "term_code": term_code}],
            metrics={"count": len(rows)},
        ),
    )
    await db.commit()
    return _xlsx_response(data, "transcripts.xlsx")


@router.get("/exchange/exports/curriculum")
async def export_curriculum(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    grade_code: str | None = None,
    major_code: str | None = None,
) -> StreamingResponse:
    actor_role = ",".join(user.roles) or None
    await ensure_export_permission(
        db,
        roles=user.roles,
        export_code=EXPORT_CURRICULUM_SUMMARY,
        actor_user_id=user.user_id,
        actor_role=actor_role,
        event_type="EXPORT",
        entity_code="CURRICULUM_PLAN",
        action="EXPORT_CURRICULUM_DENIED",
        message="当前角色无权导出培养方案汇总",
        detail=build_audit_detail(
            refs=[{"grade_code": grade_code, "major_code": major_code}],
        ),
    )
    plans, _ = await repo.list_plans(
        db, grade_code=grade_code, major_code=major_code, page=1, size=1000
    )
    headers = [
        "grade_code", "major_code", "plan_name", "version_label",
        "module_code", "module_name", "module_type", "credits_required",
    ]
    rows: list[list] = []
    for plan in plans:
        modules = await repo.list_modules_by_plan(db, plan.id)
        if not modules:
            rows.append([plan.grade_code, plan.major_code, plan.plan_name,
                         plan.version_label, None, None, None, None])
            continue
        for m in modules:
            rows.append([
                plan.grade_code, plan.major_code, plan.plan_name, plan.version_label,
                m.module_code, m.module_name, m.module_type, m.credits_required,
            ])
    data = service.export_workbook(headers, rows, sheet_name="curriculum")
    await log_action(
        db,
        event_type="EXPORT",
        entity_code="CURRICULUM_PLAN",
        action="EXPORT_CURRICULUM",
        actor_user_id=user.user_id,
        actor_role=actor_role,
        detail=build_audit_detail(
            refs=[{"grade_code": grade_code, "major_code": major_code}],
            metrics={"count": len(rows)},
        ),
    )
    await db.commit()
    return _xlsx_response(data, "curriculum.xlsx")


# ============================================================
# 培养方案 CRUD（FR-015）
# ============================================================
curriculum_router = APIRouter(prefix="/admin/curriculum", tags=["curriculum"])


@curriculum_router.get(
    "/plans", response_model=ApiResponse[Paginated[CurriculumPlanBrief]]
)
async def list_plans(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    grade_code: str | None = None,
    major_code: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[CurriculumPlanBrief]]:
    rows, total = await repo.list_plans(
        db, grade_code=grade_code, major_code=major_code,
        is_active=is_active, page=page, size=size,
    )
    items = [CurriculumPlanBrief.model_validate(r) for r in rows]
    return ok(Paginated[CurriculumPlanBrief](
        items=items, meta=PageMeta(page=page, size=size, total=total)
    ))


@curriculum_router.post(
    "/plans", response_model=ApiResponse[CurriculumPlanDetail]
)
async def create_plan(
    payload: CurriculumPlanIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[CurriculumPlanDetail]:
    raw = payload.model_dump()
    raw["modules"] = [m for m in raw.get("modules") or []]
    plan_id = await service.upsert_plan_with_modules(
        db, raw,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    plan = await repo.get_plan(db, plan_id)
    return ok(CurriculumPlanDetail.model_validate(plan))


@curriculum_router.get(
    "/plans/{plan_id}", response_model=ApiResponse[CurriculumPlanDetail]
)
async def get_plan(
    plan_id: int,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[CurriculumPlanDetail]:
    plan = await repo.get_plan(db, plan_id)
    if plan is None:
        raise NotFoundError("培养方案不存在")
    return ok(CurriculumPlanDetail.model_validate(plan))


@curriculum_router.patch(
    "/plans/{plan_id}", response_model=ApiResponse[CurriculumPlanDetail]
)
async def update_plan(
    plan_id: int,
    payload: CurriculumPlanIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[CurriculumPlanDetail]:
    # 重用 upsert 逻辑
    raw = payload.model_dump()
    plan = await repo.get_plan(db, plan_id)
    if plan is None:
        raise NotFoundError("培养方案不存在")
    # 强制绑定 id 的主键三元组 — 按当前记录
    raw["grade_code"] = plan.grade_code
    raw["major_code"] = plan.major_code
    raw["version_label"] = plan.version_label
    new_plan_id = await service.upsert_plan_with_modules(
        db, raw,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    refreshed = await repo.get_plan(db, new_plan_id)
    return ok(CurriculumPlanDetail.model_validate(refreshed))


@curriculum_router.delete(
    "/plans/{plan_id}", response_model=ApiResponse[dict]
)
async def delete_plan(
    plan_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[dict]:
    await service.delete_plan(
        db, plan_id,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok({"id": plan_id, "deleted": True})


# ---- Offerings ----
@curriculum_router.get(
    "/offerings", response_model=ApiResponse[Paginated[CourseOfferingOut]]
)
async def list_offerings(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    term_code: str | None = None,
    course_code: str | None = None,
    major_code: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
) -> ApiResponse[Paginated[CourseOfferingOut]]:
    rows, total = await repo.list_course_offerings(
        db, term_code=term_code, course_code=course_code,
        major_code=major_code, page=page, size=size,
    )
    items = [CourseOfferingOut.model_validate(r) for r in rows]
    return ok(Paginated[CourseOfferingOut](
        items=items, meta=PageMeta(page=page, size=size, total=total)
    ))


@curriculum_router.post(
    "/offerings", response_model=ApiResponse[CourseOfferingOut]
)
async def upsert_offering(
    payload: CourseOfferingIn,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[CourseOfferingOut]:
    row = await repo.upsert_course_offering(db, payload.model_dump())
    await db.commit()
    await db.refresh(row)
    return ok(CourseOfferingOut.model_validate(row))


# ---- Equivalences ----
@curriculum_router.get(
    "/equivalences", response_model=ApiResponse[Paginated[CourseEquivalenceOut]]
)
async def list_equivalences(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_AdminRole)],
    grade_code: str | None = None,
    major_code: str | None = None,
    source_code: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
) -> ApiResponse[Paginated[CourseEquivalenceOut]]:
    rows, total = await repo.list_equivalences(
        db, grade_code=grade_code, major_code=major_code,
        source_code=source_code, page=page, size=size,
    )
    items = [CourseEquivalenceOut.model_validate(r) for r in rows]
    return ok(Paginated[CourseEquivalenceOut](
        items=items, meta=PageMeta(page=page, size=size, total=total)
    ))


@curriculum_router.post(
    "/equivalences", response_model=ApiResponse[CourseEquivalenceOut]
)
async def upsert_equivalence(
    payload: CourseEquivalenceIn,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[CourseEquivalenceOut]:
    row = await repo.upsert_equivalence(db, payload.model_dump())
    await db.commit()
    await db.refresh(row)
    return ok(CourseEquivalenceOut.model_validate(row))


@router.get("/exchange/ping", response_model=ApiResponse[dict], include_in_schema=False)
async def ping() -> ApiResponse[dict]:
    return ok({"module": "exchange", "status": "ready"})
