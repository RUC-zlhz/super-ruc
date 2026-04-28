"""workflow 业务服务层 — 党团流程 + 事务申请。"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.enforcement import audit_forbidden_and_raise
from app.audit.service import build_audit_detail, log_action
from app.auth.models import Student
from app.core.config import settings
from app.core.exceptions import BizError, ConflictError, NotFoundError
from app.core.storage import put_object
from app.workflow import repository as repo
from app.workflow.models import (
    REMINDER_STATUS_PENDING,
    REQUEST_ACTION_APPROVE,
    REQUEST_ACTION_OFFLINE,
    REQUEST_ACTION_REJECT,
    REQUEST_ACTION_RESUBMIT,
    REQUEST_ACTION_SUBMIT,
    REQUEST_ACTION_WITHDRAW,
    REQUEST_STATUS_DRAFT,
    REQUEST_STATUS_REJECTED,
    REQUEST_STATUS_SUBMITTED,
    WORKFLOW_NODE_DONE,
    WORKFLOW_NODE_OVERDUE,
    WORKFLOW_NODE_PENDING,
    Request,
    RequestAttachment,
    StudentWorkflow,
    StudentWorkflowNode,
    WorkflowNode,
    WorkflowTemplate,
)
from app.workflow.schemas import (
    ApprovalRecordOut,
    AttachmentOut,
    RequestBrief,
    RequestDetail,
    StudentWorkflowBrief,
    StudentWorkflowDetail,
    StudentWorkflowNodeOut,
    WorkflowNodeOut,
    WorkflowTemplateOut,
)
from app.workflow.state_machine import (
    REQUEST_EDITABLE_STATUSES,
    ApprovalStateMachine,
    NodeStateMachine,
)

logger = logging.getLogger(__name__)


# ======================================================================
# A. 党团流程 — 模板维护（FR-005）
# ======================================================================
def template_to_out(tpl: WorkflowTemplate) -> WorkflowTemplateOut:
    return WorkflowTemplateOut(
        id=tpl.id,
        code=tpl.code,
        name=tpl.name,
        kind=tpl.kind,
        description=tpl.description,
        version_label=tpl.version_label,
        is_active=tpl.is_active,
        updated_at=tpl.updated_at,
        nodes=[WorkflowNodeOut.model_validate(n) for n in (tpl.nodes or [])],
    )


async def upsert_template_with_nodes(
    db: AsyncSession, payload, operator_id: int, operator_role: str | None
) -> WorkflowTemplateOut:
    """创建或整体替换模板节点（简化版）。"""
    existing = await repo.get_template_by_code(db, payload.code)
    if existing is None:
        tpl = await repo.create_template(
            db,
            code=payload.code,
            name=payload.name,
            kind=payload.kind,
            description=payload.description,
            version_label=payload.version_label,
            is_active=True,
        )
    else:
        tpl = existing
        tpl.name = payload.name
        tpl.kind = payload.kind
        tpl.description = payload.description
        tpl.version_label = payload.version_label
        await repo.delete_nodes_for_template(db, tpl.id)

    for n in payload.nodes:
        await repo.add_node(
            db,
            tpl.id,
            code=n.code,
            name=n.name,
            sort_order=n.sort_order,
            stage_group=n.stage_group,
            required_task=n.required_task,
            trigger_rule=n.trigger_rule,
            due_rule_days=n.due_rule_days,
            reminder_lead_days=n.reminder_lead_days,
            is_terminal=n.is_terminal,
            is_active=n.is_active,
        )

    await log_action(
        db,
        event_type="WORKFLOW",
        entity_code="WORKFLOW_TEMPLATE",
        action="UPSERT",
        entity_id=tpl.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"code": tpl.code, "nodes": len(payload.nodes)},
    )
    await db.commit()
    await db.refresh(tpl)
    # 重新加载节点
    tpl = await repo.get_template_by_code(db, tpl.code)
    assert tpl is not None
    return template_to_out(tpl)


async def list_templates(
    db: AsyncSession, kind: str | None
) -> list[WorkflowTemplateOut]:
    rows = await repo.list_templates(db, kind=kind)
    return [template_to_out(r) for r in rows]


# ======================================================================
# A.2 学生侧流程视图（FR-004） + 管理启动流程、完成节点、延期等
# ======================================================================
def _node_state_to_out(state: StudentWorkflowNode) -> StudentWorkflowNodeOut:
    n: WorkflowNode = state.node
    return StudentWorkflowNodeOut(
        id=state.id,
        node_id=state.node_id,
        node_code=n.code,
        node_name=n.name,
        sort_order=n.sort_order,
        stage_group=n.stage_group,
        required_task=n.required_task,
        status=state.status,
        triggered_at=state.triggered_at,
        due_date=state.due_date,
        completed_at=state.completed_at,
        evidence=state.evidence,
        note=state.note,
    )


def _workflow_to_detail(sw: StudentWorkflow) -> StudentWorkflowDetail:
    states = sorted(
        sw.node_states, key=lambda s: (s.node.sort_order if s.node else 0, s.id)
    )
    current_name = None
    next_hint = None
    if sw.current_node_id:
        cur = next((s for s in states if s.node_id == sw.current_node_id), None)
        if cur and cur.node:
            current_name = cur.node.name
            next_hint = cur.node.required_task
    return StudentWorkflowDetail(
        id=sw.id,
        template_code=sw.template.code,
        template_name=sw.template.name,
        kind=sw.template.kind,
        status=sw.status,
        started_at=sw.started_at,
        completed_at=sw.completed_at,
        current_node_id=sw.current_node_id,
        current_node_name=current_name,
        next_action_hint=next_hint,
        nodes=[_node_state_to_out(s) for s in states],
    )


async def start_student_workflow(
    db: AsyncSession,
    *,
    student_id: int,
    template_code: str,
    note: str | None,
    operator_id: int,
    operator_role: str | None,
) -> StudentWorkflowDetail:
    tpl = await repo.get_template_by_code(db, template_code)
    if tpl is None or not tpl.is_active:
        raise NotFoundError("流程模板不存在或已停用")
    student = await db.get(Student, student_id)
    if student is None:
        raise NotFoundError(f"学生不存在：{student_id}")

    exist = await repo.find_active_student_workflow(db, student_id, tpl.id)
    if exist is not None:
        raise ConflictError("该学生在此模板下已有进行中的流程")

    nodes = await repo.list_nodes(db, tpl.id)
    if not nodes:
        raise BizError("模板尚未配置节点", code=40013)

    sw = await repo.create_student_workflow(
        db,
        student_id=student_id,
        template_id=tpl.id,
        status="ACTIVE",
        note=note,
    )

    # 初始化节点状态：第一个节点 trigger；其余 PENDING
    for idx, n in enumerate(nodes):
        triggered = None
        due = None
        status = WORKFLOW_NODE_PENDING
        if idx == 0:
            triggered = datetime.now(UTC)
            if n.due_rule_days is not None:
                due = (triggered + timedelta(days=n.due_rule_days)).date()
        await repo.add_student_node_state(
            db,
            workflow_id=sw.id,
            node_id=n.id,
            status=status,
            triggered_at=triggered,
            due_date=due,
        )

    sw.current_node_id = nodes[0].id
    await log_action(
        db,
        event_type="WORKFLOW",
        entity_code="STUDENT_WORKFLOW",
        action="START",
        entity_id=sw.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"student_id": student_id, "template": template_code},
    )
    await db.commit()
    sw_full = await repo.get_student_workflow(db, sw.id)
    assert sw_full is not None
    return _workflow_to_detail(sw_full)


async def get_workflow_for_student(
    db: AsyncSession, workflow_id: int, viewer_student_id: int | None, viewer_roles: list[str]
) -> StudentWorkflowDetail:
    sw = await repo.get_student_workflow(db, workflow_id)
    if sw is None:
        raise NotFoundError("流程实例不存在")
    # 学生仅能查看本人；老师/管理员按角色已放行（路由层做）
    if viewer_student_id is not None and sw.student_id != viewer_student_id:
        allowed = {"SUPER_ADMIN", "COLLEGE_LEADER", "COUNSELOR", "HEAD_TEACHER",
                   "YOUTH_LEAGUE_TEACHER", "PARTY_BUILD_TEACHER", "CLASS_CADRE"}
        if not (set(viewer_roles) & allowed):
            raise BizError("无权查看该流程", code=40301, http_status=403)
    return _workflow_to_detail(sw)


async def list_my_workflows(
    db: AsyncSession, student_id: int
) -> list[StudentWorkflowDetail]:
    rows = await repo.list_student_workflows_for_student(db, student_id)
    return [_workflow_to_detail(r) for r in rows]


async def complete_node(
    db: AsyncSession,
    state_id: int,
    evidence: str | None,
    note: str | None,
    operator_id: int,
    operator_role: str | None,
) -> StudentWorkflowDetail:
    state = await repo.get_student_node_state(db, state_id)
    if state is None:
        raise NotFoundError("节点状态不存在")
    NodeStateMachine.assert_completable(state.status)

    state.status = WORKFLOW_NODE_DONE
    state.completed_at = datetime.now(UTC)
    state.completed_by = operator_id
    state.evidence = evidence
    state.note = note

    sw = state.workflow
    # 触发下一节点
    states = sorted(
        sw.node_states, key=lambda s: (s.node.sort_order if s.node else 0, s.id)
    )
    idx = next((i for i, s in enumerate(states) if s.id == state.id), -1)
    next_state = states[idx + 1] if idx >= 0 and idx + 1 < len(states) else None

    if next_state is not None:
        next_state.status = WORKFLOW_NODE_PENDING
        next_state.triggered_at = datetime.now(UTC)
        if next_state.node and next_state.node.due_rule_days is not None:
            next_state.due_date = (
                next_state.triggered_at + timedelta(days=next_state.node.due_rule_days)
            ).date()
        sw.current_node_id = next_state.node_id
    else:
        sw.current_node_id = None
        sw.status = "COMPLETED"
        sw.completed_at = datetime.now(UTC)

    await log_action(
        db,
        event_type="WORKFLOW",
        entity_code="STUDENT_WORKFLOW_NODE",
        action="COMPLETE",
        entity_id=state.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    full = await repo.get_student_workflow(db, sw.id)
    assert full is not None
    return _workflow_to_detail(full)


async def mark_node_status(
    db: AsyncSession,
    state_id: int,
    new_status: str,
    note: str | None,
    operator_id: int,
    operator_role: str | None,
) -> StudentWorkflowDetail:
    NodeStateMachine.assert_manual_status_allowed(new_status)
    state = await repo.get_student_node_state(db, state_id)
    if state is None:
        raise NotFoundError("节点状态不存在")
    if state.status == WORKFLOW_NODE_DONE:
        raise ConflictError("已完成的节点不可再改状态")
    state.status = new_status
    if note:
        state.note = note
    await log_action(
        db,
        event_type="WORKFLOW",
        entity_code="STUDENT_WORKFLOW_NODE",
        action="MARK_STATUS",
        entity_id=state.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"new_status": new_status},
    )
    await db.commit()
    full = await repo.get_student_workflow(db, state.workflow_id)
    assert full is not None
    return _workflow_to_detail(full)


async def list_admin_workflows(
    db: AsyncSession,
    *,
    template_code: str | None,
    grade_code: str | None,
    page: int,
    size: int,
) -> tuple[list[StudentWorkflowBrief], int]:
    rows, total = await repo.list_pending_workflows_admin(
        db, template_code=template_code, grade_code=grade_code, page=page, size=size
    )
    items: list[StudentWorkflowBrief] = []
    for sw in rows:
        # 查学生信息（懒加载避免额外 JOIN；此处单条查询即可）
        stu = await db.get(Student, sw.student_id)
        cur_state = None
        if sw.current_node_id:
            cur_state = next(
                (s for s in sw.node_states if s.node_id == sw.current_node_id), None
            )
        items.append(
            StudentWorkflowBrief(
                id=sw.id,
                student_id=sw.student_id,
                student_no=stu.student_no if stu else None,
                student_name=stu.full_name if stu else None,
                template_code=sw.template.code,
                template_name=sw.template.name,
                current_node_name=cur_state.node.name if cur_state and cur_state.node else None,
                current_node_status=cur_state.status if cur_state else None,
                due_date=cur_state.due_date if cur_state else None,
            )
        )
    return items, total


# ======================================================================
# A.3 提醒（FR-005）
# ======================================================================
async def generate_reminders(
    db: AsyncSession,
    *,
    as_of: date | None,
    channel: str,
    operator_id: int,
    operator_role: str | None,
) -> int:
    as_of = as_of or date.today()
    states = await repo.list_pending_nodes_for_reminder(db, as_of=as_of)
    created = 0
    for s in states:
        if s.due_date is None:
            continue
        lead = (s.node.reminder_lead_days if s.node and s.node.reminder_lead_days is not None else 0)
        remind_on = s.due_date - timedelta(days=lead)
        if remind_on > as_of:
            continue
        # 逾期也自动调整节点状态
        if s.due_date < as_of and s.status == WORKFLOW_NODE_PENDING:
            s.status = WORKFLOW_NODE_OVERDUE
        await repo.create_reminder(
            db,
            workflow_node_state_id=s.id,
            student_id=s.workflow.student_id if s.workflow else 0,
            reminder_date=as_of,
            channel=channel,
            status=REMINDER_STATUS_PENDING,
            message=f"节点 {s.node.name} 需要跟进，截止 {s.due_date}",
        )
        created += 1
    await log_action(
        db,
        event_type="WORKFLOW",
        entity_code="REMINDER",
        action="GENERATE",
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"as_of": str(as_of), "count": created},
    )
    await db.commit()
    return created


# ======================================================================
# B. 申请 — 工厂方法与辅助函数
# ======================================================================
def _generate_request_no(type_code: str) -> str:
    ts = datetime.now(UTC).strftime("%y%m%d%H%M%S")
    return f"{type_code[:4].upper()}-{ts}-{uuid.uuid4().hex[:6].upper()}"


async def _ensure_applicant_student_id(
    db: AsyncSession, user_id: int, student_id: int | None
) -> int | None:
    from app.auth.models import User  # 避免循环
    if student_id:
        return student_id
    user = await db.get(User, user_id)
    return user.student_id if user and user.student_id else None


def _request_to_detail(req: Request) -> RequestDetail:
    return RequestDetail(
        id=req.id,
        request_no=req.request_no,
        type_code=req.type_code,
        type_name=req.type_ref.name if req.type_ref else req.type_code,
        category=req.type_ref.category if req.type_ref else "OTHER",
        title=req.title,
        summary=req.summary,
        form_data=req.form_data or {},
        status=req.status,
        revision=req.revision,
        applicant_user_id=req.applicant_user_id,
        applicant_student_id=req.applicant_student_id,
        submitted_at=req.submitted_at,
        decided_at=req.decided_at,
        decided_by=req.decided_by,
        decision_comment=req.decision_comment,
        withdrawn_at=req.withdrawn_at,
        attachments=[AttachmentOut.model_validate(a) for a in (req.attachments or [])],
        approval_records=[
            ApprovalRecordOut.model_validate(r) for r in (req.approval_records or [])
        ],
    )


def _request_to_brief(req: Request) -> RequestBrief:
    return RequestBrief(
        id=req.id,
        request_no=req.request_no,
        type_code=req.type_code,
        title=req.title,
        status=req.status,
        revision=req.revision,
        applicant_user_id=req.applicant_user_id,
        applicant_student_id=req.applicant_student_id,
        submitted_at=req.submitted_at,
        updated_at=req.updated_at,
    )


# ======================================================================
# B.1 学生侧：创建 + 提交（FR-006）
# ======================================================================
async def upload_request_attachment(
    db: AsyncSession,
    *,
    request_id: int,
    filename: str,
    content: bytes,
    content_type: str,
    operator_id: int,
) -> RequestAttachment:
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    if req.applicant_user_id != operator_id:
        raise BizError("无权上传到该申请", code=40302, http_status=403)
    if req.status not in REQUEST_EDITABLE_STATUSES:
        raise BizError("当前状态不允许上传附件", code=40015)
    max_bytes = settings.UPLOAD_MAX_SIZE_BYTES
    if len(content) > max_bytes:
        raise BizError(
            f"文件超过 {settings.UPLOAD_MAX_SIZE_MB} MB", code=41300, http_status=413
        )

    checksum = hashlib.sha256(content).hexdigest()
    bucket = settings.MINIO_BUCKET_ATTACHMENT
    object_key = f"requests/{req.id}/{uuid.uuid4().hex}_{filename}"
    try:
        put_object(
            bucket=bucket,
            object_key=object_key,
            data=content,
            length=len(content),
            content_type=content_type or "application/octet-stream",
        )
    except Exception as e:
        logger.exception("Object storage upload failed")
        raise BizError(f"附件上传失败：{e}", code=50002, http_status=500) from e

    row = await repo.add_attachment(
        db,
        request_id=req.id,
        filename=filename,
        object_bucket=bucket,
        object_key=object_key,
        file_size=len(content),
        mime_type=content_type,
        checksum_sha256=checksum,
        uploaded_by=operator_id,
    )
    await db.commit()
    await db.refresh(row)
    return row


async def create_draft_request(
    db: AsyncSession,
    *,
    applicant_user_id: int,
    payload,
) -> RequestDetail:
    rt = await repo.get_request_type_by_code(db, payload.type_code)
    if rt is None or not rt.is_active:
        raise NotFoundError(f"事务类型不存在或已停用：{payload.type_code}")

    applicant_student_id = await _ensure_applicant_student_id(
        db, applicant_user_id, None
    )

    req = await repo.create_request(
        db,
        request_no=_generate_request_no(rt.code),
        type_id=rt.id,
        type_code=rt.code,
        applicant_user_id=applicant_user_id,
        applicant_student_id=applicant_student_id,
        title=payload.title,
        form_data=payload.form_data,
        summary=payload.summary,
        status=REQUEST_STATUS_DRAFT,
        revision=1,
    )
    await log_action(
        db,
        event_type="REQUEST",
        entity_code="REQUEST",
        action="CREATE",
        entity_id=req.id,
        actor_user_id=applicant_user_id,
        detail={"type": rt.code},
    )
    await db.commit()
    await db.refresh(req)
    return _request_to_detail(req)


async def submit_request(
    db: AsyncSession, request_id: int, operator_id: int
) -> RequestDetail:
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    if req.applicant_user_id != operator_id:
        raise BizError("无权提交该申请", code=40302, http_status=403)
    ApprovalStateMachine.assert_editable(req.status)

    rt = req.type_ref
    if rt and rt.attachment_required and not (req.attachments or []):
        raise BizError("此事务要求上传附件", code=40017)

    action = (
        REQUEST_ACTION_RESUBMIT
        if req.status == REQUEST_STATUS_REJECTED
        else REQUEST_ACTION_SUBMIT
    )
    result = ApprovalStateMachine.transition(req.status, action)
    status_before = result.status_before
    if status_before == REQUEST_STATUS_REJECTED:
        req.revision += 1
    req.status = result.status_after
    assert req.status == REQUEST_STATUS_SUBMITTED
    req.submitted_at = datetime.now(UTC)
    req.decided_at = None
    req.decided_by = None
    req.decision_comment = None
    req.withdrawn_at = None

    await repo.add_approval_record(
        db,
        request_id=req.id,
        revision=req.revision,
        action=action,
        status_before=status_before,
        status_after=req.status,
        operator_id=operator_id,
        operator_role="STUDENT",
    )
    await log_action(
        db,
        event_type="REQUEST",
        entity_code="REQUEST",
        action=action,
        entity_id=req.id,
        actor_user_id=operator_id,
    )
    await db.commit()
    await db.refresh(req)
    return _request_to_detail(req)


async def update_draft_request(
    db: AsyncSession, request_id: int, payload, operator_id: int
) -> RequestDetail:
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    if req.applicant_user_id != operator_id:
        raise BizError("无权修改该申请", code=40302, http_status=403)
    ApprovalStateMachine.assert_editable(req.status)

    changed = payload.model_dump(exclude_unset=True)
    for k, v in changed.items():
        setattr(req, k, v)
    await db.commit()
    await db.refresh(req)
    return _request_to_detail(req)


async def withdraw_request(
    db: AsyncSession, request_id: int, comment: str | None, operator_id: int
) -> RequestDetail:
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    if req.applicant_user_id != operator_id:
        raise BizError("无权撤回该申请", code=40302, http_status=403)

    rt = req.type_ref
    if rt and not rt.allow_withdraw:
        raise BizError("该类型申请不允许撤回", code=40020)
    if rt and rt.withdraw_hours_limit and req.submitted_at is not None:
        deadline = req.submitted_at + timedelta(hours=rt.withdraw_hours_limit)
        if datetime.now(UTC) > deadline:
            raise BizError(
                f"已超过撤回期限（{rt.withdraw_hours_limit} 小时）", code=40021
            )

    result = ApprovalStateMachine.transition(req.status, REQUEST_ACTION_WITHDRAW)
    status_before = result.status_before
    req.status = result.status_after
    req.withdrawn_at = datetime.now(UTC)

    await repo.add_approval_record(
        db,
        request_id=req.id,
        revision=req.revision,
        action=REQUEST_ACTION_WITHDRAW,
        status_before=status_before,
        status_after=req.status,
        operator_id=operator_id,
        operator_role="STUDENT",
        comment=comment,
    )
    await log_action(
        db,
        event_type="REQUEST",
        entity_code="REQUEST",
        action=REQUEST_ACTION_WITHDRAW,
        entity_id=req.id,
        actor_user_id=operator_id,
        detail={"comment": comment},
    )
    await db.commit()
    await db.refresh(req)
    return _request_to_detail(req)


# ======================================================================
# B.2 管理侧：工作台 + 审批（FR-007 / FR-008）
# ======================================================================
async def list_my_requests(
    db: AsyncSession,
    applicant_user_id: int,
    *,
    status: str | None,
    page: int,
    size: int,
) -> tuple[list[RequestBrief], int]:
    rows, total = await repo.list_requests_for_applicant(
        db, applicant_user_id, status=status, page=page, size=size
    )
    return [_request_to_brief(r) for r in rows], total


async def list_admin_requests(
    db: AsyncSession,
    *,
    q: str | None,
    type_code: str | None,
    status: str | None,
    in_review_only: bool,
    page: int,
    size: int,
) -> tuple[list[RequestBrief], int]:
    rows, total = await repo.list_requests_admin(
        db,
        q=q,
        type_code=type_code,
        status=status,
        in_review_only=in_review_only,
        page=page,
        size=size,
    )
    return [_request_to_brief(r) for r in rows], total


async def get_request_detail(
    db: AsyncSession, request_id: int, viewer_user_id: int, viewer_roles: list[str]
) -> RequestDetail:
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    # 学生仅能查看自己提交的，其他角色按路由层放行
    admin_roles = {
        "SUPER_ADMIN", "COLLEGE_LEADER", "COUNSELOR", "HEAD_TEACHER",
        "YOUTH_LEAGUE_TEACHER", "PARTY_BUILD_TEACHER", "CLASS_CADRE",
    }
    if req.applicant_user_id != viewer_user_id and not (set(viewer_roles) & admin_roles):
        await audit_forbidden_and_raise(
            db,
            event_type="REQUEST",
            entity_code="REQUEST",
            action="READ_DETAIL_DENIED",
            entity_id=req.id,
            actor_user_id=viewer_user_id,
            actor_role=",".join(viewer_roles) or None,
            message="无权查看该申请",
            code=40303,
            detail=build_audit_detail(
                target={"request_id": req.id},
            ),
        )
    detail = _request_to_detail(req)
    await log_action(
        db,
        event_type="REQUEST",
        entity_code="REQUEST",
        action="READ_DETAIL",
        entity_id=req.id,
        actor_user_id=viewer_user_id,
        actor_role=",".join(viewer_roles) or None,
        detail=build_audit_detail(
            target={"request_id": req.id},
            metrics={"attachment_count": len(detail.attachments)},
        ),
    )
    await db.commit()
    return detail


def _approver_has_role(rt, roles: list[str]) -> bool:
    if not rt or not rt.approver_roles:
        return True
    allowed = {r.strip() for r in rt.approver_roles.split(",") if r.strip()}
    return bool(set(roles) & allowed)


async def decide_request(
    db: AsyncSession,
    request_id: int,
    *,
    approve: bool,
    comment: str | None,
    operator_id: int,
    operator_roles: list[str],
) -> RequestDetail:
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    if not _approver_has_role(req.type_ref, operator_roles):
        raise BizError("无权审批该类型申请", code=40304, http_status=403)

    action = REQUEST_ACTION_APPROVE if approve else REQUEST_ACTION_REJECT
    result = ApprovalStateMachine.transition(req.status, action)
    status_before = result.status_before
    now = datetime.now(UTC)
    req.status = result.status_after
    req.decided_at = now
    req.decided_by = operator_id
    req.decision_comment = comment

    await repo.add_approval_record(
        db,
        request_id=req.id,
        revision=req.revision,
        action=action,
        status_before=status_before,
        status_after=req.status,
        operator_id=operator_id,
        operator_role=",".join(operator_roles),
        comment=comment,
    )
    await log_action(
        db,
        event_type="REQUEST",
        entity_code="REQUEST",
        action=action,
        entity_id=req.id,
        actor_user_id=operator_id,
        actor_role=",".join(operator_roles),
        detail={"comment": comment},
    )
    await db.commit()
    await db.refresh(req)
    return _request_to_detail(req)


async def mark_request_offline(
    db: AsyncSession,
    request_id: int,
    *,
    contact_info: str,
    note: str | None,
    operator_id: int,
    operator_roles: list[str],
) -> RequestDetail:
    """v1.5 涉密 / 敏感事项转线下办理。

    终止在线流转：状态 → OFFLINE_HANDLED；审批历史保留；
    contact_info 将在学生端以"线下办理提示"卡片展示（如老师姓名 + 电话）。
    """
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    if not _approver_has_role(req.type_ref, operator_roles):
        raise BizError("无权审批该类型申请", code=40304, http_status=403)

    result = ApprovalStateMachine.transition(req.status, REQUEST_ACTION_OFFLINE)
    status_before = result.status_before
    now = datetime.now(UTC)
    req.status = result.status_after
    req.decided_at = now
    req.decided_by = operator_id
    req.decision_comment = (
        f"[转线下] 联系方式：{contact_info}"
        + (f"\n说明：{note}" if note else "")
    )

    await repo.add_approval_record(
        db,
        request_id=req.id,
        revision=req.revision,
        action=REQUEST_ACTION_OFFLINE,
        status_before=status_before,
        status_after=req.status,
        operator_id=operator_id,
        operator_role=",".join(operator_roles),
        comment=req.decision_comment,
    )
    await log_action(
        db,
        event_type="REQUEST",
        entity_code="REQUEST",
        action=REQUEST_ACTION_OFFLINE,
        entity_id=req.id,
        actor_user_id=operator_id,
        actor_role=",".join(operator_roles),
        detail={"contact": contact_info, "note": note},
    )
    await db.commit()
    await db.refresh(req)
    return _request_to_detail(req)


async def claim_in_review(
    db: AsyncSession, request_id: int, operator_id: int, operator_roles: list[str]
) -> RequestDetail:
    """把 SUBMITTED → IN_REVIEW，表示某审批人已认领。"""
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    if not _approver_has_role(req.type_ref, operator_roles):
        raise BizError("无权认领该申请", code=40304, http_status=403)
    result = ApprovalStateMachine.transition(req.status, "CLAIM")
    status_before = result.status_before
    req.status = result.status_after
    await repo.add_approval_record(
        db,
        request_id=req.id,
        revision=req.revision,
        action="CLAIM",
        status_before=status_before,
        status_after=req.status,
        operator_id=operator_id,
        operator_role=",".join(operator_roles),
    )
    await log_action(
        db,
        event_type="REQUEST",
        entity_code="REQUEST",
        action="CLAIM",
        entity_id=req.id,
        actor_user_id=operator_id,
        actor_role=",".join(operator_roles),
    )
    await db.commit()
    await db.refresh(req)
    return _request_to_detail(req)


# ======================================================================
# B.3 申请类型维护
# ======================================================================
async def upsert_request_type(
    db: AsyncSession, payload, operator_id: int, operator_role: str | None
):
    existing = await repo.get_request_type_by_code(db, payload.code)
    if existing is None:
        row = await repo.create_request_type(
            db, **payload.model_dump()
        )
        await log_action(
            db,
            event_type="WORKFLOW",
            entity_code="REQUEST_TYPE",
            action="CREATE",
            entity_id=row.id,
            actor_user_id=operator_id,
            actor_role=operator_role,
        )
    else:
        for k, v in payload.model_dump(exclude={"code"}).items():
            setattr(existing, k, v)
        row = existing
        await log_action(
            db,
            event_type="WORKFLOW",
            entity_code="REQUEST_TYPE",
            action="UPDATE",
            entity_id=row.id,
            actor_user_id=operator_id,
            actor_role=operator_role,
        )
    await db.commit()
    await db.refresh(row)
    return row
