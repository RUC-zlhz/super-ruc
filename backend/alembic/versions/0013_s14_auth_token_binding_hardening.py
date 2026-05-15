"""s14 auth token and student binding hardening

Revision ID: 0013_s14_auth_token_binding
Revises: 0012_s13_knowledge_source_official
Create Date: 2026-05-14
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_s14_auth_token_binding"
down_revision: str | None = "0012_s13_knowledge_source_official"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_unique_constraint("uq_users_student_id", "users", ["student_id"])


def downgrade() -> None:
    op.drop_constraint("uq_users_student_id", "users", type_="unique")
    op.drop_column("users", "token_version")
