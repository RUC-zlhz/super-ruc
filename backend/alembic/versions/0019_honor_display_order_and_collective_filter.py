"""honor display order and collective filter

Revision ID: 0019_honor_display_order
Revises: 0018_proof_template_engine
Create Date: 2026-05-25
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0019_honor_display_order"
down_revision: str | None = "0018_proof_template_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "honor_records",
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_honor_records_display_order",
        "honor_records",
        ["display_order"],
    )


def downgrade() -> None:
    op.drop_index("ix_honor_records_display_order", table_name="honor_records")
    op.drop_column("honor_records", "display_order")
