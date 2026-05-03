"""文件交换模块模型 — FR-009 / FR-015。

两类对象：
A) 批次型导入：
   - ImportBatch: 一次导入批次（主表，含文件元数据、类型、状态、摘要）
   - ImportBatchRow: 按行记录的校验结果（severity/fatal/warn/info）
   - 导入类型 code：STUDENT / TRANSCRIPT / CURRICULUM_MODULE /
                  COURSE_EQUIV / COURSE_OFFERING / CUSTOM

B) 培养方案域：
   - CurriculumPlan: 按 (grade, major) 的培养方案主表
   - CurriculumModule: 方案下的模块（必修/选修/通识 等），及学分要求
   - CourseEquivalence: 课程替代/等价映射（source_course_code → target_course_code）
   - CourseOffering: 学期开课清单
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

# 导入类型
IMPORT_TYPE_STUDENT = "STUDENT"
IMPORT_TYPE_TRANSCRIPT = "TRANSCRIPT"
IMPORT_TYPE_CURRICULUM_MODULE = "CURRICULUM_MODULE"
IMPORT_TYPE_COURSE_EQUIV = "COURSE_EQUIV"
IMPORT_TYPE_COURSE_OFFERING = "COURSE_OFFERING"
IMPORT_TYPE_HONOR = "HONOR"
IMPORT_TYPE_TRANSCRIPT_PDF_REVIEW = "TRANSCRIPT_PDF_REVIEW"
IMPORT_TYPE_CUSTOM = "CUSTOM"

# 批次状态
BATCH_STATUS_PROCESSING = "PROCESSING"
BATCH_STATUS_VALIDATED = "VALIDATED"  # 校验完，等待 commit
BATCH_STATUS_COMMITTED = "COMMITTED"
BATCH_STATUS_FAILED = "FAILED"
BATCH_STATUS_ROLLED_BACK = "ROLLED_BACK"

# 行严重级
ROW_SEVERITY_INFO = "INFO"
ROW_SEVERITY_WARN = "WARN"
ROW_SEVERITY_FATAL = "FATAL"

# 行结果
ROW_RESULT_OK = "OK"
ROW_RESULT_SKIPPED = "SKIPPED"
ROW_RESULT_FAILED = "FAILED"


class ImportBatch(Base):
    """导入批次（主表）。"""

    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_no: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    import_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    object_bucket: Mapped[str | None] = mapped_column(String(64), nullable=True)
    object_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)

    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ok_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warn_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fatal_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=BATCH_STATUS_PROCESSING, index=True
    )
    summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    operator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    operator_role: Mapped[str | None] = mapped_column(String(64), nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    rows: Mapped[list[ImportBatchRow]] = relationship(
        "ImportBatchRow",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ImportBatchRow(Base):
    """导入批次的单行记录（含校验结果）。"""

    __tablename__ = "import_batch_rows"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    row_no: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    severity: Mapped[str] = mapped_column(String(8), nullable=False, default=ROW_SEVERITY_INFO)
    result: Mapped[str] = mapped_column(String(16), nullable=False, default=ROW_RESULT_OK)
    field_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    message: Mapped[str | None] = mapped_column(String(512), nullable=True)

    batch: Mapped[ImportBatch] = relationship("ImportBatch", back_populates="rows")

    __table_args__ = (
        Index("ix_import_batch_rows_batch_severity", "batch_id", "severity"),
    )


# ============================================================
# B. 培养方案域（FR-015）
# ============================================================
class CurriculumPlan(Base):
    """培养方案主表。按 (grade_code, major_code) 唯一。"""

    __tablename__ = "curriculum_plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    grade_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    major_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    plan_name: Mapped[str] = mapped_column(String(256), nullable=False)
    version_label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    total_credits_required: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    modules: Mapped[list[CurriculumModule]] = relationship(
        "CurriculumModule",
        back_populates="plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("grade_code", "major_code", "version_label",
                         name="uq_curriculum_plans_grade_major_ver"),
    )


class CurriculumModule(Base):
    """培养方案下的模块（必修/限选/通识 等）。"""

    __tablename__ = "curriculum_modules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("curriculum_plans.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    module_code: Mapped[str] = mapped_column(String(64), nullable=False)
    module_name: Mapped[str] = mapped_column(String(128), nullable=False)
    module_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="REQUIRED/ELECTIVE/GENERAL/PRACTICE/OTHER",
    )
    credits_required: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    courses: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="允许的课程清单：[{code, name, credits}]"
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    plan: Mapped[CurriculumPlan] = relationship("CurriculumPlan", back_populates="modules")

    __table_args__ = (
        UniqueConstraint("plan_id", "module_code", name="uq_curriculum_modules_plan_code"),
    )


class CourseEquivalence(Base):
    """课程替代/等价映射。source 课程可由 target 课程替代。"""

    __tablename__ = "course_equivalences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    grade_code: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    major_code: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    source_course_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_course_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    target_course_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_course_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ratio: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False, default=1.0)
    note: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_course_equivalences_grade_major", "grade_code", "major_code"),
    )


class CourseOffering(Base):
    """学期开课清单。用于课程类型/可修读建议。"""

    __tablename__ = "course_offerings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    term_code: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, comment="如 2026-SPRING"
    )
    course_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    course_name: Mapped[str] = mapped_column(String(128), nullable=False)
    credits: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False, default=0)
    course_type: Mapped[str | None] = mapped_column(
        String(32), nullable=True,
        comment="REQUIRED/ELECTIVE/GENERAL/PRACTICE/OTHER",
    )
    major_codes: Mapped[str | None] = mapped_column(
        String(256), nullable=True, comment="适用专业 code 逗号分隔；NULL 表示通识全院"
    )
    grade_codes: Mapped[str | None] = mapped_column(String(64), nullable=True)
    teacher: Mapped[str | None] = mapped_column(String(128), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("term_code", "course_code", name="uq_course_offerings_term_course"),
    )


# ============================================================
# C. 学生成绩（供 FR-014 学业缺口展示）
# ============================================================
class StudentCourseRecord(Base):
    """学生选课/成绩记录。由 TRANSCRIPT 导入维护。"""

    __tablename__ = "student_course_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    term_code: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    course_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    course_name: Mapped[str] = mapped_column(String(128), nullable=False)
    credits: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False, default=0)
    course_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    grade_letter: Mapped[str | None] = mapped_column(String(4), nullable=True)
    pass_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    note: Mapped[str | None] = mapped_column(String(256), nullable=True)
    imported_batch_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_code", "term_code",
            name="uq_student_course_records_student_course_term",
        ),
    )
