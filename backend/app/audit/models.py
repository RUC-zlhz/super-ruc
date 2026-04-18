"""审计模块 ORM 模型 — FR-012, FR-013。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """操作审计日志（FR-013）。

    记录审批、导出、权限变更、敏感字段读取等关键操作。
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    actor_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    actor_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    result_code: Mapped[str] = mapped_column(String(16), nullable=False, default="SUCCESS")
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(256), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_code", "entity_id"),
    )


class AuditLogHistory(Base):
    """审计日志冷备份表（v1.5 / NFR-002）。

    超过留存期（默认 1 学期）的日志由定时任务从 `audit_logs`
    搬迁到本表，避免主表膨胀影响查询性能。
    结构与 AuditLog 保持一致，保留原 id 以便可追溯。
    """

    __tablename__ = "audit_log_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    actor_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    actor_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    result_code: Mapped[str] = mapped_column(String(16), nullable=False, default="SUCCESS")
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(256), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    __table_args__ = (
        Index("ix_audit_log_history_entity", "entity_code", "entity_id"),
    )


class RoleFieldPolicy(Base):
    """角色—字段权限策略（FR-012）。

    控制某角色对某实体字段的 read/write 权限。一期作为配置化约束，
    运行时由 service 层查询并执行脱敏/只读。
    """

    __tablename__ = "role_field_policies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    entity_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    can_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_write: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mask_strategy: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="none|partial|full"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "uq_role_field_policies_role_entity_field",
            "role_code",
            "entity_code",
            "field_name",
            unique=True,
        ),
    )
