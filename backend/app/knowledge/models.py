"""知识库模块模型 — FR-001 / FR-002 / FR-003。

核心对象：
- KnowledgeCategory: 分类字典（业务/流程域）
- KnowledgeSource: 权威来源，携带版本与生效日期（FR-002）
- KnowledgeEntry: 知识条目，展示态字段（适用条件 / 所需材料 / 办理步骤）
- KnowledgeEntryTag: 条目标签关联
- KnowledgeRevision: 每次发布/停用的版本快照与操作者（FR-003）
- TemplateAsset: 模板文件（Word/Excel/PDF 均可），MinIO 托管
- KnowledgeEntryTemplate: 条目↔模板的引用关系
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

# 条目状态
ENTRY_STATUS_DRAFT = "DRAFT"
ENTRY_STATUS_PUBLISHED = "PUBLISHED"
ENTRY_STATUS_DEPRECATED = "DEPRECATED"

# 模板状态
TEMPLATE_STATUS_ACTIVE = "ACTIVE"
TEMPLATE_STATUS_DEPRECATED = "DEPRECATED"

# Revision 动作
REVISION_PUBLISH = "PUBLISH"
REVISION_UPDATE = "UPDATE"
REVISION_DEPRECATE = "DEPRECATE"


class KnowledgeCategory(Base):
    """分类字典（扁平结构，可按需扩展 parent_code 形成树）。"""

    __tablename__ = "knowledge_categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    parent_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class KnowledgeSource(Base):
    """权威来源（FR-002）。每个 entry 至少关联一个 source 以呈现版本与链接。"""

    __tablename__ = "knowledge_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(256), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    issuing_org: Mapped[str | None] = mapped_column(String(128), nullable=True)
    version_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class KnowledgeEntry(Base):
    """知识条目主表。body_md 存储 Markdown 正文；其他结构化字段便于按 FR-001 以卡片形式展示。"""

    __tablename__ = "knowledge_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(512), nullable=True)

    category_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    applicable_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_materials: Mapped[str | None] = mapped_column(Text, nullable=True)
    process_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_md: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("knowledge_sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    version_label: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ENTRY_STATUS_DRAFT, index=True
    )
    ambiguity_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="FR-002：标记为模糊/特殊/高风险，前端显示转人工咨询入口",
    )
    manual_consult_hint: Mapped[str | None] = mapped_column(
        String(256), nullable=True, comment="转人工咨询入口提示文案"
    )

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deprecated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    source: Mapped[KnowledgeSource | None] = relationship("KnowledgeSource", lazy="joined")
    tags: Mapped[list["KnowledgeEntryTag"]] = relationship(
        "KnowledgeEntryTag",
        back_populates="entry",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    templates: Mapped[list["KnowledgeEntryTemplate"]] = relationship(
        "KnowledgeEntryTemplate",
        back_populates="entry",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_knowledge_entries_status_category", "status", "category_code"),
    )


class KnowledgeEntryTag(Base):
    """条目标签（扁平字符串）。"""

    __tablename__ = "knowledge_entry_tags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("knowledge_entries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    entry: Mapped[KnowledgeEntry] = relationship("KnowledgeEntry", back_populates="tags")

    __table_args__ = (
        UniqueConstraint("entry_id", "tag", name="uq_knowledge_entry_tags_entry_tag"),
    )


class KnowledgeRevision(Base):
    """知识条目版本快照，用于 FR-003 的"谁发布/停用"追溯。"""

    __tablename__ = "knowledge_revisions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("knowledge_entries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    version_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status_before: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status_after: Mapped[str | None] = mapped_column(String(16), nullable=True)
    snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    operator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    operator_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TemplateAsset(Base):
    """模板文件（Word/Excel/PDF）。MinIO 托管，数据库只存元数据与 object key。"""

    __tablename__ = "template_assets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_name: Mapped[str] = mapped_column(String(256), nullable=False)
    template_type: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="DOCX/XLSX/PDF/OTHER"
    )
    category_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    applicable_scenario: Mapped[str | None] = mapped_column(String(512), nullable=True)
    version_label: Mapped[str | None] = mapped_column(String(64), nullable=True)

    object_bucket: Mapped[str] = mapped_column(String(64), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=TEMPLATE_STATUS_ACTIVE, index=True
    )
    uploaded_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deprecated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class KnowledgeEntryTemplate(Base):
    """知识条目 ↔ 模板文件的引用关系。"""

    __tablename__ = "knowledge_entry_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entry_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("knowledge_entries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("template_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )

    entry: Mapped[KnowledgeEntry] = relationship("KnowledgeEntry", back_populates="templates")
    template: Mapped[TemplateAsset] = relationship("TemplateAsset", lazy="joined")

    __table_args__ = (
        UniqueConstraint("entry_id", "template_id", name="uq_knowledge_entry_templates_pair"),
    )
