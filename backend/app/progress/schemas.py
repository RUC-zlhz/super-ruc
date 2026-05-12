"""S12 统一进度中心 schema。"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class ProgressItemOut(BaseModel):
    id: str
    source_type: str
    source_id: int
    title: str
    category: str | None = None
    status: str
    status_label: str
    current_step: str | None = None
    due_date: date | None = None
    updated_at: datetime
    detail_url: str


class ProgressMyResult(BaseModel):
    items: list[ProgressItemOut]
    generated_at: datetime
