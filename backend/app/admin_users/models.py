"""Dedicated batch tables for backend-account bulk creation."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

BATCH_STATUS_PROCESSING = "PROCESSING"
BATCH_STATUS_VALIDATED = "VALIDATED"
BATCH_STATUS_FAILED = "FAILED"
BATCH_STATUS_COMMITTED = "COMMITTED"

ROW_SEVERITY_INFO = "INFO"
ROW_SEVERITY_WARN = "WARN"
ROW_SEVERITY_FATAL = "FATAL"

ROW_RESULT_PENDING = "PENDING"
ROW_RESULT_VALID = "VALID"
ROW_RESULT_CREATED = "CREATED"
ROW_RESULT_EXISTING = "EXISTING"
ROW_RESULT_ROLE_GRANTED = "ROLE_GRANTED"
ROW_RESULT_FAILED = "FAILED"


class AdminUserImportBatch(Base):
    """One preview/commit batch for backend account imports."""

    __tablename__ = "admin_user_import_batches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_no: Mapped[str] = mapped_column(String(48), nullable=False, unique=True, index=True)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=BATCH_STATUS_PROCESSING, index=True
    )
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ok_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warn_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fatal_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    existing_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    role_granted_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unchanged_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    operator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    operator_role: Mapped[str | None] = mapped_column(String(128), nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    rows: Mapped[list[AdminUserImportRow]] = relationship(
        "AdminUserImportRow",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AdminUserImportRow(Base):
    """Preview and commit result for a single uploaded account row."""

    __tablename__ = "admin_user_import_rows"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("admin_user_import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_no: Mapped[int] = mapped_column(Integer, nullable=False)
    work_no: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    role_code: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    scope_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    normalized_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    severity: Mapped[str] = mapped_column(String(8), nullable=False, default=ROW_SEVERITY_INFO)
    result: Mapped[str] = mapped_column(String(24), nullable=False, default=ROW_RESULT_PENDING)
    field_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    message: Mapped[str | None] = mapped_column(String(512), nullable=True)

    batch: Mapped[AdminUserImportBatch] = relationship(
        "AdminUserImportBatch", back_populates="rows"
    )

    __table_args__ = (
        Index("ix_admin_user_import_rows_batch_severity", "batch_id", "severity"),
        Index("ix_admin_user_import_rows_batch_result", "batch_id", "result"),
    )
