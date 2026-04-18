"""knowledge 模块 Pydantic schema。"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- 分类 ----------
class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    parent_code: str | None = None
    sort_order: int = 0
    is_active: bool = True


class CategoryIn(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    parent_code: str | None = None
    sort_order: int = 0


# ---------- 来源 ----------
class SourceIn(BaseModel):
    source_name: str = Field(min_length=1, max_length=256)
    source_url: str | None = None
    issuing_org: str | None = None
    version_label: str | None = None
    effective_date: date | None = None
    expires_on: date | None = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_name: str
    source_url: str | None
    issuing_org: str | None
    version_label: str | None
    effective_date: date | None
    expires_on: date | None
    is_active: bool
    updated_at: datetime


# ---------- 模板 ----------
class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_name: str
    template_type: str
    category_code: str | None
    applicable_scenario: str | None
    version_label: str | None
    file_size: int | None
    mime_type: str | None
    status: str
    uploaded_at: datetime


class TemplateDownloadLink(BaseModel):
    template_id: int
    download_url: str
    expires_in_minutes: int


# ---------- 条目 ----------
class EntryTagItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tag: str


class EntryTemplateRef(BaseModel):
    template_id: int
    template_name: str
    template_type: str
    version_label: str | None


class EntryBrief(BaseModel):
    """搜索列表中的简略视图。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    summary: str | None
    category_code: str | None
    status: str
    ambiguity_flag: bool
    version_label: str | None
    updated_at: datetime
    tags: list[str] = []


class EntryDetail(BaseModel):
    """学生侧详情视图（FR-001 展示字段 + FR-002 治理元数据）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    summary: str | None
    category_code: str | None
    applicable_condition: str | None
    required_materials: str | None
    process_steps: str | None
    body_md: str | None
    status: str
    version_label: str | None
    ambiguity_flag: bool
    manual_consult_hint: str | None
    published_at: datetime | None
    updated_at: datetime
    tags: list[str] = []
    source: SourceOut | None = None
    templates: list[EntryTemplateRef] = []


class EntryCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=128, pattern=r"^[a-z0-9][a-z0-9-_]*$")
    title: str = Field(min_length=1, max_length=256)
    summary: str | None = None
    category_code: str | None = None
    applicable_condition: str | None = None
    required_materials: str | None = None
    process_steps: str | None = None
    body_md: str | None = None
    source_id: int | None = None
    version_label: str | None = None
    ambiguity_flag: bool = False
    manual_consult_hint: str | None = None
    tags: list[str] = []
    template_ids: list[int] = []


class EntryUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    category_code: str | None = None
    applicable_condition: str | None = None
    required_materials: str | None = None
    process_steps: str | None = None
    body_md: str | None = None
    source_id: int | None = None
    version_label: str | None = None
    ambiguity_flag: bool | None = None
    manual_consult_hint: str | None = None
    tags: list[str] | None = None
    template_ids: list[int] | None = None


class EntryStateAction(BaseModel):
    note: str | None = None


class RevisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    version_label: str | None
    status_before: str | None
    status_after: str | None
    operator_id: int | None
    operator_role: str | None
    note: str | None
    occurred_at: datetime


# ---------- AI 匹配 ----------
class AiMatchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=512)
    top_k: int = Field(default=3, ge=1, le=5)


class AiMatchCandidate(BaseModel):
    entry_id: int
    slug: str
    title: str
    score: float
    reason: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    version_label: str | None = None
    ambiguity_flag: bool = False


class AiMatchResponse(BaseModel):
    engine: str = Field(description="keyword | claude-haiku")
    candidates: list[AiMatchCandidate]
    manual_consult_required: bool = False
    manual_consult_hint: str | None = None
    disclaimer: str = (
        "本结果基于已发布的官方知识条目匹配，如遇特殊/模糊情形请转人工咨询。"
    )
