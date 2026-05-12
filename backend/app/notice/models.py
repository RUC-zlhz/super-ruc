"""通知模块模型 — FR-010 / FR-011。

核心对象：
- Notice: 通知主表（标题、正文、标签、目标规则、状态）
- NoticeTag: 标签关联（多对多弱关系，直接字符串）
- NoticeDeliveryBatch: 发送批次（一次发送一个批次，可含多通道）
- NoticeDelivery: 每个接收者的投递记录（目标+渠道+状态）
- NoticeRead: 学生端站内已读标记

状态机：
- Notice.status: DRAFT → PUBLISHED → ARCHIVED
- NoticeDelivery.status: PENDING / SENT / FAILED / SKIPPED / READ
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
NOTICE_STATUS_DRAFT = "DRAFT"
NOTICE_STATUS_PUBLISHED = "PUBLISHED"
NOTICE_STATUS_ARCHIVED = "ARCHIVED"

NOTICE_SOURCE_TYPE_URL = "URL"
NOTICE_SOURCE_TYPE_RSS = "RSS"

INGEST_RUN_STATUS_SUCCESS = "SUCCESS"
INGEST_RUN_STATUS_FAILED = "FAILED"
INGEST_RUN_STATUS_PARTIAL = "PARTIAL"

DELIVERY_STATUS_PENDING = "PENDING"
DELIVERY_STATUS_SENT = "SENT"
DELIVERY_STATUS_FAILED = "FAILED"
DELIVERY_STATUS_SKIPPED = "SKIPPED"
DELIVERY_STATUS_READ = "READ"

DELIVERY_ATTEMPT_STATUS_SENT = "SENT"
DELIVERY_ATTEMPT_STATUS_FAILED = "FAILED"
DELIVERY_ATTEMPT_STATUS_SKIPPED = "SKIPPED"

CHANNEL_IN_APP = "IN_APP"
CHANNEL_EMAIL = "EMAIL"
CHANNEL_SMS = "SMS"


class NoticeSource(Base):
    """受控通知抓取来源。

    仅支持管理员配置的公开 URL / RSS；不会接入登录态、公众号或绕过反爬。
    """

    __tablename__ = "notice_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target_rule: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    runs: Mapped[list[NoticeIngestRun]] = relationship(
        "NoticeIngestRun",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class NoticeIngestRun(Base):
    """一次手工触发的公开来源抓取记录。"""

    __tablename__ = "notice_ingest_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("notice_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=INGEST_RUN_STATUS_SUCCESS)
    fetched_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    source: Mapped[NoticeSource] = relationship("NoticeSource", back_populates="runs")


class Notice(Base):
    """通知主表。

    - target_rule: JSON 规则，用于按画像条件筛选目标学生。示例：
        {"grade_codes": ["2023"], "major_codes": ["CS"], "political_status": ["中共党员"]}
    - category: 业务大类，便于前端分类展示
    - is_pinned: 是否置顶展示
    """

    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(512), nullable=True)

    category: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=NOTICE_STATUS_DRAFT, index=True
    )

    source_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="MANUAL",
        comment="MANUAL/INGESTED 受控抓取",
    )
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    target_rule: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    target_summary: Mapped[str | None] = mapped_column(
        String(256), nullable=True, comment="人类可读目标描述，如 2023级计算机专业"
    )

    channels: Mapped[str] = mapped_column(
        String(64), nullable=False, default=CHANNEL_IN_APP,
        comment="逗号分隔：IN_APP,EMAIL,SMS",
    )

    effective_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    tags: Mapped[list[NoticeTag]] = relationship(
        "NoticeTag",
        back_populates="notice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    batches: Mapped[list[NoticeDeliveryBatch]] = relationship(
        "NoticeDeliveryBatch",
        back_populates="notice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class NoticeTag(Base):
    """通知标签（业务维度，区别于知识标签）。"""

    __tablename__ = "notice_tags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    notice_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("notices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    notice: Mapped[Notice] = relationship("Notice", back_populates="tags")

    __table_args__ = (
        UniqueConstraint("notice_id", "tag", name="uq_notice_tags_notice_tag"),
    )


class NoticeDeliveryBatch(Base):
    """发送批次。每次"发送"/"重新发送"创建一个新批次。"""

    __tablename__ = "notice_delivery_batches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    notice_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("notices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    batch_no: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    channels: Mapped[str] = mapped_column(String(64), nullable=False)
    target_rule_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    target_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="PROCESSING",
        comment="PROCESSING/COMPLETED/PARTIAL/FAILED",
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    notice: Mapped[Notice] = relationship("Notice", back_populates="batches")
    deliveries: Mapped[list[NoticeDelivery]] = relationship(
        "NoticeDelivery",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class NoticeDelivery(Base):
    """单条投递记录：一个 target student × 一个 channel。"""

    __tablename__ = "notice_deliveries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("notice_delivery_batches.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    notice_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("notices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    channel: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=DELIVERY_STATUS_PENDING, index=True
    )
    target_handle: Mapped[str | None] = mapped_column(
        String(256), nullable=True, comment="收件人 email/phone 等通道地址，脱敏存储"
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    batch: Mapped[NoticeDeliveryBatch] = relationship(
        "NoticeDeliveryBatch", back_populates="deliveries"
    )
    attempts: Mapped[list[NoticeDeliveryAttempt]] = relationship(
        "NoticeDeliveryAttempt",
        back_populates="delivery",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "batch_id", "student_id", "channel", name="uq_notice_deliveries_batch_student_channel"
        ),
        Index("ix_notice_deliveries_notice_student", "notice_id", "student_id"),
    )


class NoticeDeliveryAttempt(Base):
    """短信等外部通道的单次投递尝试与回执记录。"""

    __tablename__ = "notice_delivery_attempts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("notice_deliveries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    target_handle: Mapped[str | None] = mapped_column(String(256), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    receipt_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    receipt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    delivery: Mapped[NoticeDelivery] = relationship(
        "NoticeDelivery", back_populates="attempts"
    )

    __table_args__ = (
        UniqueConstraint("delivery_id", "attempt_no", name="uq_notice_delivery_attempt_no"),
        Index("ix_notice_delivery_attempts_status", "status"),
    )
