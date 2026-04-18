"""学生画像扩展模型 — FR-018。

静态学籍字段在 app.auth.models.Student 维护，不在此重复。
本模块仅存放动态成长字段（科研 / 竞赛 / 社会实践 / 志愿服务 / 干部任职）及
画像纠错申诉记录。
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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# 画像事实类型
PROFILE_FACT_RESEARCH = "RESEARCH"        # 科研项目
PROFILE_FACT_COMPETITION = "COMPETITION"  # 学科竞赛
PROFILE_FACT_PRACTICE = "PRACTICE"        # 社会实践
PROFILE_FACT_VOLUNTEER = "VOLUNTEER"      # 志愿服务
PROFILE_FACT_LEADERSHIP = "LEADERSHIP"    # 学生干部任职
PROFILE_FACT_CUSTOM = "CUSTOM"

# 来源
PROFILE_SOURCE_IMPORT = "IMPORT"
PROFILE_SOURCE_TEACHER_ENTRY = "TEACHER_ENTRY"
PROFILE_SOURCE_STUDENT_SELF = "STUDENT_SELF"
PROFILE_SOURCE_SYSTEM = "SYSTEM"

# 审批状态（用于学生自录/申诉）
PROFILE_APPROVAL_PENDING = "PENDING"
PROFILE_APPROVAL_APPROVED = "APPROVED"
PROFILE_APPROVAL_REJECTED = "REJECTED"


class ProfileFact(Base):
    """学生画像事实表。一条记录 = 一项成长事实。"""

    __tablename__ = "profile_facts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    fact_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 角色在项目中的身份（负责人 / 成员 / 主持人等）
    role_in_activity: Mapped[str | None] = mapped_column(String(64), nullable=True)

    started_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    ended_on: Mapped[date | None] = mapped_column(Date, nullable=True)

    # 数值型可选字段（志愿时长 / 竞赛排名）
    hours: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    rank_label: Mapped[str | None] = mapped_column(
        String(32), nullable=True,
        comment="如 '国家级一等奖' 或 '省部级二等奖'"
    )

    attachments: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="附件/证明链接列表"
    )
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # 治理元数据
    source: Mapped[str] = mapped_column(String(32), nullable=False, default=PROFILE_SOURCE_TEACHER_ENTRY)
    source_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    approval_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=PROFILE_APPROVAL_APPROVED
    )
    # 敏感字段默认隐藏非授权角色；true 表示该条事实含敏感信息
    is_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    approved_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_profile_facts_student_type", "student_id", "fact_type"),
        Index("ix_profile_facts_approval", "approval_status"),
    )


class ProfileCorrection(Base):
    """学生画像纠错申诉。

    场景：学生本人对描述字段提出修改申请；辅导员审批。
    不直接修改事实；由审批人决定是否应用修改。
    """

    __tablename__ = "profile_corrections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    fact_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("profile_facts.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    current_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=PROFILE_APPROVAL_PENDING, index=True
    )
    handled_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    handler_comment: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
