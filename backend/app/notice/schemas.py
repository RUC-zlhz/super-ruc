"""notice 模块 Pydantic schema。"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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

    @model_validator(mode="after")
    def validate_effective_range(self) -> NoticeIn:
        if (
            self.effective_start is not None
            and self.effective_end is not None
            and self.effective_start > self.effective_end
        ):
            raise ValueError("生效结束日期不能早于生效开始日期")
        return self


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
    source_type: str
    channels: str
    target_summary: str | None
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
    target_handle: str | None
    sent_at: datetime | None
    read_at: datetime | None
    error_code: str | None
    error_message: str | None


class NoticeDeliveryAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    delivery_id: int
    provider: str
    attempt_no: int
    status: str
    target_handle: str | None
    provider_message_id: str | None
    error_code: str | None
    error_message: str | None
    receipt_status: str | None
    receipt_at: datetime | None
    created_at: datetime


class NoticeDeliveryReceiptMockIn(BaseModel):
    receipt_status: str = Field(default="DELIVERED", max_length=32)


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


class NoticeSourceIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    source_type: str = Field(description="URL/RSS")
    source_url: str = Field(min_length=1, max_length=1024)
    category: str | None = None
    target_rule: TargetRule | None = None
    is_active: bool = True


class NoticeSourcePatchIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    source_type: str | None = Field(default=None, description="URL/RSS")
    source_url: str | None = Field(default=None, min_length=1, max_length=1024)
    category: str | None = None
    target_rule: TargetRule | None = None
    is_active: bool | None = None


class NoticeSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source_type: str
    source_url: str
    category: str | None
    target_rule: dict[str, Any] | None
    is_active: bool
    last_run_at: datetime | None
    created_by: int | None
    updated_by: int | None
    created_at: datetime
    updated_at: datetime


class NoticeIngestRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    status: str
    fetched_count: int
    created_count: int
    skipped_count: int
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None
    created_by: int | None


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


class WechatSubscribeTemplateOut(BaseModel):
    scene: str
    template_id: str


class WechatSubscribeConfigOut(BaseModel):
    enabled: bool
    templates: list[WechatSubscribeTemplateOut] = []


class WechatSubscribeResultIn(BaseModel):
    template_id: str = Field(min_length=1, max_length=128)
    status: str = Field(description="accept/reject/ban/filter")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized not in {"accept", "reject", "ban", "filter"}:
            raise ValueError("订阅授权结果仅支持 accept/reject/ban/filter")
        return normalized


class WechatSubscribeAuthorizationIn(BaseModel):
    results: list[WechatSubscribeResultIn] = Field(min_length=1)


class WechatSubscribeAuthorizationOut(BaseModel):
    template_id: str
    scene: str
    status: str
