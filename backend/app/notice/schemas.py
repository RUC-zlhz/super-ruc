"""notice 模块 Pydantic schema。"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TargetRule(BaseModel):
    """目标人群筛选规则。所有字段 AND 组合；每个字段内部 IN 组合。"""

    grade_codes: list[str] | None = None
    major_codes: list[str] | None = None
    class_codes: list[str] | None = None
    political_status: list[str] | None = None
    role_codes: list[str] | None = None
    exclude_graduated: bool = True


class NoticeIn(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    body_md: str = Field(min_length=1)
    summary: str | None = None
    category: str | None = None
    tags: list[str] = []
    target_rule: TargetRule | None = None
    target_summary: str | None = None
    channels: list[str] = Field(default_factory=lambda: ["IN_APP"])
    effective_start: date | None = None
    effective_end: date | None = None
    is_pinned: bool = False
    source_type: str = "MANUAL"
    source_url: str | None = None


class NoticeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body_md: str
    summary: str | None
    category: str | None
    status: str
    source_type: str
    source_url: str | None
    channels: str
    target_rule: dict[str, Any] | None
    target_summary: str | None
    effective_start: date | None
    effective_end: date | None
    is_pinned: bool
    published_at: datetime | None
    updated_at: datetime
    tags: list[str] = []


class NoticeBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: str | None
    category: str | None
    status: str
    is_pinned: bool
    published_at: datetime | None
    updated_at: datetime
    tags: list[str] = []


class TargetPreviewRequest(BaseModel):
    target_rule: TargetRule | None = None


class TargetPreviewResult(BaseModel):
    target_count: int
    sample_student_nos: list[str] = []


class DeliveryDispatchIn(BaseModel):
    channels: list[str] | None = None
    note: str | None = None


class NoticeDeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    user_id: int | None
    channel: str
    status: str
    sent_at: datetime | None
    read_at: datetime | None
    error_code: str | None
    error_message: str | None


class NoticeBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    notice_id: int
    batch_no: str
    channels: str
    target_count: int
    success_count: int
    failed_count: int
    status: str
    note: str | None
    started_at: datetime
    finished_at: datetime | None


class StudentNoticeItem(BaseModel):
    """学生端通知中心的一条。"""

    id: int
    title: str
    summary: str | None
    category: str | None
    is_pinned: bool
    published_at: datetime | None
    read_at: datetime | None
    delivery_id: int | None
