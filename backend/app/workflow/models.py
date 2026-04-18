"""流程 + 审批模块模型 — FR-004/005/006/007/008。

两大子域：

A. 党团流程（FR-004/005）
- WorkflowTemplate: 流程定义（党员发展 / 团员管理 等）
- WorkflowNode: 阶段节点（顺序、触发条件、到期规则、提醒规则）
- StudentWorkflow: 学生的流程实例（继承自 WorkflowTemplate 的一次运行）
- StudentWorkflowNode: 学生在某节点的状态（PENDING/DONE/OVERDUE/DEFERRED）
- WorkflowReminder: 提醒记录（待推送或已推送）

B. 常见事务申请（FR-006/007/008）
- RequestType: 申请类型字典（LEAVE / CERTIFICATE / STAMP / REGISTRATION / MATERIAL）
- Request: 申请单（学生提交，含 form_data JSONB + 状态机）
- RequestAttachment: 申请附件（MinIO 托管）
- RequestApprovalRecord: 流转记录（提交/审批/驳回/撤回/重提/重批）

状态机（Request.status）：
    DRAFT → SUBMITTED → IN_REVIEW → APPROVED
                              └───→ REJECTED → (RESUBMITTED=新 SUBMITTED)
    SUBMITTED/IN_REVIEW → WITHDRAWN
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# ---------- 党团流程状态 ----------
WORKFLOW_KIND_PARTY = "PARTY"
WORKFLOW_KIND_YOUTH = "YOUTH_LEAGUE"

WORKFLOW_NODE_PENDING = "PENDING"
WORKFLOW_NODE_DONE = "DONE"
WORKFLOW_NODE_OVERDUE = "OVERDUE"
WORKFLOW_NODE_DEFERRED = "DEFERRED"
WORKFLOW_NODE_MANUAL = "MANUAL_FOLLOW_UP"

REMINDER_STATUS_PENDING = "PENDING"
REMINDER_STATUS_SENT = "SENT"
REMINDER_STATUS_CANCELLED = "CANCELLED"

# ---------- 申请状态机 ----------
REQUEST_STATUS_DRAFT = "DRAFT"
REQUEST_STATUS_SUBMITTED = "SUBMITTED"
REQUEST_STATUS_IN_REVIEW = "IN_REVIEW"
REQUEST_STATUS_APPROVED = "APPROVED"
REQUEST_STATUS_REJECTED = "REJECTED"
REQUEST_STATUS_WITHDRAWN = "WITHDRAWN"
# v1.5：涉密/敏感事项由审批老师标记"转线下办理"，终止线上流转但保留审批历史。
REQUEST_STATUS_OFFLINE_HANDLED = "OFFLINE_HANDLED"

REQUEST_ACTION_SUBMIT = "SUBMIT"
REQUEST_ACTION_APPROVE = "APPROVE"
REQUEST_ACTION_REJECT = "REJECT"
REQUEST_ACTION_WITHDRAW = "WITHDRAW"
REQUEST_ACTION_RESUBMIT = "RESUBMIT"
REQUEST_ACTION_REOPEN = "REOPEN"
REQUEST_ACTION_COMMENT = "COMMENT"
REQUEST_ACTION_OFFLINE = "OFFLINE_HANDLE"


# =====================================================================
# A. 党团流程
# =====================================================================
class WorkflowTemplate(Base):
    """流程模板定义（如"党员发展完整流程"/"团员管理"）。"""

    __tablename__ = "workflow_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    kind: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True, comment="PARTY/YOUTH_LEAGUE/OTHER"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version_label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    nodes: Mapped[list["WorkflowNode"]] = relationship(
        "WorkflowNode",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="WorkflowNode.sort_order",
        lazy="selectin",
    )


class WorkflowNode(Base):
    """流程模板中的阶段节点。

    - trigger_rule: 触发条件（如"申请提交""上一节点完成""手动启动"）
    - due_rule_days: 距离触发时间多少天到期（NULL 表示无强制期限）
    - reminder_lead_days: 到期前多少天发提醒
    - required_task: 本节点要求学生完成的动作（如"提交入党申请书""参加党校培训"）
    """

    __tablename__ = "workflow_nodes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workflow_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stage_group: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="阶段大类（积极分子/发展对象/预备党员等）"
    )
    required_task: Mapped[str | None] = mapped_column(Text, nullable=True)

    trigger_rule: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PREV_DONE",
        comment="PREV_DONE/MANUAL/ON_APPLY/ON_DATE",
    )
    due_rule_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reminder_lead_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    template: Mapped[WorkflowTemplate] = relationship("WorkflowTemplate", back_populates="nodes")

    __table_args__ = (
        UniqueConstraint("template_id", "code", name="uq_workflow_nodes_template_code"),
        Index("ix_workflow_nodes_template_sort", "template_id", "sort_order"),
    )


class StudentWorkflow(Base):
    """学生的流程实例。一个学生针对同一模板只应有一个 ACTIVE 实例。"""

    __tablename__ = "student_workflows"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workflow_templates.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ACTIVE",
        comment="ACTIVE/COMPLETED/SUSPENDED",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_node_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("workflow_nodes.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    template: Mapped[WorkflowTemplate] = relationship("WorkflowTemplate", lazy="joined")
    node_states: Mapped[list["StudentWorkflowNode"]] = relationship(
        "StudentWorkflowNode",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="StudentWorkflowNode.id",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_student_workflows_student_template", "student_id", "template_id"),
    )


class StudentWorkflowNode(Base):
    """学生在某节点的运行态。"""

    __tablename__ = "student_workflow_nodes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workflow_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("student_workflows.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    node_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("workflow_nodes.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default=WORKFLOW_NODE_PENDING, index=True
    )
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True, comment="完成佐证/备注")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    workflow: Mapped[StudentWorkflow] = relationship("StudentWorkflow", back_populates="node_states")
    node: Mapped[WorkflowNode] = relationship("WorkflowNode", lazy="joined")

    __table_args__ = (
        UniqueConstraint("workflow_id", "node_id", name="uq_student_workflow_nodes_pair"),
    )


class WorkflowReminder(Base):
    """提醒记录。由"生成提醒清单"接口批量插入，发送通道由 notice 模块消费。"""

    __tablename__ = "workflow_reminders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workflow_node_state_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("student_workflow_nodes.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reminder_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    channel: Mapped[str] = mapped_column(
        String(16), nullable=False, default="IN_APP", comment="IN_APP/EMAIL/SMS"
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=REMINDER_STATUS_PENDING, index=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# =====================================================================
# B. 常见事务申请
# =====================================================================
class RequestType(Base):
    """申请类型字典。form_schema 为 JSON Schema，便于前端动态渲染。"""

    __tablename__ = "request_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="LEAVE/CERTIFICATE/STAMP/REGISTRATION/MATERIAL/OTHER",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    form_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    attachment_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_withdraw: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    withdraw_hours_limit: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="提交多少小时内可撤回；NULL 表示不限时"
    )
    # 允许的审批角色（逗号分隔，如 "COUNSELOR,COLLEGE_LEADER"）
    approver_roles: Mapped[str] = mapped_column(String(256), nullable=False, default="COUNSELOR")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Request(Base):
    """申请单主表。

    - form_data: 按 request_type.form_schema 填写的表单值
    - 同一业务键（request_no）全局唯一
    - 被驳回或撤回后的重提：在同一 Request 上递增 revision 并重置状态为 SUBMITTED
    """

    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    request_no: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("request_types.id"), nullable=False, index=True
    )
    type_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    applicant_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    applicant_student_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    form_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    summary: Mapped[str | None] = mapped_column(String(512), nullable=True)

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=REQUEST_STATUS_DRAFT, index=True
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    decision_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    type_ref: Mapped[RequestType] = relationship("RequestType", lazy="joined")
    attachments: Mapped[list["RequestAttachment"]] = relationship(
        "RequestAttachment",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    approval_records: Mapped[list["RequestApprovalRecord"]] = relationship(
        "RequestApprovalRecord",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="RequestApprovalRecord.occurred_at",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_requests_status_type", "status", "type_code"),
        Index("ix_requests_applicant_status", "applicant_user_id", "status"),
    )


class RequestAttachment(Base):
    """申请附件。MinIO 托管，DB 仅存元数据。"""

    __tablename__ = "request_attachments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    object_bucket: Mapped[str] = mapped_column(String(64), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    uploaded_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    request: Mapped[Request] = relationship("Request", back_populates="attachments")


class RequestApprovalRecord(Base):
    """审批流转记录（FR-007 历史 + FR-008 撤回/重提/重批留痕）。"""

    __tablename__ = "request_approval_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    action: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    status_before: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status_after: Mapped[str | None] = mapped_column(String(16), nullable=True)
    operator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    operator_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    request: Mapped[Request] = relationship("Request", back_populates="approval_records")
