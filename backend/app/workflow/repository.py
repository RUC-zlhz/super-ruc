"""workflow 模块仓储层。"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from sqlalchemy import and_, false, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import Student, UserRole
from app.auth.role_codes import expand_role_codes_for_lookup
from app.core.sql import order_by_nulls_last_desc
from app.workflow.models import (
    REMINDER_STATUS_CANCELLED,
    REQUEST_STATUS_APPROVED,
    REQUEST_STATUS_IN_REVIEW,
    REQUEST_STATUS_REJECTED,
    REQUEST_STATUS_SUBMITTED,
    REQUEST_STATUS_WITHDRAWN,
    WORKFLOW_NODE_DONE,
    WORKFLOW_NODE_OVERDUE,
    WORKFLOW_NODE_PENDING,
    ProofTemplate,
    Request,
    RequestApprovalRecord,
    RequestAttachment,
    RequestType,
    StudentWorkflow,
    StudentWorkflowNode,
    WorkflowNode,
    WorkflowReminder,
    WorkflowReminderRun,
    WorkflowTemplate,
)


# ==================================================================
# A. 党团流程
# ==================================================================
async def get_template(db: AsyncSession, template_id: int) -> WorkflowTemplate | None:
    return await db.get(WorkflowTemplate, template_id)


async def get_template_by_code(db: AsyncSession, code: str) -> WorkflowTemplate | None:
    stmt = select(WorkflowTemplate).where(WorkflowTemplate.code == code)
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_templates(
    db: AsyncSession, *, kind: str | None = None, active_only: bool = True
) -> Sequence[WorkflowTemplate]:
    stmt = select(WorkflowTemplate)
    if kind:
        stmt = stmt.where(WorkflowTemplate.kind == kind)
    if active_only:
        stmt = stmt.where(WorkflowTemplate.is_active.is_(True))
    stmt = stmt.order_by(
        WorkflowTemplate.is_active.desc(),
        WorkflowTemplate.kind,
        WorkflowTemplate.code,
        WorkflowTemplate.id,
    )
    return (await db.execute(stmt)).scalars().unique().all()


async def create_template(db: AsyncSession, **fields) -> WorkflowTemplate:
    row = WorkflowTemplate(**fields)
    db.add(row)
    await db.flush()
    return row


async def add_node(db: AsyncSession, template_id: int, **fields) -> WorkflowNode:
    row = WorkflowNode(template_id=template_id, **fields)
    db.add(row)
    await db.flush()
    return row


async def delete_nodes_for_template(db: AsyncSession, template_id: int) -> None:
    existing = (
        await db.execute(select(WorkflowNode).where(WorkflowNode.template_id == template_id))
    ).scalars().all()
    for row in existing:
        await db.delete(row)
    await db.flush()


async def list_nodes(db: AsyncSession, template_id: int) -> Sequence[WorkflowNode]:
    stmt = (
        select(WorkflowNode)
        .where(WorkflowNode.template_id == template_id)
        .order_by(WorkflowNode.sort_order, WorkflowNode.id)
    )
    return (await db.execute(stmt)).scalars().all()


async def get_node(db: AsyncSession, node_id: int) -> WorkflowNode | None:
    return await db.get(WorkflowNode, node_id)


async def get_student_workflow(db: AsyncSession, workflow_id: int) -> StudentWorkflow | None:
    stmt = (
        select(StudentWorkflow)
        .options(selectinload(StudentWorkflow.node_states).selectinload(StudentWorkflowNode.node))
        .where(StudentWorkflow.id == workflow_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def find_active_student_workflow(
    db: AsyncSession, student_id: int, template_id: int
) -> StudentWorkflow | None:
    stmt = (
        select(StudentWorkflow)
        .where(
            and_(
                StudentWorkflow.student_id == student_id,
                StudentWorkflow.template_id == template_id,
                StudentWorkflow.status == "ACTIVE",
            )
        )
        .options(selectinload(StudentWorkflow.node_states).selectinload(StudentWorkflowNode.node))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_student_workflows_for_student(
    db: AsyncSession, student_id: int
) -> Sequence[StudentWorkflow]:
    stmt = (
        select(StudentWorkflow)
        .where(StudentWorkflow.student_id == student_id)
        .options(selectinload(StudentWorkflow.node_states).selectinload(StudentWorkflowNode.node))
        .order_by(StudentWorkflow.id.desc())
    )
    return (await db.execute(stmt)).scalars().unique().all()


async def create_student_workflow(db: AsyncSession, **fields) -> StudentWorkflow:
    row = StudentWorkflow(**fields)
    db.add(row)
    await db.flush()
    return row


async def add_student_node_state(db: AsyncSession, **fields) -> StudentWorkflowNode:
    row = StudentWorkflowNode(**fields)
    db.add(row)
    await db.flush()
    return row


async def get_student_node_state(
    db: AsyncSession, state_id: int
) -> StudentWorkflowNode | None:
    stmt = (
        select(StudentWorkflowNode)
        .options(
            selectinload(StudentWorkflowNode.node),
            selectinload(StudentWorkflowNode.workflow)
            .selectinload(StudentWorkflow.node_states)
            .selectinload(StudentWorkflowNode.node),
        )
        .where(StudentWorkflowNode.id == state_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_pending_nodes_for_reminder(
    db: AsyncSession, *, as_of: date
) -> Sequence[StudentWorkflowNode]:
    """返回需要生成提醒的节点状态：
    - status IN (PENDING, OVERDUE)
    - due_date - reminder_lead_days <= as_of
    逻辑层再做过滤。"""
    stmt = (
        select(StudentWorkflowNode)
        .options(
            selectinload(StudentWorkflowNode.node),
            selectinload(StudentWorkflowNode.workflow).selectinload(StudentWorkflow.template),
        )
        .where(StudentWorkflowNode.status.in_([WORKFLOW_NODE_PENDING, WORKFLOW_NODE_OVERDUE]))
        .where(StudentWorkflowNode.due_date.is_not(None))
    )
    return (await db.execute(stmt)).scalars().all()


async def list_user_role_scope_codes(
    db: AsyncSession,
    *,
    user_id: int,
    role_codes: Sequence[str],
) -> Sequence[str]:
    lookup_codes = expand_role_codes_for_lookup(role_codes)
    if not lookup_codes:
        return []
    stmt = select(UserRole.scope_code).where(
        UserRole.user_id == user_id,
        UserRole.role_code.in_(lookup_codes),
        UserRole.scope_code.is_not(None),
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [scope.strip() for scope in rows if scope and scope.strip()]


async def create_reminder(db: AsyncSession, **fields) -> WorkflowReminder:
    row = WorkflowReminder(**fields)
    db.add(row)
    await db.flush()
    return row


async def create_reminder_run(db: AsyncSession, **fields) -> WorkflowReminderRun:
    row = WorkflowReminderRun(**fields)
    db.add(row)
    await db.flush()
    return row


async def list_reminder_runs(
    db: AsyncSession,
    *,
    page: int = 1,
    size: int = 20,
) -> tuple[Sequence[WorkflowReminderRun], int]:
    stmt = select(WorkflowReminderRun)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()
    stmt = (
        stmt.order_by(WorkflowReminderRun.started_at.desc(), WorkflowReminderRun.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return (await db.execute(stmt)).scalars().all(), total


async def find_reminder_by_state_date_channel(
    db: AsyncSession,
    *,
    workflow_node_state_id: int,
    reminder_date: date,
    channel: str,
) -> WorkflowReminder | None:
    stmt = select(WorkflowReminder).where(
        WorkflowReminder.workflow_node_state_id == workflow_node_state_id,
        WorkflowReminder.reminder_date == reminder_date,
        WorkflowReminder.channel == channel,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_reminders_for_state(
    db: AsyncSession,
    *,
    workflow_node_state_id: int,
    channel: str | None = None,
) -> Sequence[WorkflowReminder]:
    stmt = select(WorkflowReminder).where(
        WorkflowReminder.workflow_node_state_id == workflow_node_state_id
    )
    if channel:
        stmt = stmt.where(WorkflowReminder.channel == channel)
    stmt = stmt.order_by(WorkflowReminder.reminder_date, WorkflowReminder.id)
    return (await db.execute(stmt)).scalars().all()


async def cancel_unsent_reminders_for_state(
    db: AsyncSession,
    *,
    workflow_node_state_id: int,
    statuses: Sequence[str],
    cancel_reason: str,
) -> int:
    stmt = select(WorkflowReminder).where(
        WorkflowReminder.workflow_node_state_id == workflow_node_state_id,
        WorkflowReminder.status.in_(list(statuses)),
    )
    rows = (await db.execute(stmt)).scalars().all()
    for row in rows:
        row.status = REMINDER_STATUS_CANCELLED
        row.cancel_reason = cancel_reason
    await db.flush()
    return len(rows)


async def list_workflow_reminders_admin(
    db: AsyncSession,
    *,
    template_code: str | None = None,
    student_no: str | None = None,
    status: str | None = None,
    class_scope_codes: set[str] | None = None,
    major_scope_codes: set[str] | None = None,
    grade_scope_codes: set[str] | None = None,
    legacy_scope_codes: set[str] | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[tuple[WorkflowReminder, StudentWorkflowNode, StudentWorkflow, WorkflowTemplate, Student]], int]:
    stmt = (
        select(
            WorkflowReminder,
            StudentWorkflowNode,
            StudentWorkflow,
            WorkflowTemplate,
            Student,
        )
        .join(StudentWorkflowNode, WorkflowReminder.workflow_node_state_id == StudentWorkflowNode.id)
        .join(StudentWorkflow, StudentWorkflowNode.workflow_id == StudentWorkflow.id)
        .join(WorkflowTemplate, StudentWorkflow.template_id == WorkflowTemplate.id)
        .join(Student, WorkflowReminder.student_id == Student.id)
    )
    if template_code:
        stmt = stmt.where(WorkflowTemplate.code == template_code)
    if student_no:
        stmt = stmt.where(Student.student_no.ilike(f"%{student_no}%"))
    if status:
        stmt = stmt.where(WorkflowReminder.status == status)
    stmt = _apply_student_scope_filters(
        stmt,
        class_scope_codes=class_scope_codes,
        major_scope_codes=major_scope_codes,
        grade_scope_codes=grade_scope_codes,
        legacy_scope_codes=legacy_scope_codes,
    )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        stmt.order_by(
            *order_by_nulls_last_desc(WorkflowReminder.sent_at),
            WorkflowReminder.created_at.desc(),
            WorkflowReminder.id.desc(),
        )
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [(row[0], row[1], row[2], row[3], row[4]) for row in rows], total


async def list_pending_workflows_admin(
    db: AsyncSession,
    *,
    template_code: str | None = None,
    student_no: str | None = None,
    grade_code: str | None = None,
    class_scope_codes: set[str] | None = None,
    major_scope_codes: set[str] | None = None,
    grade_scope_codes: set[str] | None = None,
    legacy_scope_codes: set[str] | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[Sequence[StudentWorkflow], int]:
    stmt = (
        select(StudentWorkflow)
        .join(WorkflowTemplate, StudentWorkflow.template_id == WorkflowTemplate.id)
        .join(Student, StudentWorkflow.student_id == Student.id)
        .options(
            selectinload(StudentWorkflow.node_states).selectinload(StudentWorkflowNode.node),
            selectinload(StudentWorkflow.template),
        )
        .where(StudentWorkflow.status == "ACTIVE")
    )
    if template_code:
        stmt = stmt.where(WorkflowTemplate.code == template_code)
    if student_no:
        stmt = stmt.where(Student.student_no.ilike(f"%{student_no}%"))
    if grade_code:
        stmt = stmt.where(Student.grade_code == grade_code)
    stmt = _apply_student_scope_filters(
        stmt,
        class_scope_codes=class_scope_codes,
        major_scope_codes=major_scope_codes,
        grade_scope_codes=grade_scope_codes,
        legacy_scope_codes=legacy_scope_codes,
    )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(StudentWorkflow.id).offset((page - 1) * size).limit(size)
    rows = (await db.execute(stmt)).scalars().unique().all()
    return rows, total


def _apply_student_scope_filters(
    stmt,
    *,
    class_scope_codes: set[str] | None,
    major_scope_codes: set[str] | None,
    grade_scope_codes: set[str] | None,
    legacy_scope_codes: set[str] | None,
):
    if (
        class_scope_codes is None
        and major_scope_codes is None
        and grade_scope_codes is None
        and legacy_scope_codes is None
    ):
        return stmt
    scope_conds = []
    if class_scope_codes:
        scope_conds.append(Student.class_code.in_(sorted(class_scope_codes)))
    if major_scope_codes:
        scope_conds.append(Student.major_code.in_(sorted(major_scope_codes)))
    if grade_scope_codes:
        scope_conds.append(Student.grade_code.in_(sorted(grade_scope_codes)))
    if legacy_scope_codes:
        legacy = sorted(legacy_scope_codes)
        scope_conds.extend(
            [
                Student.class_code.in_(legacy),
                Student.major_code.in_(legacy),
                Student.grade_code.in_(legacy),
            ]
        )
    if not scope_conds:
        return stmt.where(false())
    return stmt.where(or_(*scope_conds))


# ==================================================================
# B. 申请
# ==================================================================
async def list_request_types(
    db: AsyncSession, *, active_only: bool = True
) -> Sequence[RequestType]:
    stmt = select(RequestType)
    if active_only:
        stmt = stmt.where(RequestType.is_active.is_(True))
    stmt = stmt.order_by(RequestType.id)
    return (await db.execute(stmt)).scalars().all()


async def get_request_type(db: AsyncSession, type_id: int) -> RequestType | None:
    return await db.get(RequestType, type_id)


async def get_request_type_by_code(db: AsyncSession, code: str) -> RequestType | None:
    stmt = select(RequestType).where(RequestType.code == code)
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_request_type(db: AsyncSession, **fields) -> RequestType:
    row = RequestType(**fields)
    db.add(row)
    await db.flush()
    return row


async def get_proof_template_by_code(
    db: AsyncSession, code: str
) -> ProofTemplate | None:
    stmt = select(ProofTemplate).where(ProofTemplate.code == code)
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_active_proof_template(
    db: AsyncSession, request_type_code: str
) -> ProofTemplate | None:
    stmt = (
        select(ProofTemplate)
        .where(
            ProofTemplate.request_type_code == request_type_code,
            ProofTemplate.is_active.is_(True),
        )
        .order_by(ProofTemplate.is_default.desc(), ProofTemplate.id.desc())
    )
    return (await db.execute(stmt)).scalars().first()


async def list_proof_templates(
    db: AsyncSession,
    *,
    request_type_code: str | None = None,
    active_only: bool = False,
) -> Sequence[ProofTemplate]:
    stmt = select(ProofTemplate)
    if request_type_code:
        stmt = stmt.where(ProofTemplate.request_type_code == request_type_code)
    if active_only:
        stmt = stmt.where(ProofTemplate.is_active.is_(True))
    stmt = stmt.order_by(
        ProofTemplate.request_type_code,
        ProofTemplate.is_default.desc(),
        ProofTemplate.id.desc(),
    )
    return (await db.execute(stmt)).scalars().all()


async def create_proof_template(db: AsyncSession, **fields) -> ProofTemplate:
    row = ProofTemplate(**fields)
    db.add(row)
    await db.flush()
    return row


async def create_request(db: AsyncSession, **fields) -> Request:
    row = Request(**fields)
    db.add(row)
    await db.flush()
    return row


async def get_request(db: AsyncSession, request_id: int) -> Request | None:
    return await db.get(Request, request_id)


async def get_request_by_no(db: AsyncSession, request_no: str) -> Request | None:
    stmt = select(Request).where(Request.request_no == request_no)
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_requests_for_applicant(
    db: AsyncSession,
    applicant_user_id: int,
    *,
    status: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[Sequence[Request], int]:
    stmt = select(Request).where(Request.applicant_user_id == applicant_user_id)
    if status:
        stmt = stmt.where(Request.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Request.updated_at.desc()).offset((page - 1) * size).limit(size)
    rows = (await db.execute(stmt)).scalars().all()
    return rows, total


async def list_requests_admin(
    db: AsyncSession,
    *,
    q: str | None = None,
    type_code: str | None = None,
    status: str | None = None,
    in_review_only: bool = False,
    class_scope_codes: set[str] | None = None,
    major_scope_codes: set[str] | None = None,
    grade_scope_codes: set[str] | None = None,
    legacy_scope_codes: set[str] | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[Sequence[Request], int]:
    stmt = select(Request)
    conds = []
    if (
        class_scope_codes is not None
        or major_scope_codes is not None
        or grade_scope_codes is not None
        or legacy_scope_codes is not None
    ):
        scope_conds = []
        if class_scope_codes:
            scope_conds.append(Student.class_code.in_(sorted(class_scope_codes)))
        if major_scope_codes:
            scope_conds.append(Student.major_code.in_(sorted(major_scope_codes)))
        if grade_scope_codes:
            scope_conds.append(Student.grade_code.in_(sorted(grade_scope_codes)))
        if legacy_scope_codes:
            legacy = sorted(legacy_scope_codes)
            scope_conds.extend(
                [
                    Student.class_code.in_(legacy),
                    Student.major_code.in_(legacy),
                    Student.grade_code.in_(legacy),
                ]
            )
        if scope_conds:
            stmt = stmt.join(Student, Request.applicant_student_id == Student.id)
            conds.append(or_(*scope_conds))
        else:
            conds.append(false())
    if type_code:
        conds.append(Request.type_code == type_code)
    if status:
        conds.append(Request.status == status)
    if in_review_only:
        conds.append(
            Request.status.in_([REQUEST_STATUS_SUBMITTED, REQUEST_STATUS_IN_REVIEW])
        )
    if q:
        like = f"%{q}%"
        conds.append(
            or_(
                Request.title.ilike(like),
                Request.request_no.ilike(like),
                Request.summary.ilike(like),
            )
        )
    if conds:
        stmt = stmt.where(and_(*conds))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(*order_by_nulls_last_desc(Request.submitted_at), Request.id.desc()).offset(
        (page - 1) * size
    ).limit(size)
    rows = (await db.execute(stmt)).scalars().all()
    return rows, total


async def add_attachment(db: AsyncSession, **fields) -> RequestAttachment:
    row = RequestAttachment(**fields)
    db.add(row)
    await db.flush()
    return row


async def get_attachment(db: AsyncSession, attachment_id: int) -> RequestAttachment | None:
    return await db.get(RequestAttachment, attachment_id)


async def add_approval_record(db: AsyncSession, **fields) -> RequestApprovalRecord:
    row = RequestApprovalRecord(**fields)
    db.add(row)
    await db.flush()
    return row


async def terminal_statuses() -> tuple[str, ...]:
    return (REQUEST_STATUS_APPROVED, REQUEST_STATUS_REJECTED, REQUEST_STATUS_WITHDRAWN)


async def workflow_done_status() -> str:
    return WORKFLOW_NODE_DONE
