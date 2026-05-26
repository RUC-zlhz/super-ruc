"""奖励荣誉展示模型 — FR-017。

- HonorCategory: 荣誉类别字典（如 国家奖学金 / 校优 / 学科竞赛国家级）
- HonorRecord: 荣誉条目主表（绑定学生或集体）。红头文件/证书编号、公示日期、有效期
- HonorRecipient: 获奖者（一条荣誉可有多个获奖学生）
- HonorAuditLog: 归档/撤销留痕
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# 状态常量
HONOR_STATUS_ACTIVE = "ACTIVE"
HONOR_STATUS_ARCHIVED = "ARCHIVED"
HONOR_STATUS_REVOKED = "REVOKED"

# 层级常量（校级及以上：CLASS/COLLEGE 不允许进入展示）
HONOR_LEVEL_NATIONAL = "NATIONAL"
HONOR_LEVEL_PROVINCIAL = "PROVINCIAL"
HONOR_LEVEL_MINISTERIAL = "MINISTERIAL"
HONOR_LEVEL_SCHOOL = "SCHOOL"


class HonorCategory(Base):
    """荣誉类别字典。"""

    __tablename__ = "honor_categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class HonorRecord(Base):
    """荣誉条目主表。

    - 仅收录"校级及以上"正式荣誉（level in NATIONAL/PROVINCIAL/MINISTERIAL/SCHOOL）
    - 个人 / 集体 通过 is_collective 区分；集体条目允许多个 recipients
    """

    __tablename__ = "honor_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    level: Mapped[str] = mapped_column(
        String(16), nullable=False,
        comment="NATIONAL/PROVINCIAL/MINISTERIAL/SCHOOL",
    )
    awarded_by: Mapped[str] = mapped_column(String(256), nullable=False, comment="授予单位")
    document_no: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="红头文件号或证书编号",
    )
    announced_at: Mapped[date] = mapped_column(Date, nullable=False, comment="公示日期")
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_collective: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # 图文展示内容
    summary: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="事迹摘要")
    story_md: Mapped[str | None] = mapped_column(Text, nullable=True, comment="完整事迹 Markdown")
    acceptance_speech: Mapped[str | None] = mapped_column(Text, nullable=True, comment="获奖感言")
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    media: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="其他图文附件列表")

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=HONOR_STATUS_ACTIVE, index=True,
    )
    consent_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="获奖者本人已授权公示（批量导入默认 True，个人录入须勾选）",
    )
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    archive_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    recipients: Mapped[list[HonorRecipient]] = relationship(
        "HonorRecipient",
        back_populates="record",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_honor_records_status_level", "status", "level"),
        Index("ix_honor_records_announced_at", "announced_at"),
    )


class HonorRecipient(Base):
    """获奖者。"""

    __tablename__ = "honor_recipients"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("honor_records.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    student_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    # 冗余字段用于集体荣誉或学生数据缺失时展示
    student_no_snapshot: Mapped[str | None] = mapped_column(String(32), nullable=True)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    major_snapshot: Mapped[str | None] = mapped_column(String(64), nullable=True)
    grade_snapshot: Mapped[str | None] = mapped_column(String(16), nullable=True)
    class_snapshot: Mapped[str | None] = mapped_column(String(32), nullable=True)
    role_in_collective: Mapped[str | None] = mapped_column(String(64), nullable=True)

    record: Mapped[HonorRecord] = relationship("HonorRecord", back_populates="recipients")

    __table_args__ = (
        UniqueConstraint("record_id", "student_id", "display_name",
                         name="uq_honor_recipients_record_student_name"),
    )
