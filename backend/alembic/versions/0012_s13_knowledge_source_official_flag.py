"""s13 knowledge source official flag

Revision ID: 0012_s13_knowledge_source_official
Revises: 0011_s12_notice_sms
Create Date: 2026-05-12
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_s13_knowledge_source_official"
down_revision: str | None = "0011_s12_notice_sms"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "knowledge_sources",
        sa.Column("is_official", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("knowledge_sources", "is_official")
