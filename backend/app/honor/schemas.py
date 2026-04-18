"""honor 模块 Pydantic schema — FR-017。"""
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
    summary: str | None = None
    story_md: str | None = None
    acceptance_speech: str | None = None
    cover_image_url: str | None = None
    media: dict[str, Any] | None = None
    consent_flag: bool = False
    recipients: list[HonorRecipientIn] = []


class HonorRecordBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_code: str
    title: str
    level: str
    awarded_by: str
    announced_at: date
    status: str
    is_collective: bool
    cover_image_url: str | None
    summary: str | None
    effective_to: date | None
    recipient_names: list[str] = []


class HonorRecordDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_code: str
    title: str
    level: str
    awarded_by: str
    document_no: str | None
    announced_at: date
    effective_from: date | None
    effective_to: date | None
    is_collective: bool
    summary: str | None
    story_md: str | None
    acceptance_speech: str | None
    cover_image_url: str | None
    media: dict[str, Any] | None
    status: str
    consent_flag: bool
    view_count: int
    archived_at: datetime | None
    archive_reason: str | None
    recipients: list[HonorRecipientOut] = []
    updated_at: datetime


class HonorArchiveIn(BaseModel):
    reason: str | None = None
    new_status: str = Field(default="ARCHIVED", description="ARCHIVED/REVOKED")
