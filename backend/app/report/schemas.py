"""report 模块 Pydantic schema — FR-014 学业缺口 / FR-016 运营看板。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


# ============================================================
# FR-014 学业缺口（弱结论）
# ============================================================
class AcademicModuleGap(BaseModel):
    module_code: str
    module_name: str
    module_type: str
    credits_required: float
    credits_earned: float
    credits_gap: float
    passed_courses: list[str] = []
    note: str | None = None


class AcademicGapResult(BaseModel):
    """学业缺口展示结果。**不得输出毕业结论**。"""

    student_no: str
    student_name: str
    grade_code: str | None
    major_code: str | None
    plan_id: int | None = None
    plan_name: str | None = None
    total_credits_required: float | None = None
    total_credits_earned: float = 0
    modules: list[AcademicModuleGap] = []
    suggested_courses: list[dict] = []
    disclaimer: str = (
        "本结果仅为辅助提示，不构成毕业资格、课程替代或教务最终结论；"
        "请以学院/学校正式审核结果为准。"
    )
    data_warnings: list[str] = []
    generated_at: datetime


class AcademicGapAggregateItem(BaseModel):
    student_id: int
    student_no: str
    student_name: str
    grade_code: str | None
    major_code: str | None
    total_credits_required: float | None = None
    total_credits_earned: float = 0
    credits_gap: float | None = None
    data_warnings: list[str] = []
    generated_at: datetime


# ============================================================
# FR-016 运营看板
# ============================================================
class KVMetric(BaseModel):
    key: str
    label: str
    value: int | float
    sub_label: str | None = None


class RequestSummary(BaseModel):
    """按 request_type × status 汇总。"""

    type_code: str
    type_name: str
    draft: int = 0
    submitted: int = 0
    in_review: int = 0
    approved: int = 0
    rejected: int = 0
    withdrawn: int = 0
    total: int = 0


class NoticeSummary(BaseModel):
    total_notices: int
    published_notices: int
    total_batches: int
    total_deliveries: int
    sent: int
    failed: int
    skipped: int
    read: int


class WorkflowSummary(BaseModel):
    template_code: str
    template_name: str
    kind: str
    total_students: int
    nodes_pending: int
    nodes_overdue: int
    nodes_done: int


class OverviewResult(BaseModel):
    metrics: list[KVMetric]
    requests: list[RequestSummary]
    notices: NoticeSummary | None
    workflows: list[WorkflowSummary]
    generated_at: datetime
    disclaimer: str = (
        "本看板基于学院平台留痕数据汇总，仅用于内部运营观察。"
    )
