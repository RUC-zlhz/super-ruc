"""S49 quiz source metadata

Revision ID: 0020_s49_quiz_source
Revises: 0019_honor_display_order
Create Date: 2026-05-26
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0020_s49_quiz_source"
down_revision: str | None = "0019_honor_display_order"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("quiz_questions", sa.Column("source_name", sa.String(length=256), nullable=True))
    op.add_column("quiz_questions", sa.Column("source_url", sa.String(length=1024), nullable=True))
    op.add_column(
        "quiz_questions",
        sa.Column("source_official", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("quiz_questions", sa.Column("import_batch_id", sa.BigInteger(), nullable=True))
    op.create_index("ix_quiz_questions_import_batch_id", "quiz_questions", ["import_batch_id"])


def downgrade() -> None:
    op.drop_index("ix_quiz_questions_import_batch_id", table_name="quiz_questions")
    op.drop_column("quiz_questions", "import_batch_id")
    op.drop_column("quiz_questions", "source_official")
    op.drop_column("quiz_questions", "source_url")
    op.drop_column("quiz_questions", "source_name")
