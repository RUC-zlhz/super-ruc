"""quiz bank: FR-005 理论自测

- quiz_questions: 题库（单选 / 多选 / 判断）
- quiz_records:   学生作答记录

Revision ID: 0008_quiz
Revises: 0007_v15_lifecycle
Create Date: 2026-04-18
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_quiz"
down_revision: Union[str, None] = "0007_v15_lifecycle"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("topic", sa.String(64), nullable=False),
        sa.Column("qtype", sa.String(16), nullable=False),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("options_json", postgresql.JSONB(), nullable=True),
        sa.Column("correct_key", sa.String(64), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(8), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_quiz_questions_topic", "quiz_questions", ["topic"])
    op.create_index("ix_quiz_questions_qtype", "quiz_questions", ["qtype"])
    op.create_index(
        "ix_quiz_questions_topic_active",
        "quiz_questions",
        ["topic", "is_active"],
    )

    op.create_table(
        "quiz_records",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id",
            sa.BigInteger(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.BigInteger(),
            sa.ForeignKey("quiz_questions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("batch_id", sa.String(36), nullable=True),
        sa.Column("answer", sa.String(64), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_quiz_records_student_id", "quiz_records", ["student_id"])
    op.create_index("ix_quiz_records_question_id", "quiz_records", ["question_id"])
    op.create_index("ix_quiz_records_batch_id", "quiz_records", ["batch_id"])
    op.create_index("ix_quiz_records_submitted_at", "quiz_records", ["submitted_at"])
    op.create_index(
        "ix_quiz_records_student_submitted",
        "quiz_records",
        ["student_id", "submitted_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_quiz_records_student_submitted", table_name="quiz_records")
    op.drop_index("ix_quiz_records_submitted_at", table_name="quiz_records")
    op.drop_index("ix_quiz_records_batch_id", table_name="quiz_records")
    op.drop_index("ix_quiz_records_question_id", table_name="quiz_records")
    op.drop_index("ix_quiz_records_student_id", table_name="quiz_records")
    op.drop_table("quiz_records")

    op.drop_index("ix_quiz_questions_topic_active", table_name="quiz_questions")
    op.drop_index("ix_quiz_questions_qtype", table_name="quiz_questions")
    op.drop_index("ix_quiz_questions_topic", table_name="quiz_questions")
    op.drop_table("quiz_questions")
