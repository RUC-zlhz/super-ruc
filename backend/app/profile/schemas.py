"""profile 模块 Pydantic schema — FR-018。"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StudentBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_no: str
    full_name: str
    gender: str | None
    grade_code: str | None
    major_code: str | None
    class_code: str | None
    political_status: str | None
    enrollment_year: int | None
    expected_graduation_year: int | None
    status: str
    enrollment_status: str
    enrollment_status_reason: str | None = None
    enrollment_status_updated_at: datetime | None = None


class ProfileFactIn(BaseModel):
    fact_type: str
    title: str = Field(min_length=1, max_length=256)
    description: str | None = None
    role_in_activity: str | None = None
    started_on: date | None = None
    ended_on: date | None = None
    hours: float | None = None
    rank_label: str | None = None
    attachments: dict[str, Any] | None = None
    extra: dict[str, Any] | None = None
    source: str = "TEACHER_ENTRY"
    source_ref: str | None = None
    is_sensitive: bool = False


class ProfileFactOut(BaseModel):
    id: int
    student_id: int
    fact_type: str
    title: str
    description: str | None
    role_in_activity: str | None
    started_on: date | None
    ended_on: date | None
    hours: float | None
    rank_label: str | None
    attachments: dict[str, Any] | None
    extra: dict[str, Any] | None
    source: str
    source_label: str | None = None
    source_ref: str | None
    approval_status: str
    is_sensitive: bool
    created_by: int | None = None
    updated_by: int | None = None
    created_by_name: str | None = None
    updated_by_name: str | None = None
    updated_at: datetime
    review_comment: str | None = None


class ProfileFactStudentView(BaseModel):
    """学生侧视图：不暴露 created_by / source_ref / approved_by 等管理元数据。"""

    id: int
    fact_type: str
    title: str
    description: str | None
    role_in_activity: str | None
    started_on: date | None
    ended_on: date | None
    hours: float | None
    rank_label: str | None
    attachments: dict[str, Any] | None = None
    approval_status: str
    updated_at: datetime


class ProfileFactSubmissionOut(BaseModel):
    id: int
    fact_type: str
    title: str
    description: str | None
    role_in_activity: str | None
    started_on: date | None
    ended_on: date | None
    hours: float | None
    rank_label: str | None
    attachments: dict[str, Any] | None = None
    approval_status: str
    review_comment: str | None = None
    updated_at: datetime


class ProfileSummary(BaseModel):
    student: StudentBasic
    facts: list[ProfileFactOut] = []
    research_count: int = 0
    competition_count: int = 0
    practice_count: int = 0
    volunteer_hours: float = 0
    leadership_count: int = 0
    masked_fields: list[str] = []
    hidden_sensitive_fact_count: int = 0
    full_view_approved_fields: list[str] = []
    full_view_sensitive_facts_approved: bool = False
    generated_at: datetime


class ProfileStudentSelfView(BaseModel):
    student: StudentBasic
    facts: list[ProfileFactStudentView] = []
    research_count: int = 0
    competition_count: int = 0
    practice_count: int = 0
    volunteer_hours: float = 0
    leadership_count: int = 0
    masked_fields: list[str] = []
    hidden_sensitive_fact_count: int = 0
    full_view_approved_fields: list[str] = []
    full_view_sensitive_facts_approved: bool = False
    generated_at: datetime


class CorrectionIn(BaseModel):
    fact_id: int | None = None
    field_name: str
    proposed_value: str | None = None
    reason: str | None = None


class AcademicCorrectionIn(BaseModel):
    field_name: str = Field(description="grade_code/major_code/class_code/expected_graduation_year")
    proposed_value: str | None = None
    reason: str | None = None


class StudentAcademicInfoPatch(BaseModel):
    student_no: str | None = None
    full_name: str | None = None
    id_card: str | None = None
    phone: str | None = None
    gender: str | None = None
    grade_code: str | None = None
    major_code: str | None = None
    class_code: str | None = None
    political_status: str | None = None
    enrollment_year: int | None = None
    expected_graduation_year: int | None = None


class StudentCreateIn(BaseModel):
    student_no: str = Field(min_length=1, max_length=32)
    full_name: str = Field(min_length=1, max_length=64)
    id_card: str | None = Field(default=None, max_length=32)
    phone: str | None = Field(default=None, max_length=32)
    gender: str | None = Field(default=None, max_length=8)
    grade_code: str | None = Field(default=None, max_length=16)
    major_code: str | None = Field(default=None, max_length=32)
    class_code: str | None = Field(default=None, max_length=32)
    political_status: str | None = Field(default=None, max_length=32)
    enrollment_year: int | None = None
    expected_graduation_year: int | None = None


class StudentWechatBindingOut(BaseModel):
    student_id: int
    student_no: str
    bound: bool
    user_id: int | None = None
    display_name: str | None = None
    openid_masked: str | None = None
    unionid_masked: str | None = None
    is_active: bool | None = None
    last_login_at: datetime | None = None
    roles: list[str] = []


class CorrectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    fact_id: int | None
    field_name: str
    current_value: str | None
    proposed_value: str | None
    reason: str | None
    status: str
    handled_by: int | None
    handled_at: datetime | None
    handler_comment: str | None
    created_at: datetime


class CorrectionDecisionIn(BaseModel):
    decision: str = Field(description="APPROVED/REJECTED")
    comment: str | None = None
    apply_to_fact: bool = True


class ProfileFactDecisionIn(BaseModel):
    decision: str = Field(description="APPROVED/REJECTED")
    comment: str | None = None


class ProfileFullViewRequestIn(BaseModel):
    target_type: str = Field(description="STUDENT_FIELD/PROFILE_FACTS")
    field_name: str | None = None
    reason: str | None = None


class ProfileFullViewRequestOut(BaseModel):
    id: int
    student_id: int
    requester_user_id: int | None = None
    requester_name: str | None = None
    target_type: str
    field_name: str | None = None
    reason: str | None = None
    status: str
    handled_by: int | None = None
    handled_at: datetime | None = None
    handler_comment: str | None = None
    created_at: datetime


class ProfileFullViewDecisionIn(BaseModel):
    decision: str = Field(description="APPROVED/REJECTED")
    comment: str | None = None
