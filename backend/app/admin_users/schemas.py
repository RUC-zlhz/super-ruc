"""Schemas for backend-account bulk import."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AdminUserImportBatchBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_no: str
    filename: str
    status: str
    total_rows: int
    ok_rows: int
    warn_rows: int
    fatal_rows: int
    created_rows: int
    existing_rows: int
    role_granted_rows: int
    unchanged_rows: int
    operator_id: int | None
    operator_role: str | None
    started_at: datetime
    finished_at: datetime | None
    committed_at: datetime | None
    summary: dict[str, Any] | None = None


class AdminUserImportBatchDetail(AdminUserImportBatchBrief):
    pass


class AdminUserImportRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    row_no: int
    work_no: str | None
    role_code: str | None
    scope_code: str | None
    severity: str
    result: str
    field_name: str | None
    message: str | None
    raw_data: dict[str, Any] | None
    normalized_data: dict[str, Any] | None


class AdminUserImportPreviewResult(BaseModel):
    batch: AdminUserImportBatchDetail
    rows: list[AdminUserImportRowOut]


class AdminUserImportCommitIn(BaseModel):
    batch_id: int = Field(ge=1)
    note: str | None = Field(default=None, max_length=256)


class AdminUserCredentialOut(BaseModel):
    work_no: str
    display_name: str
    role_code: str
    scope_code: str | None = None
    initial_password: str


class AdminUserImportCommitResult(BaseModel):
    batch: AdminUserImportBatchDetail
    rows: list[AdminUserImportRowOut]
    credentials: list[AdminUserCredentialOut]


class AdminUserImportTemplateFormat(BaseModel):
    format: Literal["xlsx", "csv"] = "xlsx"
