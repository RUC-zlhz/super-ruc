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
from app.auth.role_codes import ROLE_CODE_COLLABORATOR_ROLES, normalize_role_codes
from app.auth.scopes import StudentScopeSet, split_student_scope_codes, student_in_scope
from app.core.config import settings
from app.core.exceptions import (
    BizError,
    ConflictError,
    NotFoundError,
)
from app.core.exceptions import (
    PermissionError as AppPermissionError,
)
from app.core.storage import put_object
from app.notice import repository as notice_repo
from app.notice.models import (
    WECHAT_SUBSCRIBE_SCENE_REQUEST_STATUS,
    WECHAT_SUBSCRIBE_SCENE_WORKFLOW_REMINDER,
)
from app.notice.service import (
    create_system_in_app_notice_for_student,
    send_wechat_subscribe_for_delivery,
)
from app.workflow import pdf_generator
from app.workflow import repository as repo
from app.workflow.models import (
    REMINDER_RUN_STATUS_COMPLETED,
    REMINDER_RUN_STATUS_FAILED,
    REMINDER_RUN_STATUS_RUNNING,
    REMINDER_STATUS_CANCELLED,
    REMINDER_STATUS_FAILED,
    REMINDER_STATUS_PENDING,
    REMINDER_STATUS_SENT,
    REQUEST_ACTION_APPROVE,
    REQUEST_ACTION_OFFLINE,
    REQUEST_ACTION_REJECT,
    REQUEST_ACTION_REOPEN,
    REQUEST_ACTION_RESUBMIT,
    REQUEST_ACTION_SUBMIT,
    REQUEST_ACTION_WITHDRAW,
    REQUEST_STATUS_DRAFT,
    REQUEST_STATUS_REJECTED,
    REQUEST_STATUS_SUBMITTED,
    WORKFLOW_NODE_DONE,
    WORKFLOW_NODE_MANUAL,
    WORKFLOW_NODE_MATERIAL_SUBMITTED,
    WORKFLOW_NODE_OVERDUE,
    WORKFLOW_NODE_PENDING,
    ProofTemplate,
    Request,
    RequestAttachment,
    StudentWorkflow,
    StudentWorkflowNode,
    WorkflowNode,
    WorkflowReminder,
    WorkflowReminderRun,
    WorkflowTemplate,
)
from app.workflow.schemas import (
    ApprovalRecordOut,
    AttachmentOut,
    ProofTemplateIn,
    ProofTemplateOut,
    ProofTemplatePreviewIn,
    ProofTemplatePreviewOut,
    ReminderAdminOut,
    ReminderRunOut,
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

_REQUEST_GLOBAL_ROLES = {
    "SUPER_ADMIN",
    "COLLEGE_LEADER",
    "COUNSELOR",
    "HEAD_TEACHER",
    "YOUTH_LEAGUE_TEACHER",
    "PARTY_BUILD_TEACHER",
}
_REQUEST_COLLABORATOR_ROLES = set(ROLE_CODE_COLLABORATOR_ROLES)
_WORKFLOW_START_SCOPED_ROLES = {
    "COUNSELOR",
    "HEAD_TEACHER",
    "YOUTH_LEAGUE_TEACHER",
    "PARTY_BUILD_TEACHER",
    *ROLE_CODE_COLLABORATOR_ROLES,
}
_WORKFLOW_GLOBAL_ROLES = {"SUPER_ADMIN", "COLLEGE_LEADER"}
_WORKFLOW_SCOPED_ROLES = {
    "COUNSELOR",
    "HEAD_TEACHER",
    "YOUTH_LEAGUE_TEACHER",
    "PARTY_BUILD_TEACHER",
    *ROLE_CODE_COLLABORATOR_ROLES,
}

_STUDENT_MATERIAL_REQUIRED_NODE_CODES = frozenset(
    {
        "APPLY_SUBMIT",
        "PARTY_SCHOOL",
        "POLITICAL_REVIEW",
        "PARTY_02_RECEIVE_APPLICATION_TALK",
        "PARTY_05_INSPECTION",
        "PARTY_10_SHORT_TRAINING",
        "PARTY_23_SUBMIT_FULL_MEMBER_APPLICATION",
        "LEAGUE_APPLY",
        "LEAGUE_LECTURE",
        "YOUTH_01_SUBMIT_APPLICATION",
        "YOUTH_10_FILL_APPLICATION_FORM",
    }
)

_STUDENT_MATERIAL_TASK_MARKERS = (
    "学生提交",
    "学生递交",
    "提交入党申请书",
    "递交入党申请书",
    "提交入团申请书",
    "递交入团申请书",
    "提交转正申请书",
    "递交转正申请书",
    "提交思想汇报",
    "递交思想汇报",
    "提交书面申请",
    "提交申请",
    "填写入团志愿书",
    "上传材料",
    "提交材料",
    "补交材料",
    "补充材料",
    "提交证明",
    "提交结业证",
)


def _is_student_material_required(node: WorkflowNode | None) -> bool:
    if node is None:
        return False
    code = (node.code or "").strip().upper()
    if code in _STUDENT_MATERIAL_REQUIRED_NODE_CODES:
        return True
    text = f"{node.name or ''} {node.required_task or ''}"
    return any(marker in text for marker in _STUDENT_MATERIAL_TASK_MARKERS)


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
            reminder_enabled=n.reminder_enabled,
            reminder_channel=n.reminder_channel,
            repeat_interval_days=n.repeat_interval_days,
            max_reminders=n.max_reminders,
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
    db: AsyncSession, kind: str | None, *, active_only: bool = True
) -> list[WorkflowTemplateOut]:
    rows = await repo.list_templates(db, kind=kind, active_only=active_only)
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
        student_material_required=_is_student_material_required(n),
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
    operator_roles: list[str],
) -> StudentWorkflowDetail:
    tpl = await repo.get_template_by_code(db, template_code)
    if tpl is None or not tpl.is_active:
        raise NotFoundError("流程模板不存在或已停用")
    student = await db.get(Student, student_id)
    if student is None:
        raise NotFoundError(f"学生不存在：{student_id}")
    await _ensure_workflow_start_allowed(
        db,
        student=student,
        template_code=template_code,
        operator_id=operator_id,
        operator_role=operator_role,
        operator_roles=operator_roles,
    )

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


async def _ensure_workflow_start_allowed(
    db: AsyncSession,
    *,
    student: Student,
    template_code: str,
    operator_id: int,
    operator_role: str | None,
    operator_roles: list[str],
) -> None:
    allowed = await _workflow_student_visible(
        db,
        student=student,
        viewer_user_id=operator_id,
        viewer_student_id=None,
        viewer_roles=operator_roles,
        scoped_roles=_WORKFLOW_START_SCOPED_ROLES,
        allow_student_self=False,
    )
    if allowed:
        return
    reason = await _workflow_denial_reason(
        db,
        student=student,
        viewer_user_id=operator_id,
        viewer_roles=operator_roles,
        scoped_roles=_WORKFLOW_START_SCOPED_ROLES,
    )
    await audit_forbidden_and_raise(
        db,
        event_type="WORKFLOW",
        entity_code="STUDENT_WORKFLOW",
        action="START",
        entity_id=student.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        message="无权为该学生发起流程",
        code=40306,
        detail=build_audit_detail(
            target={"student_id": student.id, "template_code": template_code},
            reason=reason,
        ),
    )


async def _workflow_scope_codes_for_viewer(
    db: AsyncSession,
    *,
    viewer_user_id: int,
    viewer_roles: list[str],
    scoped_roles: set[str] | None = None,
) -> StudentScopeSet | None:
    roles = _normalized_role_set(viewer_roles)
    if roles & _WORKFLOW_GLOBAL_ROLES:
        return None
    effective_scoped_roles = scoped_roles or _WORKFLOW_SCOPED_ROLES
    role_codes = sorted(roles & effective_scoped_roles)
    if not role_codes:
        return StudentScopeSet()
    return split_student_scope_codes(
        list(
            await repo.list_user_role_scope_codes(
                db,
                user_id=viewer_user_id,
                role_codes=role_codes,
            )
        )
    )


async def _workflow_student_visible(
    db: AsyncSession,
    *,
    student: Student,
    viewer_user_id: int,
    viewer_student_id: int | None,
    viewer_roles: list[str],
    scoped_roles: set[str] | None = None,
    allow_student_self: bool = True,
) -> bool:
    if allow_student_self and viewer_student_id is not None and student.id == viewer_student_id:
        return True
    scope = await _workflow_scope_codes_for_viewer(
        db,
        viewer_user_id=viewer_user_id,
        viewer_roles=viewer_roles,
        scoped_roles=scoped_roles,
    )
    if scope is None:
        return True
    if scope.is_empty():
        return False
    return student_in_scope(student, scope)


async def _workflow_denial_reason(
    db: AsyncSession,
    *,
    student: Student,
    viewer_user_id: int,
    viewer_roles: list[str],
    scoped_roles: set[str] | None = None,
) -> str:
    roles = _normalized_role_set(viewer_roles)
    effective_scoped_roles = scoped_roles or _WORKFLOW_SCOPED_ROLES
    if not roles & effective_scoped_roles:
        return "NO_WORKFLOW_SCOPE_ROLE"
    scope = await _workflow_scope_codes_for_viewer(
        db,
        viewer_user_id=viewer_user_id,
        viewer_roles=viewer_roles,
        scoped_roles=effective_scoped_roles,
    )
    if scope is None:
        return "GLOBAL"
    if scope.is_empty():
        return "EMPTY_SCOPE"
    if not student_in_scope(student, scope):
        return "OUT_OF_SCOPE"
    return "UNKNOWN"


async def _ensure_workflow_student_visible(
    db: AsyncSession,
    *,
    student: Student,
    workflow_id: int,
    viewer_user_id: int,
    viewer_student_id: int | None,
    viewer_roles: list[str],
    action: str,
    entity_code: str,
    entity_id: int,
    message: str,
    code: int,
) -> None:
    allowed = await _workflow_student_visible(
        db,
        student=student,
        viewer_user_id=viewer_user_id,
        viewer_student_id=viewer_student_id,
        viewer_roles=viewer_roles,
    )
    if allowed:
        return
    reason = await _workflow_denial_reason(
        db,
        student=student,
        viewer_user_id=viewer_user_id,
        viewer_roles=viewer_roles,
    )
    await audit_forbidden_and_raise(
        db,
        event_type="WORKFLOW",
        entity_code=entity_code,
        action=action,
        entity_id=entity_id,
        actor_user_id=viewer_user_id,
        actor_role=",".join(viewer_roles) or None,
        message=message,
        code=code,
        detail=build_audit_detail(
            target={"workflow_id": workflow_id, "student_id": student.id},
            refs=[{"reason": reason}],
        ),
    )


async def _ensure_workflow_node_operable(
    db: AsyncSession,
    *,
    state: StudentWorkflowNode,
    operator_id: int,
    operator_roles: list[str],
    action: str,
) -> None:
    workflow = state.workflow
    student = await db.get(Student, workflow.student_id) if workflow else None
    if student is None or workflow is None:
        raise NotFoundError("流程实例不存在")
    await _ensure_workflow_student_visible(
        db,
        student=student,
        workflow_id=workflow.id,
        viewer_user_id=operator_id,
        viewer_student_id=None,
        viewer_roles=operator_roles,
        action=action,
        entity_code="STUDENT_WORKFLOW_NODE",
        entity_id=state.id,
        message="无权操作该流程节点",
        code=40307,
    )


async def get_workflow_for_student(
    db: AsyncSession,
    workflow_id: int,
    viewer_user_id: int,
    viewer_student_id: int | None,
    viewer_roles: list[str],
) -> StudentWorkflowDetail:
    sw = await repo.get_student_workflow(db, workflow_id)
    if sw is None:
        raise NotFoundError("流程实例不存在")
    student = await db.get(Student, sw.student_id)
    if student is None:
        raise NotFoundError("流程学生不存在")
    await _ensure_workflow_student_visible(
        db,
        student=student,
        workflow_id=sw.id,
        viewer_user_id=viewer_user_id,
        viewer_student_id=viewer_student_id,
        viewer_roles=viewer_roles,
        action="READ_DETAIL_DENIED",
        entity_code="STUDENT_WORKFLOW",
        entity_id=sw.id,
        message="无权访问该流程",
        code=40301,
    )
    return _workflow_to_detail(sw)


async def list_my_workflows(
    db: AsyncSession, student_id: int
) -> list[StudentWorkflowDetail]:
    rows = await repo.list_student_workflows_for_student(db, student_id)
    return [_workflow_to_detail(r) for r in rows]


async def submit_node_material(
    db: AsyncSession,
    *,
    state_id: int,
    evidence: str,
    note: str | None,
    operator_id: int,
    student_id: int | None,
) -> StudentWorkflowDetail:
    if student_id is None:
        raise AppPermissionError("仅绑定学生可提交党团流程材料", code=40305)
    state = await repo.get_student_node_state(db, state_id)
    if state is None:
        raise NotFoundError("节点状态不存在")
    sw = state.workflow
    if sw.student_id != student_id:
        raise AppPermissionError("只能提交本人流程的当前节点材料", code=40306)
    if sw.status != "ACTIVE":
        raise ConflictError("该流程当前不可提交材料")
    if sw.current_node_id != state.node_id:
        raise BizError("只能提交当前节点材料", code=40031)
    if state.status == WORKFLOW_NODE_DONE:
        raise ConflictError("节点已完成，不能重复提交材料", code=40916)
    if not _is_student_material_required(state.node):
        raise BizError("当前节点无需学生提交材料，请等待老师或支部处理", code=40032)

    submitted = datetime.now(UTC)
    state.status = WORKFLOW_NODE_MATERIAL_SUBMITTED
    state.evidence = evidence.strip()
    state.note = note.strip() if note else None
    if state.triggered_at is None:
        state.triggered_at = submitted

    await log_action(
        db,
        event_type="WORKFLOW",
        entity_code="STUDENT_WORKFLOW_NODE",
        action="SUBMIT_MATERIAL",
        entity_id=state.id,
        actor_user_id=operator_id,
        actor_role="STUDENT",
        detail=build_audit_detail(
            target={"workflow_id": sw.id, "state_id": state.id, "node_id": state.node_id},
            metrics={"has_note": bool(state.note)},
        ),
    )
    await db.commit()
    full = await repo.get_student_workflow(db, sw.id)
    assert full is not None
    return _workflow_to_detail(full)


async def complete_node(
    db: AsyncSession,
    state_id: int,
    evidence: str | None,
    note: str | None,
    operator_id: int,
    operator_role: str | None,
    operator_roles: list[str],
) -> StudentWorkflowDetail:
    state = await repo.get_student_node_state(db, state_id)
    if state is None:
        raise NotFoundError("节点状态不存在")
    await _ensure_workflow_node_operable(
        db,
        state=state,
        operator_id=operator_id,
        operator_roles=operator_roles,
        action="COMPLETE_DENIED",
    )
    NodeStateMachine.assert_completable(state.status)

    state.status = WORKFLOW_NODE_DONE
    state.completed_at = datetime.now(UTC)
    state.completed_by = operator_id
    if evidence is not None:
        state.evidence = evidence
    if note is not None:
        state.note = note
    cancelled = await _cancel_unsent_reminders_for_state(
        db,
        state_id=state.id,
        reason="节点已完成，自动关闭未发送提醒",
    )

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
        detail={"cancelled_reminders": cancelled},
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
    operator_roles: list[str],
) -> StudentWorkflowDetail:
    NodeStateMachine.assert_manual_status_allowed(new_status)
    state = await repo.get_student_node_state(db, state_id)
    if state is None:
        raise NotFoundError("节点状态不存在")
    await _ensure_workflow_node_operable(
        db,
        state=state,
        operator_id=operator_id,
        operator_roles=operator_roles,
        action="MARK_STATUS_DENIED",
    )
    if state.status == WORKFLOW_NODE_DONE:
        raise ConflictError("已完成的节点不可再改状态")
    state.status = new_status
    if note:
        state.note = note
    cancelled = 0
    if new_status == WORKFLOW_NODE_MANUAL:
        cancelled = await _cancel_unsent_reminders_for_state(
            db,
            state_id=state.id,
            reason="节点已转人工跟进，自动关闭未发送提醒",
        )
    await log_action(
        db,
        event_type="WORKFLOW",
        entity_code="STUDENT_WORKFLOW_NODE",
        action="MARK_STATUS",
        entity_id=state.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"new_status": new_status, "cancelled_reminders": cancelled},
    )
    await db.commit()
    full = await repo.get_student_workflow(db, state.workflow_id)
    assert full is not None
    return _workflow_to_detail(full)


async def list_admin_workflows(
    db: AsyncSession,
    *,
    template_code: str | None,
    student_no: str | None,
    grade_code: str | None,
    page: int,
    size: int,
    viewer_user_id: int,
    viewer_roles: list[str],
) -> tuple[list[StudentWorkflowBrief], int]:
    scope = await _workflow_scope_codes_for_viewer(
        db,
        viewer_user_id=viewer_user_id,
        viewer_roles=viewer_roles,
    )
    rows, total = await repo.list_pending_workflows_admin(
        db,
        template_code=template_code,
        student_no=student_no,
        grade_code=grade_code,
        class_scope_codes=None if scope is None else scope.class_codes,
        major_scope_codes=None if scope is None else scope.major_codes,
        grade_scope_codes=None if scope is None else scope.grade_codes,
        legacy_scope_codes=None if scope is None else scope.legacy_codes,
        page=page,
        size=size,
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
                current_node_state_id=cur_state.id if cur_state else None,
                current_node_name=cur_state.node.name if cur_state and cur_state.node else None,
                current_node_status=cur_state.status if cur_state else None,
                current_node_student_material_required=_is_student_material_required(
                    cur_state.node if cur_state else None
                ),
                current_node_evidence=cur_state.evidence if cur_state else None,
                current_node_note=cur_state.note if cur_state else None,
                due_date=cur_state.due_date if cur_state else None,
            )
        )
    return items, total


def _reminder_run_to_out(run: WorkflowReminderRun) -> ReminderRunOut:
    return ReminderRunOut.model_validate(run)


def _reminder_row_to_out(
    reminder: WorkflowReminder,
    state: StudentWorkflowNode,
    workflow: StudentWorkflow,
    template: WorkflowTemplate,
    student: Student,
) -> ReminderAdminOut:
    return ReminderAdminOut(
        id=reminder.id,
        workflow_node_state_id=reminder.workflow_node_state_id,
        student_id=reminder.student_id,
        student_no=student.student_no,
        student_name=student.full_name,
        template_code=template.code,
        template_name=template.name,
        node_code=state.node.code if state.node else "",
        node_name=state.node.name if state.node else "",
        node_status=state.status,
        due_date=state.due_date,
        reminder_date=reminder.reminder_date,
        channel=reminder.channel,
        status=reminder.status,
        sent_at=reminder.sent_at,
        message=reminder.message,
        cancel_reason=reminder.cancel_reason,
        error_message=reminder.error_message,
        created_at=reminder.created_at,
    )


async def list_reminder_runs(
    db: AsyncSession,
    *,
    page: int,
    size: int,
) -> tuple[list[ReminderRunOut], int]:
    rows, total = await repo.list_reminder_runs(db, page=page, size=size)
    return [_reminder_run_to_out(row) for row in rows], total


async def list_reminders_admin(
    db: AsyncSession,
    *,
    template_code: str | None,
    student_no: str | None,
    status: str | None,
    page: int,
    size: int,
    viewer_user_id: int,
    viewer_roles: list[str],
) -> tuple[list[ReminderAdminOut], int]:
    scope = await _workflow_scope_codes_for_viewer(
        db,
        viewer_user_id=viewer_user_id,
        viewer_roles=viewer_roles,
    )
    rows, total = await repo.list_workflow_reminders_admin(
        db,
        template_code=template_code,
        student_no=student_no,
        status=status,
        class_scope_codes=None if scope is None else scope.class_codes,
        major_scope_codes=None if scope is None else scope.major_codes,
        grade_scope_codes=None if scope is None else scope.grade_codes,
        legacy_scope_codes=None if scope is None else scope.legacy_codes,
        page=page,
        size=size,
    )
    return [
        _reminder_row_to_out(reminder, state, workflow, template, student)
        for reminder, state, workflow, template, student in rows
    ], total


async def _cancel_unsent_reminders_for_state(
    db: AsyncSession,
    *,
    state_id: int,
    reason: str,
) -> int:
    return await repo.cancel_unsent_reminders_for_state(
        db,
        workflow_node_state_id=state_id,
        statuses=[REMINDER_STATUS_PENDING, REMINDER_STATUS_FAILED],
        cancel_reason=reason,
    )


def _build_reminder_message(
    *,
    template: WorkflowTemplate,
    node: WorkflowNode,
    due_date: date | None,
) -> tuple[str, str, str]:
    title = f"党团流程提醒：{template.name} - {node.name}"
    due_text = str(due_date) if due_date else "未设置，请按学院要求及时跟进"
    summary = f"{node.name} 需及时跟进" if due_date is None else f"{node.name} 需在 {due_date} 前跟进"
    body = "\n".join(
        [
            f"你在《{template.name}》中的当前节点为：{node.name}",
            f"截止日期：{due_text}",
            f"待完成事项：{node.required_task or '请按学院要求及时跟进'}",
        ]
    )
    return title, summary, body


async def run_reminder_cycle(
    db: AsyncSession,
    *,
    as_of: date | None,
    channel: str | None,
    trigger_mode: str,
    operator_id: int | None,
    operator_role: str | None,
    force_current_nodes: bool = False,
) -> ReminderRunOut:
    as_of = as_of or date.today()
    run = await repo.create_reminder_run(
        db,
        as_of_date=as_of,
        channel=channel or settings.WORKFLOW_REMINDER_CHANNEL,
        trigger_mode=trigger_mode,
        status=REMINDER_RUN_STATUS_RUNNING,
        created_count=0,
        sent_count=0,
        skipped_count=0,
        cancelled_count=0,
        failed_count=0,
        operator_id=operator_id,
        operator_role=operator_role,
    )

    created_count = 0
    sent_count = 0
    skipped_count = 0
    failed_count = 0
    user_cache: dict[int, int | None] = {}
    try:
        states = await repo.list_pending_nodes_for_reminder(
            db, as_of=as_of, include_without_due_date=force_current_nodes
        )
        for state in states:
            if state.node is None or state.workflow is None:
                skipped_count += 1
                continue

            node = state.node
            workflow = state.workflow
            template = workflow.template

            if force_current_nodes and workflow.current_node_id != state.node_id:
                skipped_count += 1
                continue
            if state.due_date is None and not force_current_nodes:
                skipped_count += 1
                continue

            if not node.reminder_enabled:
                skipped_count += 1
                continue

            effective_channel = channel or node.reminder_channel or settings.WORKFLOW_REMINDER_CHANNEL
            if effective_channel != "IN_APP":
                raise BizError("流程提醒一期仅支持站内提醒 IN_APP", code=40086)

            lead_days = node.reminder_lead_days or 0
            remind_on = state.due_date - timedelta(days=lead_days) if state.due_date else None
            if remind_on is not None and remind_on > as_of and not force_current_nodes:
                skipped_count += 1
                continue

            if state.due_date is not None and state.due_date < as_of and state.status == WORKFLOW_NODE_PENDING:
                state.status = WORKFLOW_NODE_OVERDUE

            existing = await repo.list_reminders_for_state(
                db,
                workflow_node_state_id=state.id,
                channel=effective_channel,
            )
            active_reminders = [row for row in existing if row.status != REMINDER_STATUS_CANCELLED]
            if any(row.reminder_date == as_of for row in active_reminders):
                skipped_count += 1
                continue

            if node.max_reminders is not None and len(active_reminders) >= node.max_reminders:
                skipped_count += 1
                continue

            if active_reminders:
                interval_days = node.repeat_interval_days
                if interval_days is None or interval_days <= 0:
                    if not force_current_nodes:
                        skipped_count += 1
                        continue
                    interval_days = None
                last_date = max(row.reminder_date for row in active_reminders)
                if interval_days is not None and (as_of - last_date).days < interval_days and not force_current_nodes:
                    skipped_count += 1
                    continue

            title, summary, body = _build_reminder_message(
                template=template,
                node=node,
                due_date=state.due_date,
            )
            reminder = await repo.create_reminder(
                db,
                run_id=run.id,
                workflow_node_state_id=state.id,
                student_id=workflow.student_id,
                reminder_date=as_of,
                channel=effective_channel,
                status=REMINDER_STATUS_PENDING,
                message=summary,
            )
            created_count += 1

            try:
                if workflow.student_id not in user_cache:
                    user = await notice_repo.find_user_by_student_id(db, workflow.student_id)
                    user_cache[workflow.student_id] = user.id if user else None
                in_app_delivery = await create_system_in_app_notice_for_student(
                    db,
                    student_id=workflow.student_id,
                    user_id=user_cache[workflow.student_id],
                    title=title,
                    body_md=body,
                    summary=summary,
                    category="WORKFLOW",
                    source_type="SYSTEM",
                    source_url=f"workflow-reminder:{reminder.id}",
                    operator_id=operator_id,
                )
                await send_wechat_subscribe_for_delivery(
                    db,
                    in_app_delivery=in_app_delivery,
                    scene=WECHAT_SUBSCRIBE_SCENE_WORKFLOW_REMINDER,
                    title=title,
                    summary=summary,
                    page="/pages/workflow/index",
                )
                reminder.status = REMINDER_STATUS_SENT
                reminder.sent_at = datetime.now(UTC)
                sent_count += 1
            except Exception as exc:  # noqa: BLE001
                logger.exception("workflow reminder send failed | reminder_id=%s", reminder.id)
                reminder.status = REMINDER_STATUS_FAILED
                reminder.error_message = str(exc)[:512]
                failed_count += 1

        run.status = REMINDER_RUN_STATUS_COMPLETED
        run.created_count = created_count
        run.sent_count = sent_count
        run.skipped_count = skipped_count
        run.cancelled_count = 0
        run.failed_count = failed_count
        run.finished_at = datetime.now(UTC)

        await log_action(
            db,
            event_type="WORKFLOW",
            entity_code="REMINDER_RUN",
            action="RUN",
            entity_id=run.id,
            actor_user_id=operator_id,
            actor_role=operator_role,
            detail={
                "as_of": str(as_of),
                "channel": run.channel,
                "trigger_mode": trigger_mode,
                "created": created_count,
                "sent": sent_count,
                "skipped": skipped_count,
                "failed": failed_count,
            },
        )
        await db.commit()
        await db.refresh(run)
        return _reminder_run_to_out(run)
    except Exception as exc:  # noqa: BLE001
        run.status = REMINDER_RUN_STATUS_FAILED
        run.error_message = str(exc)[:512]
        run.created_count = created_count
        run.sent_count = sent_count
        run.skipped_count = skipped_count
        run.cancelled_count = 0
        run.failed_count = failed_count
        run.finished_at = datetime.now(UTC)
        await db.commit()
        raise


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
    force_current_nodes: bool = False,
) -> ReminderRunOut:
    return await run_reminder_cycle(
        db,
        as_of=as_of,
        channel=channel,
        trigger_mode="MANUAL",
        operator_id=operator_id,
        operator_role=operator_role,
        force_current_nodes=force_current_nodes,
    )


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


def _parse_request_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise BizError("日期格式应为 YYYY-MM-DD", code=40043) from exc


def _validate_request_form_data(rt, form_data: dict | None) -> None:
    if not rt or not isinstance(form_data, dict):
        return
    category = (rt.category or "").upper()
    type_code = (rt.code or "").upper()
    if category != "LEAVE" and "LEAVE" not in type_code:
        return

    start_date = _parse_request_date(form_data.get("start_date"))
    end_date = _parse_request_date(form_data.get("end_date"))
    if start_date is not None and end_date is not None and start_date > end_date:
        raise BizError("请假起始日期不能晚于结束日期", code=40044)


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
    _validate_request_form_data(rt, payload.form_data)

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
    _validate_request_form_data(rt, req.form_data)

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
    next_form_data = changed.get("form_data", req.form_data)
    _validate_request_form_data(req.type_ref, next_form_data)
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
    viewer_user_id: int,
    viewer_roles: list[str],
    page: int,
    size: int,
) -> tuple[list[RequestBrief], int]:
    scope_codes = await _request_scope_codes_for_viewer(
        db,
        viewer_user_id=viewer_user_id,
        viewer_roles=viewer_roles,
    )
    rows, total = await repo.list_requests_admin(
        db,
        q=q,
        type_code=type_code,
        status=status,
        in_review_only=in_review_only,
        class_scope_codes=None if scope_codes is None else scope_codes.class_codes,
        major_scope_codes=None if scope_codes is None else scope_codes.major_codes,
        grade_scope_codes=None if scope_codes is None else scope_codes.grade_codes,
        legacy_scope_codes=None if scope_codes is None else scope_codes.legacy_codes,
        page=page,
        size=size,
    )
    return [_request_to_brief(r) for r in rows], total


def _normalized_role_set(roles: list[str]) -> set[str]:
    return set(normalize_role_codes(roles))


async def _request_scope_codes_for_viewer(
    db: AsyncSession,
    *,
    viewer_user_id: int,
    viewer_roles: list[str],
) -> StudentScopeSet | None:
    roles = _normalized_role_set(viewer_roles)
    if roles & _REQUEST_GLOBAL_ROLES:
        return None
    collaborator_roles = sorted(roles & _REQUEST_COLLABORATOR_ROLES)
    if not collaborator_roles:
        return StudentScopeSet()
    return split_student_scope_codes(
        list(
            await repo.list_user_role_scope_codes(
                db,
                user_id=viewer_user_id,
                role_codes=collaborator_roles,
            )
        )
    )


async def _request_in_viewer_scope(
    db: AsyncSession,
    *,
    req: Request,
    viewer_user_id: int,
    viewer_student_id: int | None,
    viewer_roles: list[str],
    allow_applicant_self: bool = True,
) -> bool:
    if allow_applicant_self and req.applicant_user_id == viewer_user_id:
        return True
    if (
        allow_applicant_self
        and viewer_student_id is not None
        and req.applicant_student_id == viewer_student_id
    ):
        return True
    roles = _normalized_role_set(viewer_roles)
    if roles & _REQUEST_GLOBAL_ROLES:
        return True
    if not roles & _REQUEST_COLLABORATOR_ROLES:
        return False
    scope_codes = await _request_scope_codes_for_viewer(
        db,
        viewer_user_id=viewer_user_id,
        viewer_roles=viewer_roles,
    )
    if scope_codes is None or scope_codes.is_empty() or req.applicant_student_id is None:
        return False
    student = await db.get(Student, req.applicant_student_id)
    if student is None:
        return False
    return student_in_scope(student, scope_codes)


async def _audit_request_scope_denied(
    db: AsyncSession,
    *,
    req: Request,
    viewer_user_id: int,
    viewer_roles: list[str],
    action: str,
    message: str,
    code: int = 40303,
) -> None:
    await audit_forbidden_and_raise(
        db,
        event_type="REQUEST",
        entity_code="REQUEST",
        action=action,
        entity_id=req.id,
        actor_user_id=viewer_user_id,
        actor_role=",".join(viewer_roles) or None,
        message=message,
        code=code,
        detail=build_audit_detail(target={"request_id": req.id}),
    )


async def _ensure_request_visible_to_viewer(
    db: AsyncSession,
    *,
    req: Request,
    viewer_user_id: int,
    viewer_student_id: int | None,
    viewer_roles: list[str],
    allow_applicant_self: bool = True,
    action: str = "READ_DETAIL_DENIED",
    message: str = "无权查看该申请",
    code: int = 40303,
) -> None:
    if not await _request_in_viewer_scope(
        db,
        req=req,
        viewer_user_id=viewer_user_id,
        viewer_student_id=viewer_student_id,
        viewer_roles=viewer_roles,
        allow_applicant_self=allow_applicant_self,
    ):
        await _audit_request_scope_denied(
            db,
            req=req,
            viewer_user_id=viewer_user_id,
            viewer_roles=viewer_roles,
            action=action,
            message=message,
            code=code,
        )


async def get_request_detail(
    db: AsyncSession,
    request_id: int,
    viewer_user_id: int,
    viewer_roles: list[str],
    viewer_student_id: int | None = None,
) -> RequestDetail:
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    await _ensure_request_visible_to_viewer(
        db,
        req=req,
        viewer_user_id=viewer_user_id,
        viewer_student_id=viewer_student_id,
        viewer_roles=viewer_roles,
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
    allowed = set(normalize_role_codes(rt.approver_roles.split(",")))
    return bool(set(normalize_role_codes(roles)) & allowed)


def _request_status_label(status: str) -> str:
    return {
        "APPROVED": "已通过",
        "REJECTED": "已驳回",
        "OFFLINE_HANDLED": "已转线下办理",
        "IN_REVIEW": "审核中",
        "SUBMITTED": "已提交",
    }.get(status, status)


async def _notify_request_status_change(
    db: AsyncSession,
    *,
    req: Request,
    title: str,
    body_md: str,
    summary: str,
    operator_id: int | None,
) -> None:
    if req.applicant_student_id is None:
        return
    in_app_delivery = await create_system_in_app_notice_for_student(
        db,
        student_id=req.applicant_student_id,
        user_id=req.applicant_user_id,
        title=title,
        body_md=body_md,
        summary=summary,
        category="WORKFLOW",
        source_type="SYSTEM",
        source_url=f"request:{req.id}",
        operator_id=operator_id,
    )
    await send_wechat_subscribe_for_delivery(
        db,
        in_app_delivery=in_app_delivery,
        scene=WECHAT_SUBSCRIBE_SCENE_REQUEST_STATUS,
        title=title,
        summary=summary,
        page=f"/pages/request/detail?id={req.id}",
    )


async def decide_request(
    db: AsyncSession,
    request_id: int,
    *,
    approve: bool,
    comment: str | None,
    operator_id: int,
    operator_roles: list[str],
    operator_student_id: int | None = None,
) -> RequestDetail:
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    await _ensure_request_visible_to_viewer(
        db,
        req=req,
        viewer_user_id=operator_id,
        viewer_student_id=operator_student_id,
        viewer_roles=operator_roles,
        allow_applicant_self=False,
        action="DECIDE_DENIED",
        message="无权审批该申请",
        code=40304,
    )
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
    status_label = _request_status_label(req.status)
    await _notify_request_status_change(
        db,
        req=req,
        title=f"申请{status_label}：{req.title}",
        body_md=(
            f"你的申请《{req.title}》{status_label}。"
            + (f"\n\n处理意见：{comment}" if comment else "")
        ),
        summary=f"申请状态更新为{status_label}",
        operator_id=operator_id,
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
    operator_student_id: int | None = None,
) -> RequestDetail:
    """v1.5 涉密 / 敏感事项转线下办理。

    终止在线流转：状态 → OFFLINE_HANDLED；审批历史保留；
    contact_info 将在学生端以"线下办理提示"卡片展示（如老师姓名 + 电话）。
    """
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    await _ensure_request_visible_to_viewer(
        db,
        req=req,
        viewer_user_id=operator_id,
        viewer_student_id=operator_student_id,
        viewer_roles=operator_roles,
        allow_applicant_self=False,
        action="OFFLINE_HANDLE_DENIED",
        message="无权处理该申请",
        code=40304,
    )
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
    body = (
        f"你的申请《{req.title}》已转为线下办理。\n\n"
        f"联系方式：{contact_info}"
        + (f"\n\n说明：{note}" if note else "")
    )
    await _notify_request_status_change(
        db,
        req=req,
        title=f"申请已转线下办理：{req.title}",
        body_md=body,
        summary=f"请按线下办理提示联系负责老师：{contact_info}",
        operator_id=operator_id,
    )
    await db.commit()
    await db.refresh(req)
    return _request_to_detail(req)


async def reopen_request(
    db: AsyncSession,
    request_id: int,
    *,
    comment: str | None,
    target_status: str,
    operator_id: int,
    operator_roles: list[str],
    operator_student_id: int | None = None,
) -> RequestDetail:
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    await _ensure_request_visible_to_viewer(
        db,
        req=req,
        viewer_user_id=operator_id,
        viewer_student_id=operator_student_id,
        viewer_roles=operator_roles,
        allow_applicant_self=False,
        action="REOPEN_DENIED",
        message="无权重开该申请",
        code=40304,
    )
    if not _approver_has_role(req.type_ref, operator_roles):
        raise BizError("无权重开该类型申请", code=40304, http_status=403)

    result = ApprovalStateMachine.reopen(req.status, target_status)
    status_before = result.status_before
    req.status = result.status_after
    req.decided_at = None
    req.decided_by = None
    req.decision_comment = None
    req.withdrawn_at = None

    await repo.add_approval_record(
        db,
        request_id=req.id,
        revision=req.revision,
        action=REQUEST_ACTION_REOPEN,
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
        action=REQUEST_ACTION_REOPEN,
        entity_id=req.id,
        actor_user_id=operator_id,
        actor_role=",".join(operator_roles),
        detail={
            "comment": comment,
            "status_before": status_before,
            "status_after": req.status,
        },
    )
    await db.commit()
    await db.refresh(req)
    return _request_to_detail(req)


async def claim_in_review(
    db: AsyncSession,
    request_id: int,
    operator_id: int,
    operator_roles: list[str],
    operator_student_id: int | None = None,
) -> RequestDetail:
    """把 SUBMITTED → IN_REVIEW，表示某审批人已认领。"""
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    await _ensure_request_visible_to_viewer(
        db,
        req=req,
        viewer_user_id=operator_id,
        viewer_student_id=operator_student_id,
        viewer_roles=operator_roles,
        allow_applicant_self=False,
        action="CLAIM_DENIED",
        message="无权认领该申请",
        code=40304,
    )
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
# B.3 电子证明模板维护
# ======================================================================
def _proof_template_to_out(row: ProofTemplate) -> ProofTemplateOut:
    return ProofTemplateOut.model_validate(row)


async def list_proof_templates(
    db: AsyncSession,
    *,
    request_type_code: str | None = None,
    active_only: bool = False,
) -> list[ProofTemplateOut]:
    rows = await repo.list_proof_templates(
        db,
        request_type_code=request_type_code,
        active_only=active_only,
    )
    return [_proof_template_to_out(row) for row in rows]


async def upsert_proof_template(
    db: AsyncSession,
    payload: ProofTemplateIn,
    operator_id: int,
    operator_role: str | None,
) -> ProofTemplateOut:
    pdf_generator.validate_template_placeholders(payload.html_template)
    request_type = await repo.get_request_type_by_code(db, payload.request_type_code)
    if request_type is None:
        raise NotFoundError(f"申请类型不存在：{payload.request_type_code}")
    if (
        request_type.category != "CERTIFICATE"
        and not request_type.code.upper().startswith("CERT")
    ):
        raise BizError("电子证明模板只能绑定证明类申请类型", code=40042)

    existing = await repo.get_proof_template_by_code(db, payload.code)
    if existing is None:
        row = await repo.create_proof_template(
            db,
            **payload.model_dump(),
            created_by=operator_id,
            updated_by=operator_id,
        )
        action = "CREATE"
    else:
        data = payload.model_dump(exclude={"code"})
        for key, value in data.items():
            setattr(existing, key, value)
        existing.updated_by = operator_id
        row = existing
        action = "UPDATE"
    await log_action(
        db,
        event_type="WORKFLOW",
        entity_code="PROOF_TEMPLATE",
        action=action,
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail=build_audit_detail(
            target={
                "code": row.code,
                "request_type_code": row.request_type_code,
                "version_label": row.version_label,
            }
        ),
    )
    await db.commit()
    await db.refresh(row)
    return _proof_template_to_out(row)


async def deactivate_proof_template(
    db: AsyncSession,
    template_code: str,
    operator_id: int,
    operator_role: str | None,
) -> ProofTemplateOut:
    row = await repo.get_proof_template_by_code(db, template_code)
    if row is None:
        raise NotFoundError("证明模板不存在")
    row.is_active = False
    row.updated_by = operator_id
    await log_action(
        db,
        event_type="WORKFLOW",
        entity_code="PROOF_TEMPLATE",
        action="DEACTIVATE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail=build_audit_detail(target={"code": row.code}),
    )
    await db.commit()
    await db.refresh(row)
    return _proof_template_to_out(row)


async def preview_proof_template(
    db: AsyncSession,
    payload: ProofTemplatePreviewIn,
) -> ProofTemplatePreviewOut:
    placeholders = pdf_generator.validate_template_placeholders(payload.html_template)
    if payload.request_id is not None:
        req = await repo.get_request(db, payload.request_id)
        if req is None:
            raise NotFoundError("申请不存在")
        student = (
            await db.get(Student, req.applicant_student_id)
            if req.applicant_student_id is not None
            else None
        )
        context = pdf_generator.build_render_context(req, student)
        html = pdf_generator.render_template_html(payload.html_template, context)
        return ProofTemplatePreviewOut(html=html, placeholders=placeholders)

    sample = payload.sample_data or {}
    context = {
        "today": datetime.now(UTC).strftime("%Y-%m-%d"),
        "student": {
            "full_name": sample.get("student_full_name", "张三"),
            "student_no": sample.get("student_no", "2024000000"),
            "grade_code": sample.get("grade_code", "2024"),
            "major_code": sample.get("major_code", "CS"),
            "class_code": sample.get("class_code", "CS2401"),
            "political_status": sample.get("political_status", "共青团员"),
            "enrollment_year": sample.get("enrollment_year", "2024"),
            "expected_graduation_year": sample.get("expected_graduation_year", "2028"),
        },
        "request": {
            "request_no": sample.get("request_no", "CERT-260523-DEMO01"),
            "title": sample.get("title", "在读证明"),
            "summary": sample.get("summary", "用于证明模板预览"),
            "status": "APPROVED",
            "revision": 1,
            "submitted_date": sample.get("submitted_date", "2026-05-23"),
            "decided_date": sample.get("decided_date", "2026-05-23"),
            "decision_comment": sample.get("decision_comment", "同意开具"),
        },
        "type": {
            "code": sample.get("type_code", "CERTIFICATE_IN_SCHOOL"),
            "name": sample.get("type_name", "在读证明"),
            "category": "CERTIFICATE",
        },
        "form": sample.get(
            "form",
            {"purpose": "出国交流申请", "deliver_to": "接收单位"},
        ),
    }
    return ProofTemplatePreviewOut(
        html=pdf_generator.render_template_html(payload.html_template, context),
        placeholders=placeholders,
    )


# ======================================================================
# B.4 申请类型维护
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
