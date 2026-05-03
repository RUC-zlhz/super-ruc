"""workflow 路由 — FR-004~008。

三个 APIRouter：
- router            /workflow   学生侧本人流程视图（FR-004）
- request_router    /requests   学生侧申请（FR-006）+ 管理侧申请详情
- admin_router      /admin/*    管理侧（FR-005/007/008 + 类型维护）
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.audit.enforcement import ensure_export_permission
from app.audit.policies import REQUEST_PROOF_PREVIEW
from app.audit.service import build_audit_detail, log_action
from app.core.dependencies import (
    ActiveStudentDep,
    CurrentUserDep,
    DBDep,
    require_role,
)
from app.core.exceptions import BizError
from app.core.response import ApiResponse, PageMeta, Paginated, ok
from app.workflow import pdf_generator, quiz_service, service
from app.workflow import repository as repo
from app.workflow.schemas import (
    ApprovalActionIn,
    AttachmentOut,
    NodeCompleteIn,
    NodeMarkStatusIn,
    OfflineHandleIn,
    QuizDrawOut,
    QuizQuestionAdminOut,
    QuizQuestionIn,
    QuizQuestionStudentOut,
    QuizQuestionUpdate,
    QuizSubmitIn,
    QuizSubmitOut,
    ReminderGenerateIn,
    ReopenRequestIn,
    RequestBrief,
    RequestCreate,
    RequestDetail,
    RequestTypeIn,
    RequestTypeOut,
    RequestUpdate,
    StudentWorkflowBrief,
    StudentWorkflowDetail,
    StudentWorkflowStart,
    WorkflowTemplateIn,
    WorkflowTemplateOut,
)

_APPROVER_ROLES = (
    "SUPER_ADMIN",
    "COLLEGE_LEADER",
    "COUNSELOR",
    "HEAD_TEACHER",
    "YOUTH_LEAGUE_TEACHER",
    "PARTY_BUILD_TEACHER",
)
_WORKFLOW_EDITOR_ROLES = _APPROVER_ROLES
_ApproverRole = require_role(*_APPROVER_ROLES)
_EditorRole = require_role(*_WORKFLOW_EDITOR_ROLES)
_AdminRole = require_role("SUPER_ADMIN")

router = APIRouter(prefix="/workflow", tags=["workflow"])
request_router = APIRouter(prefix="/requests", tags=["request"])
admin_router = APIRouter(prefix="/admin", tags=["workflow-admin"])
quiz_router = APIRouter(prefix="/quiz", tags=["quiz"])


# ===========================================================
# A. 学生侧：本人流程视图（FR-004）
# ===========================================================
@router.get("/my", response_model=ApiResponse[list[StudentWorkflowDetail]])
async def list_my_workflows(
    db: DBDep, user: CurrentUserDep
) -> ApiResponse[list[StudentWorkflowDetail]]:
    if user.student_id is None:
        raise BizError("仅学生可查看本人流程", code=40305, http_status=403)
    return ok(await service.list_my_workflows(db, user.student_id))


@router.get("/{workflow_id}", response_model=ApiResponse[StudentWorkflowDetail])
async def get_workflow(
    workflow_id: int, db: DBDep, user: CurrentUserDep
) -> ApiResponse[StudentWorkflowDetail]:
    detail = await service.get_workflow_for_student(
        db, workflow_id, user.student_id, user.roles
    )
    return ok(detail)


@router.get("/public/templates", response_model=ApiResponse[list[WorkflowTemplateOut]])
async def public_list_templates(
    db: DBDep, _user: CurrentUserDep, kind: str | None = Query(default=None)
) -> ApiResponse[list[WorkflowTemplateOut]]:
    return ok(await service.list_templates(db, kind))


# ===========================================================
# B. 学生侧：常见事务申请（FR-006 / FR-008 撤回）
# ===========================================================
@request_router.get("/types", response_model=ApiResponse[list[RequestTypeOut]])
async def list_types(db: DBDep, _user: CurrentUserDep) -> ApiResponse[list[RequestTypeOut]]:
    rows = await repo.list_request_types(db)
    return ok([RequestTypeOut.model_validate(r) for r in rows])


@request_router.get("/my", response_model=ApiResponse[Paginated[RequestBrief]])
async def list_my_requests(
    db: DBDep,
    user: CurrentUserDep,
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[RequestBrief]]:
    items, total = await service.list_my_requests(
        db, user.user_id, status=status, page=page, size=size
    )
    return ok(Paginated[RequestBrief](items=items, meta=PageMeta(page=page, size=size, total=total)))


@request_router.post("", response_model=ApiResponse[RequestDetail])
async def create_request(
    payload: RequestCreate, db: DBDep, user: ActiveStudentDep
) -> ApiResponse[RequestDetail]:
    detail = await service.create_draft_request(
        db, applicant_user_id=user.user_id, payload=payload
    )
    return ok(detail)


@request_router.patch("/{request_id}", response_model=ApiResponse[RequestDetail])
async def update_request(
    request_id: int, payload: RequestUpdate, db: DBDep, user: ActiveStudentDep
) -> ApiResponse[RequestDetail]:
    return ok(await service.update_draft_request(db, request_id, payload, user.user_id))


@request_router.post("/{request_id}/submit", response_model=ApiResponse[RequestDetail])
async def submit_request(
    request_id: int, db: DBDep, user: ActiveStudentDep
) -> ApiResponse[RequestDetail]:
    return ok(await service.submit_request(db, request_id, user.user_id))


@request_router.post("/{request_id}/withdraw", response_model=ApiResponse[RequestDetail])
async def withdraw_request(
    request_id: int,
    payload: ApprovalActionIn,
    db: DBDep,
    user: ActiveStudentDep,
) -> ApiResponse[RequestDetail]:
    return ok(await service.withdraw_request(db, request_id, payload.comment, user.user_id))


@request_router.post("/{request_id}/attachments", response_model=ApiResponse[AttachmentOut])
async def upload_attachment(
    request_id: int,
    db: DBDep,
    user: ActiveStudentDep,
    file: Annotated[UploadFile, File()],
) -> ApiResponse[AttachmentOut]:
    content = await file.read()
    row = await service.upload_request_attachment(
        db,
        request_id=request_id,
        filename=file.filename or "attachment.bin",
        content=content,
        content_type=file.content_type or "application/octet-stream",
        operator_id=user.user_id,
    )
    return ok(AttachmentOut.model_validate(row))


@request_router.get("/{request_id}", response_model=ApiResponse[RequestDetail])
async def get_request_detail(
    request_id: int, db: DBDep, user: CurrentUserDep
) -> ApiResponse[RequestDetail]:
    return ok(
        await service.get_request_detail(db, request_id, user.user_id, user.roles)
    )


@router.get(
    "/proof-preview/{request_id}",
    summary="下载/预览证明 PDF（FR-006）",
)
async def proof_preview(
    request_id: int, db: DBDep, user: CurrentUserDep
) -> StreamingResponse:
    # 复用查看权限：学生本人或管理角色
    await service.get_request_detail(db, request_id, user.user_id, user.roles)
    await ensure_export_permission(
        db,
        roles=user.roles,
        export_code=REQUEST_PROOF_PREVIEW,
        actor_user_id=user.user_id,
        actor_role=",".join(user.roles) or None,
        event_type="REQUEST",
        entity_code="REQUEST_PROOF",
        action="PROOF_PREVIEW_DENIED",
        entity_id=request_id,
        message="当前角色无权预览证明 PDF",
        detail=build_audit_detail(
            target={"request_id": request_id},
        ),
    )
    pdf_bytes, filename = await pdf_generator.generate_proof_pdf(db, request_id)
    await log_action(
        db,
        event_type="REQUEST",
        entity_code="REQUEST_PROOF",
        action="PROOF_PREVIEW",
        entity_id=request_id,
        actor_user_id=user.user_id,
        actor_role=",".join(user.roles) or None,
        detail=build_audit_detail(
            target={"request_id": request_id},
        ),
    )
    await db.commit()
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# ===========================================================
# C. 管理侧：模板维护 / 流程操作 / 提醒 / 审批工作台 / 类型维护
# ===========================================================

# -------- 流程模板 --------
@admin_router.get(
    "/workflow/templates", response_model=ApiResponse[list[WorkflowTemplateOut]]
)
async def admin_list_templates(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
    kind: str | None = Query(default=None),
) -> ApiResponse[list[WorkflowTemplateOut]]:
    return ok(await service.list_templates(db, kind))


@admin_router.post(
    "/workflow/templates", response_model=ApiResponse[WorkflowTemplateOut]
)
async def admin_upsert_template(
    payload: WorkflowTemplateIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[WorkflowTemplateOut]:
    return ok(
        await service.upsert_template_with_nodes(
            db, payload, user.user_id, ",".join(user.roles) or None
        )
    )


# -------- 流程启动 / 节点操作 / 列表 --------
@admin_router.post(
    "/workflow/students", response_model=ApiResponse[StudentWorkflowDetail]
)
async def admin_start_student_workflow(
    payload: StudentWorkflowStart,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[StudentWorkflowDetail]:
    return ok(
        await service.start_student_workflow(
            db,
            student_id=payload.student_id,
            template_code=payload.template_code,
            note=payload.note,
            operator_id=user.user_id,
            operator_role=",".join(user.roles) or None,
        )
    )


@admin_router.get(
    "/workflow/students", response_model=ApiResponse[Paginated[StudentWorkflowBrief]]
)
async def admin_list_student_workflows(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
    template_code: str | None = Query(default=None),
    grade_code: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[StudentWorkflowBrief]]:
    items, total = await service.list_admin_workflows(
        db,
        template_code=template_code,
        grade_code=grade_code,
        page=page,
        size=size,
    )
    return ok(
        Paginated[StudentWorkflowBrief](
            items=items, meta=PageMeta(page=page, size=size, total=total)
        )
    )


@admin_router.post(
    "/workflow/node-states/{state_id}/complete",
    response_model=ApiResponse[StudentWorkflowDetail],
)
async def admin_complete_node(
    state_id: int,
    payload: NodeCompleteIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[StudentWorkflowDetail]:
    return ok(
        await service.complete_node(
            db,
            state_id,
            evidence=payload.evidence,
            note=payload.note,
            operator_id=user.user_id,
            operator_role=",".join(user.roles) or None,
        )
    )


@admin_router.post(
    "/workflow/node-states/{state_id}/status",
    response_model=ApiResponse[StudentWorkflowDetail],
)
async def admin_mark_node_status(
    state_id: int,
    payload: NodeMarkStatusIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[StudentWorkflowDetail]:
    return ok(
        await service.mark_node_status(
            db,
            state_id,
            payload.status,
            payload.note,
            user.user_id,
            ",".join(user.roles) or None,
        )
    )


# -------- 提醒生成 --------
@admin_router.post("/workflow/reminders/generate", response_model=ApiResponse[dict])
async def admin_generate_reminders(
    payload: ReminderGenerateIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[dict]:
    count = await service.generate_reminders(
        db,
        as_of=payload.as_of_date,
        channel=payload.channel,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok({"created": count})


# -------- 申请类型维护 --------
@admin_router.get(
    "/request-types", response_model=ApiResponse[list[RequestTypeOut]]
)
async def admin_list_request_types(
    db: DBDep, _user: Annotated[CurrentUserDep, Depends(_EditorRole)]
) -> ApiResponse[list[RequestTypeOut]]:
    rows = await repo.list_request_types(db, active_only=False)
    return ok([RequestTypeOut.model_validate(r) for r in rows])


@admin_router.post(
    "/request-types", response_model=ApiResponse[RequestTypeOut]
)
async def admin_upsert_request_type(
    payload: RequestTypeIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_AdminRole)],
) -> ApiResponse[RequestTypeOut]:
    row = await service.upsert_request_type(
        db, payload, user.user_id, ",".join(user.roles) or None
    )
    return ok(RequestTypeOut.model_validate(row))


# -------- 审批工作台（FR-007 / FR-008）--------
@admin_router.get(
    "/requests", response_model=ApiResponse[Paginated[RequestBrief]]
)
async def admin_list_requests(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_ApproverRole)],
    q: str | None = None,
    type_code: str | None = None,
    status: str | None = None,
    in_review_only: bool = False,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[RequestBrief]]:
    items, total = await service.list_admin_requests(
        db,
        q=q,
        type_code=type_code,
        status=status,
        in_review_only=in_review_only,
        page=page,
        size=size,
    )
    return ok(
        Paginated[RequestBrief](items=items, meta=PageMeta(page=page, size=size, total=total))
    )


@admin_router.post(
    "/requests/{request_id}/claim", response_model=ApiResponse[RequestDetail]
)
async def admin_claim_request(
    request_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_ApproverRole)],
) -> ApiResponse[RequestDetail]:
    return ok(await service.claim_in_review(db, request_id, user.user_id, user.roles))


@admin_router.post(
    "/requests/{request_id}/approve", response_model=ApiResponse[RequestDetail]
)
async def admin_approve_request(
    request_id: int,
    payload: ApprovalActionIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_ApproverRole)],
) -> ApiResponse[RequestDetail]:
    return ok(
        await service.decide_request(
            db,
            request_id,
            approve=True,
            comment=payload.comment,
            operator_id=user.user_id,
            operator_roles=user.roles,
        )
    )


@admin_router.post(
    "/requests/{request_id}/offline",
    response_model=ApiResponse[RequestDetail],
    summary="v1.5 涉密/敏感事项转线下办理（终止在线流转）",
)
async def admin_mark_request_offline(
    request_id: int,
    payload: OfflineHandleIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_ApproverRole)],
) -> ApiResponse[RequestDetail]:
    return ok(
        await service.mark_request_offline(
            db,
            request_id,
            contact_info=payload.contact_info,
            note=payload.note,
            operator_id=user.user_id,
            operator_roles=user.roles,
        )
    )


@admin_router.post(
    "/requests/{request_id}/reject", response_model=ApiResponse[RequestDetail]
)
async def admin_reject_request(
    request_id: int,
    payload: ApprovalActionIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_ApproverRole)],
) -> ApiResponse[RequestDetail]:
    return ok(
        await service.decide_request(
            db,
            request_id,
            approve=False,
            comment=payload.comment,
            operator_id=user.user_id,
            operator_roles=user.roles,
        )
    )


@admin_router.post(
    "/requests/{request_id}/reopen",
    response_model=ApiResponse[RequestDetail],
    summary="FR-008 终态申请受控重开 / 重批",
)
async def admin_reopen_request(
    request_id: int,
    payload: ReopenRequestIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_ApproverRole)],
) -> ApiResponse[RequestDetail]:
    return ok(
        await service.reopen_request(
            db,
            request_id,
            comment=payload.comment,
            target_status=payload.target_status,
            operator_id=user.user_id,
            operator_roles=user.roles,
        )
    )


# ===========================================================
# D. 理论自测题库（FR-005）
# ===========================================================

# -------- 管理端：题库 CRUD --------
@admin_router.get(
    "/quiz/questions", response_model=ApiResponse[Paginated[QuizQuestionAdminOut]]
)
async def admin_list_quiz_questions(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
    topic: str | None = Query(default=None),
    qtype: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[QuizQuestionAdminOut]]:
    rows, total = await quiz_service.list_questions(
        db,
        topic=topic,
        qtype=qtype,
        is_active=is_active,
        keyword=q,
        page=page,
        size=size,
    )
    items = [QuizQuestionAdminOut.model_validate(r) for r in rows]
    return ok(
        Paginated[QuizQuestionAdminOut](
            items=items, meta=PageMeta(page=page, size=size, total=total)
        )
    )


@admin_router.post(
    "/quiz/questions", response_model=ApiResponse[QuizQuestionAdminOut]
)
async def admin_create_quiz_question(
    payload: QuizQuestionIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[QuizQuestionAdminOut]:
    row = await quiz_service.create_question(
        db,
        topic=payload.topic,
        qtype=payload.qtype,
        stem=payload.stem,
        options_json=[o.model_dump() for o in payload.options_json]
        if payload.options_json
        else None,
        correct_key=payload.correct_key,
        explanation=payload.explanation,
        difficulty=payload.difficulty,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(QuizQuestionAdminOut.model_validate(row))


@admin_router.patch(
    "/quiz/questions/{question_id}",
    response_model=ApiResponse[QuizQuestionAdminOut],
)
async def admin_update_quiz_question(
    question_id: int,
    payload: QuizQuestionUpdate,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[QuizQuestionAdminOut]:
    row = await quiz_service.update_question(
        db,
        question_id,
        topic=payload.topic,
        qtype=payload.qtype,
        stem=payload.stem,
        options_json=[o.model_dump() for o in payload.options_json]
        if payload.options_json is not None
        else None,
        correct_key=payload.correct_key,
        explanation=payload.explanation,
        difficulty=payload.difficulty,
        is_active=payload.is_active,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(QuizQuestionAdminOut.model_validate(row))


@admin_router.delete(
    "/quiz/questions/{question_id}", response_model=ApiResponse[dict]
)
async def admin_delete_quiz_question(
    question_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[dict]:
    await quiz_service.delete_question(
        db,
        question_id,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok({"id": question_id, "is_active": False})


# -------- 学生端：抽题 + 提交 + 记录 --------
@quiz_router.get("/draw", response_model=ApiResponse[QuizDrawOut])
async def student_draw_quiz(
    db: DBDep,
    user: CurrentUserDep,
    topic: str | None = Query(default=None),
    qtype: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=50),
) -> ApiResponse[QuizDrawOut]:
    if user.student_id is None:
        raise BizError("仅学生可参加自测", code=40305, http_status=403)
    batch_id, rows = await quiz_service.draw_quiz(
        db, topic=topic, qtype=qtype, difficulty=difficulty, limit=limit
    )
    questions = [QuizQuestionStudentOut.model_validate(r) for r in rows]
    return ok(QuizDrawOut(batch_id=batch_id, questions=questions))


@quiz_router.post("/submit", response_model=ApiResponse[QuizSubmitOut])
async def student_submit_quiz(
    payload: QuizSubmitIn,
    db: DBDep,
    user: CurrentUserDep,
) -> ApiResponse[QuizSubmitOut]:
    if user.student_id is None:
        raise BizError("仅学生可提交自测", code=40305, http_status=403)
    result = await quiz_service.submit_quiz(
        db,
        student_id=user.student_id,
        batch_id=payload.batch_id,
        answers=[a.model_dump() for a in payload.answers],
        operator_id=user.user_id,
    )
    return ok(QuizSubmitOut(**result))


@quiz_router.get("/my/records", response_model=ApiResponse[list[dict]])
async def student_list_my_records(
    db: DBDep,
    user: CurrentUserDep,
    batch_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> ApiResponse[list[dict]]:
    if user.student_id is None:
        raise BizError("仅学生可查看本人记录", code=40305, http_status=403)
    rows = await quiz_service.list_my_records(
        db, student_id=user.student_id, batch_id=batch_id, limit=limit
    )
    return ok(
        [
            {
                "id": r.id,
                "question_id": r.question_id,
                "batch_id": r.batch_id,
                "answer": r.answer,
                "is_correct": r.is_correct,
                "score": r.score,
                "submitted_at": r.submitted_at.isoformat(),
            }
            for r in rows
        ]
    )
