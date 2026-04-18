"""exchange 模块 Pydantic schema — FR-009 / FR-015。"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# 导入批次
# ============================================================
class ImportBatchBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_no: str
    import_type: str
    filename: str
    status: str
    total_rows: int
    ok_rows: int
    warn_rows: int
    fatal_rows: int
    operator_id: int | None
    operator_role: str | None
    started_at: datetime
    finished_at: datetime | None
    note: str | None


class ImportBatchRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    row_no: int
    severity: str
    result: str
    field_name: str | None
    message: str | None
    raw_data: dict[str, Any] | None


class ImportBatchDetail(ImportBatchBrief):
    summary: dict[str, Any] | None = None


class ImportCommitIn(BaseModel):
    note: str | None = None


class ImportPreviewResult(BaseModel):
    batch: ImportBatchBrief
    rows: list[ImportBatchRowOut]


# ============================================================
# 培养方案
# ============================================================
class CurriculumModuleIn(BaseModel):
    module_code: str = Field(min_length=1, max_length=64)
    module_name: str = Field(min_length=1, max_length=128)
    module_type: str = Field(
        default="REQUIRED",
        description="REQUIRED/ELECTIVE/GENERAL/PRACTICE/OTHER",
    )
    credits_required: float = 0
    courses: list[dict[str, Any]] | None = None
    note: str | None = None
    sort_order: int = 0


class CurriculumModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    module_code: str
    module_name: str
    module_type: str
    credits_required: float
    courses: list[dict[str, Any]] | None
    note: str | None
    sort_order: int


class CurriculumPlanIn(BaseModel):
    grade_code: str = Field(min_length=1, max_length=16)
    major_code: str = Field(min_length=1, max_length=32)
    plan_name: str = Field(min_length=1, max_length=256)
    version_label: str | None = None
    total_credits_required: float | None = None
    effective_from: date | None = None
    is_active: bool = True
    note: str | None = None
    modules: list[CurriculumModuleIn] = []


class CurriculumPlanBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    grade_code: str
    major_code: str
    plan_name: str
    version_label: str | None
    total_credits_required: float | None
    effective_from: date | None
    is_active: bool
    updated_at: datetime


class CurriculumPlanDetail(CurriculumPlanBrief):
    note: str | None = None
    modules: list[CurriculumModuleOut] = []


# ============================================================
# 课程等价 / 开课
# ============================================================
class CourseEquivalenceIn(BaseModel):
    grade_code: str | None = None
    major_code: str | None = None
    source_course_code: str = Field(min_length=1, max_length=64)
    source_course_name: str | None = None
    target_course_code: str = Field(min_length=1, max_length=64)
    target_course_name: str | None = None
    ratio: float = 1.0
    note: str | None = None
    is_active: bool = True


class CourseEquivalenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    grade_code: str | None
    major_code: str | None
    source_course_code: str
    source_course_name: str | None
    target_course_code: str
    target_course_name: str | None
    ratio: float
    note: str | None
    is_active: bool
    created_at: datetime


class CourseOfferingIn(BaseModel):
    term_code: str = Field(min_length=1, max_length=16)
    course_code: str = Field(min_length=1, max_length=64)
    course_name: str = Field(min_length=1, max_length=128)
    credits: float = 0
    course_type: str | None = None
    major_codes: str | None = None
    grade_codes: str | None = None
    teacher: str | None = None
    capacity: int | None = None
    note: str | None = None
    is_active: bool = True


class CourseOfferingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    term_code: str
    course_code: str
    course_name: str
    credits: float
    course_type: str | None
    major_codes: str | None
    grade_codes: str | None
    teacher: str | None
    capacity: int | None
    note: str | None
    is_active: bool
    created_at: datetime


# ============================================================
# 导出
# ============================================================
class ExportRequest(BaseModel):
    """通用导出请求。scope 决定导出什么。"""

    scope: str = Field(
        description="STUDENTS/TRANSCRIPT/CURRICULUM/COURSE_OFFERINGS/AUDIT",
    )
    filters: dict[str, Any] = {}
