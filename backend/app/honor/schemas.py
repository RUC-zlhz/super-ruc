"""honor 模块 Pydantic schema — FR-017."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HonorCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool


class HonorCategoryIn(BaseModel):
    id: int | None = None
    code: str
    name: str
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True


class HonorRecipientIn(BaseModel):
    student_id: int | None = None
    student_no_snapshot: str | None = None
    display_name: str = Field(min_length=1, max_length=64)
    major_snapshot: str | None = None
    grade_snapshot: str | None = None
    class_snapshot: str | None = None
    role_in_collective: str | None = None


class HonorRecipientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int | None
    student_no_snapshot: str | None
    display_name: str
    major_snapshot: str | None
    grade_snapshot: str | None
    class_snapshot: str | None
    role_in_collective: str | None


class HonorRecordIn(BaseModel):
    category_code: str
    title: str = Field(min_length=1, max_length=256)
    level: str = Field(description="NATIONAL/PROVINCIAL/MINISTERIAL/SCHOOL")
    awarded_by: str
    document_no: str | None = None
    announced_at: date
    effective_from: date | None = None
    effective_to: date | None = None
    is_collective: bool = False
    display_order: int = Field(default=0, ge=0)
    summary: str | None = None
    story_md: str | None = None
    acceptance_speech: str | None = None
    cover_image_url: str | None = None
    media: dict[str, Any] | None = None
    consent_flag: bool = False
    recipients: list[HonorRecipientIn] = []


class PublicHonorRecordBrief(BaseModel):
    id: int
    category_code: str
    category_name: str | None = None
    title: str
    level: str
    awarded_by: str
    announced_at: date
    status: str
    is_collective: bool
    display_order: int = 0
    cover_image_url: str | None = None
    summary: str | None = None
    effective_to: date | None = None
    recipient_names: list[str] = []
    is_historical: bool = False
    history_reason: str | None = None


class PublicHonorRecordDetail(BaseModel):
    id: int
    category_code: str
    category_name: str | None = None
    title: str
    level: str
    awarded_by: str
    document_no: str | None = None
    announced_at: date
    effective_from: date | None = None
    effective_to: date | None = None
    is_collective: bool
    display_order: int = 0
    summary: str | None = None
    story_md: str | None = None
    acceptance_speech: str | None = None
    cover_image_url: str | None = None
    media: dict[str, Any] | None = None
    status: str
    view_count: int
    recipients: list[HonorRecipientOut] = []
    updated_at: datetime
    is_historical: bool = False
    history_reason: str | None = None


class AdminHonorRecordBrief(BaseModel):
    id: int
    category_code: str
    category_name: str | None = None
    title: str
    level: str
    awarded_by: str
    announced_at: date
    status: str
    is_collective: bool
    display_order: int = 0
    cover_image_url: str | None = None
    summary: str | None = None
    effective_to: date | None = None
    recipient_names: list[str] = []
    consent_flag: bool
    updated_at: datetime
    updated_by_name: str | None = None
    is_historical: bool = False
    history_reason: str | None = None


class AdminHonorRecordDetail(BaseModel):
    id: int
    category_code: str
    category_name: str | None = None
    title: str
    level: str
    awarded_by: str
    document_no: str | None = None
    announced_at: date
    effective_from: date | None = None
    effective_to: date | None = None
    is_collective: bool
    display_order: int = 0
    summary: str | None = None
    story_md: str | None = None
    acceptance_speech: str | None = None
    cover_image_url: str | None = None
    media: dict[str, Any] | None = None
    status: str
    consent_flag: bool
    view_count: int
    archived_at: datetime | None = None
    archive_reason: str | None = None
    recipients: list[HonorRecipientOut] = []
    updated_at: datetime
    updated_by_name: str | None = None
    is_historical: bool = False
    history_reason: str | None = None


class HonorArchiveIn(BaseModel):
    reason: str | None = None
    new_status: str = Field(default="ARCHIVED", description="ARCHIVED/REVOKED")
