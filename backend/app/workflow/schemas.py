"""workflow 模块 Pydantic schema。"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# A. 党团流程（FR-004 / FR-005）
# ============================================================
class WorkflowNodeIn(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    sort_order: int = 0
    stage_group: str | None = None
    required_task: str | None = None
    trigger_rule: str = "PREV_DONE"
    due_rule_days: int | None = None
    reminder_lead_days: int | None = None
    reminder_enabled: bool = True
    reminder_channel: str = "IN_APP"
    repeat_interval_days: int | None = None
    max_reminders: int | None = 1
    is_terminal: bool = False
    is_active: bool = True


class WorkflowNodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    sort_order: int
    stage_group: str | None
    required_task: str | None
    trigger_rule: str
    due_rule_days: int | None
    reminder_lead_days: int | None
    reminder_enabled: bool
    reminder_channel: str
    repeat_interval_days: int | None
    max_reminders: int | None
    is_terminal: bool
    is_active: bool


class WorkflowTemplateIn(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    kind: str = Field(description="PARTY/YOUTH_LEAGUE/OTHER")
    description: str | None = None
    version_label: str | None = None
    nodes: list[WorkflowNodeIn] = []


class WorkflowTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    kind: str
    description: str | None
    version_label: str | None
    is_active: bool
    updated_at: datetime
    nodes: list[WorkflowNodeOut] = []


class StudentWorkflowNodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    node_id: int
    node_code: str
    node_name: str
    sort_order: int
    stage_group: str | None
    required_task: str | None
    status: str
    triggered_at: datetime | None
    due_date: date | None
    completed_at: datetime | None
    evidence: str | None
    note: str | None


class StudentWorkflowDetail(BaseModel):
    """学生侧本人流程视图（FR-004）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    template_code: str
    template_name: str
    kind: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    current_node_id: int | None
    current_node_name: str | None
    next_action_hint: str | None
    nodes: list[StudentWorkflowNodeOut]


class StudentWorkflowBrief(BaseModel):
    """管理端列出待跟进学生的简略视图（FR-005）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    student_no: str | None
    student_name: str | None
    template_code: str
    template_name: str
    current_node_name: str | None
    current_node_status: str | None
    due_date: date | None


class StudentWorkflowStart(BaseModel):
    student_id: int
    template_code: str
    note: str | None = None


class NodeCompleteIn(BaseModel):
    evidence: str | None = None
    note: str | None = None


class NodeMarkStatusIn(BaseModel):
    status: str = Field(description="DEFERRED / MANUAL_FOLLOW_UP / PENDING / OVERDUE")
    note: str | None = None


class ReminderGenerateIn(BaseModel):
    as_of_date: date | None = None
    channel: str = "IN_APP"


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_node_state_id: int
    student_id: int
    reminder_date: date
    channel: str
    status: str
    sent_at: datetime | None
    message: str | None
    cancel_reason: str | None
    error_message: str | None
    created_at: datetime


class ReminderRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    as_of_date: date
    channel: str
    trigger_mode: str
    status: str
    created_count: int
    sent_count: int
    skipped_count: int
    cancelled_count: int
    failed_count: int
    error_message: str | None
    operator_id: int | None
    operator_role: str | None
    started_at: datetime
    finished_at: datetime | None


class ReminderAdminOut(BaseModel):
    id: int
    workflow_node_state_id: int
    student_id: int
    student_no: str | None
    student_name: str | None
    template_code: str
    template_name: str
    node_code: str
    node_name: str
    node_status: str
    due_date: date | None
    reminder_date: date
    channel: str
    status: str
    sent_at: datetime | None
    message: str | None
    cancel_reason: str | None
    error_message: str | None
    created_at: datetime


# ============================================================
# B. 事务申请（FR-006 / FR-007 / FR-008）
# ============================================================
class RequestTypeIn(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    category: str = Field(description="LEAVE/CERTIFICATE/STAMP/REGISTRATION/MATERIAL/OTHER")
    description: str | None = None
    form_schema: dict[str, Any] | None = None
    attachment_required: bool = False
    allow_withdraw: bool = True
    withdraw_hours_limit: int | None = None
    approver_roles: str = "COUNSELOR"


class RequestTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: str
    description: str | None
    form_schema: dict[str, Any] | None
    attachment_required: bool
    allow_withdraw: bool
    withdraw_hours_limit: int | None
    approver_roles: str
    is_active: bool


class RequestCreate(BaseModel):
    type_code: str
    title: str = Field(min_length=1, max_length=256)
    form_data: dict[str, Any] = Field(default_factory=dict)
    summary: str | None = None
    attachment_ids: list[int] = []


class RequestUpdate(BaseModel):
    title: str | None = None
    form_data: dict[str, Any] | None = None
    summary: str | None = None


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_size: int | None
    mime_type: str | None
    uploaded_at: datetime


class ApprovalRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    revision: int
    action: str
    status_before: str | None
    status_after: str | None
    operator_id: int | None
    operator_role: str | None
    comment: str | None
    occurred_at: datetime


class RequestBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_no: str
    type_code: str
    title: str
    status: str
    revision: int
    applicant_user_id: int
    applicant_student_id: int | None
    submitted_at: datetime | None
    updated_at: datetime


class RequestDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_no: str
    type_code: str
    type_name: str
    category: str
    title: str
    summary: str | None
    form_data: dict[str, Any]
    status: str
    revision: int
    applicant_user_id: int
    applicant_student_id: int | None
    submitted_at: datetime | None
    decided_at: datetime | None
    decided_by: int | None
    decision_comment: str | None
    withdrawn_at: datetime | None
    attachments: list[AttachmentOut]
    approval_records: list[ApprovalRecordOut]


class ApprovalActionIn(BaseModel):
    comment: str | None = None


class OfflineHandleIn(BaseModel):
    """v1.5 转线下办理入参。

    contact_info 在学生端展示为线下联系方式；note 作为内部说明。
    """

    contact_info: str = Field(..., min_length=1, max_length=256)
    note: str | None = Field(default=None, max_length=512)


class ReopenRequestIn(BaseModel):
    """受控重开入参。默认直接回到审核中，也可回到待受理。"""

    comment: str | None = Field(default=None, max_length=512)
    target_status: Literal["IN_REVIEW", "SUBMITTED"] = "IN_REVIEW"


# ============================================================
# C. 理论自测题库（FR-005）
# ============================================================
class QuizOption(BaseModel):
    """选择题单个选项。"""

    key: str = Field(min_length=1, max_length=4, description="A/B/C/D…")
    text: str = Field(min_length=1, max_length=512)


class QuizQuestionIn(BaseModel):
    """管理端新增/更新题目入参。"""

    topic: str = Field(min_length=1, max_length=64)
    qtype: str = Field(description="SINGLE/MULTI/JUDGE")
    stem: str = Field(min_length=1)
    options_json: list[QuizOption] | None = None
    correct_key: str = Field(min_length=1, max_length=64)
    explanation: str | None = None
    difficulty: str | None = Field(default=None, description="EASY/MEDIUM/HARD")


class QuizQuestionUpdate(BaseModel):
    topic: str | None = None
    qtype: str | None = None
    stem: str | None = None
    options_json: list[QuizOption] | None = None
    correct_key: str | None = None
    explanation: str | None = None
    difficulty: str | None = None
    is_active: bool | None = None


class QuizQuestionAdminOut(BaseModel):
    """管理端返回（含正确答案与解析）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str
    qtype: str
    stem: str
    options_json: list[dict[str, Any]] | None
    correct_key: str
    explanation: str | None
    difficulty: str | None
    is_active: bool
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class QuizQuestionStudentOut(BaseModel):
    """学生抽题返回（屏蔽正确答案和解析）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str
    qtype: str
    stem: str
    options_json: list[dict[str, Any]] | None
    difficulty: str | None


class QuizDrawOut(BaseModel):
    batch_id: str
    questions: list[QuizQuestionStudentOut]


class QuizAnswerIn(BaseModel):
    question_id: int
    answer: str = Field(default="", max_length=64)


class QuizSubmitIn(BaseModel):
    batch_id: str = Field(min_length=1, max_length=36)
    answers: list[QuizAnswerIn] = Field(min_length=1)


class QuizItemResultOut(BaseModel):
    question_id: int
    is_correct: bool
    correct_key: str
    explanation: str | None = None


class QuizSubmitOut(BaseModel):
    batch_id: str
    total: int
    correct: int
    score: int
    items: list[QuizItemResultOut]


class QuizRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    question_id: int
    batch_id: str | None
    answer: str
    is_correct: bool
    score: int
    submitted_at: datetime
