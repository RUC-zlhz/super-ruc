"""理论自测题库模型 — FR-005。

- QuizQuestion: 题目（支持单选 / 多选 / 判断三种题型）
- QuizRecord:   学生作答记录（每道题一条；一次测验通过 batch_id 聚合）

题型约定（`qtype`）：
- SINGLE  单选：options_json 为 [{key,text}...]，correct_key 为单个大写字母
- MULTI   多选：options_json 同上，correct_key 为逗号分隔大写字母（如 "A,C,D"）
- JUDGE   判断：options_json 可空，correct_key 为 "TRUE" 或 "FALSE"

软删除：`is_active=False` 表示停用，历史作答记录仍保留对该题的外键引用。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

QUIZ_TYPE_SINGLE = "SINGLE"
QUIZ_TYPE_MULTI = "MULTI"
QUIZ_TYPE_JUDGE = "JUDGE"
QUIZ_TYPES = (QUIZ_TYPE_SINGLE, QUIZ_TYPE_MULTI, QUIZ_TYPE_JUDGE)

QUIZ_DIFF_EASY = "EASY"
QUIZ_DIFF_MEDIUM = "MEDIUM"
QUIZ_DIFF_HARD = "HARD"
QUIZ_DIFFICULTIES = (QUIZ_DIFF_EASY, QUIZ_DIFF_MEDIUM, QUIZ_DIFF_HARD)


class QuizQuestion(Base):
    """题库条目。"""

    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    qtype: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    options_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    correct_key: Mapped[str] = mapped_column(String(64), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(8), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_quiz_questions_topic_active", "topic", "is_active"),
    )


class QuizRecord(Base):
    """学生作答记录。"""

    __tablename__ = "quiz_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("quiz_questions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    batch_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    answer: Mapped[str] = mapped_column(String(64), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    __table_args__ = (
        Index("ix_quiz_records_student_submitted", "student_id", "submitted_at"),
    )
