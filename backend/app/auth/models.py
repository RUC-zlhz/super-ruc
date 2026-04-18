"""身份、角色、学生主档模型。

- users: 微信 openid 登录主档
- students: 学生主档（Excel 导入维护，C-02）
- roles / user_roles: 角色关联
- 敏感字段后缀 `_enc`（C-04）
- enrollment_status: 学籍生命周期状态（v1.5 新增），非 ACTIVE 账号降级为历史归档
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# v1.5 学籍生命周期状态（FR-018 / 4.2 设计约束）
ENROLLMENT_ACTIVE = "ACTIVE"          # 在读
ENROLLMENT_SUSPENDED = "SUSPENDED"    # 休学
ENROLLMENT_TRANSFERRED = "TRANSFERRED"  # 转出
ENROLLMENT_GRADUATED = "GRADUATED"    # 毕业
ENROLLMENT_ARCHIVED = "ARCHIVED"      # 归档（通用降级标记）

ENROLLMENT_ACTIVE_SET = {ENROLLMENT_ACTIVE}
ENROLLMENT_READ_ONLY_SET = {
    ENROLLMENT_SUSPENDED,
    ENROLLMENT_TRANSFERRED,
    ENROLLMENT_GRADUATED,
    ENROLLMENT_ARCHIVED,
}


class User(Base):
    """系统用户，微信 openid 为首要标识。教师/学生均使用该表。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    openid: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    unionid: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    # 教师账号可用 work_no 作为备用登录标识；学生主要走 openid+student_no 绑定
    work_no: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    display_name: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    phone_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 学生绑定：一个 user 最多关联一个 student。教师类 user 则为 NULL。
    student_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["Student | None"] = relationship(
        "Student", foreign_keys=[student_id], lazy="joined"
    )
    roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )


class Role(Base):
    """角色字典。L1~L5 对应五级权限层级。"""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=5, comment="1=超管,5=学生")
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UserRole(Base):
    """User ↔ Role 多对多；可携带 scope_code 限定范围（如班级、专业）。"""

    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    scope_code: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="班级/专业/年级代码，空表示全局"
    )
    granted_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship("User", back_populates="roles")

    __table_args__ = (
        UniqueConstraint("user_id", "role_code", "scope_code", name="uq_user_roles_user_role_scope"),
    )


class Student(Base):
    """学生主档（Excel 导入维护）。"""

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_no: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(64), nullable=False)
    # 身份证号加密存储（C-04）
    id_card_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)

    gender: Mapped[str | None] = mapped_column(String(8), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    grade_code: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    major_code: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    class_code: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)

    political_status: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="群众/共青团员/入党积极分子/发展对象/预备党员/中共党员"
    )

    enrollment_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    graduation_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="IN_SCHOOL", comment="IN_SCHOOL/LEAVE/GRADUATED"
    )
    # v1.5：学籍生命周期状态，非 ACTIVE 的账号自动降级为只读，
    # 全局依赖 `require_active_enrollment` 会拦截写操作（FR-018 / 4.2 设计约束）。
    enrollment_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=ENROLLMENT_ACTIVE,
        index=True,
        comment="ACTIVE/SUSPENDED/TRANSFERRED/GRADUATED/ARCHIVED",
    )
    enrollment_status_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    enrollment_status_reason: Mapped[str | None] = mapped_column(
        String(256), nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_students_grade_major_class", "grade_code", "major_code", "class_code"),
    )
