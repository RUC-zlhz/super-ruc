"""notice: notices/tags/batches/deliveries (FR-010/011)

Revision ID: 0004_notice
Revises: 0003_workflow
Create Date: 2026-04-15

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_notice"
down_revision: Union[str, None] = "0003_workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------- notices --------
    op.create_table(
        "notices",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("body_md", sa.Text(), nullable=False),
        sa.Column("summary", sa.String(512), nullable=True),
        sa.Column("category", sa.String(32), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("source_type", sa.String(16), nullable=False, server_default="MANUAL"),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("target_rule", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("target_summary", sa.String(256), nullable=True),
        sa.Column("channels", sa.String(64), nullable=False, server_default="IN_APP"),
        sa.Column("effective_start", sa.Date(), nullable=True),
        sa.Column("effective_end", sa.Date(), nullable=True),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_by", sa.BigInteger(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by", sa.BigInteger(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notices_status", "notices", ["status"])
    op.create_index("ix_notices_category", "notices", ["category"])

    # -------- notice_tags --------
    op.create_table(
        "notice_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "notice_id",
            sa.BigInteger(),
            sa.ForeignKey("notices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tag", sa.String(64), nullable=False),
    )
    op.create_unique_constraint("uq_notice_tags_notice_tag", "notice_tags", ["notice_id", "tag"])
    op.create_index("ix_notice_tags_notice_id", "notice_tags", ["notice_id"])
    op.create_index("ix_notice_tags_tag", "notice_tags", ["tag"])

    # -------- notice_delivery_batches --------
    op.create_table(
        "notice_delivery_batches",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "notice_id",
            sa.BigInteger(),
            sa.ForeignKey("notices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("batch_no", sa.String(32), nullable=False),
        sa.Column("channels", sa.String(64), nullable=False),
        sa.Column("target_rule_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("target_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="PROCESSING"),
        sa.Column("note", sa.String(512), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_notice_delivery_batches_batch_no", "notice_delivery_batches", ["batch_no"]
    )
    op.create_index("ix_notice_delivery_batches_notice_id", "notice_delivery_batches", ["notice_id"])
    op.create_index("ix_notice_delivery_batches_batch_no", "notice_delivery_batches", ["batch_no"])

    # -------- notice_deliveries --------
    op.create_table(
        "notice_deliveries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "batch_id",
            sa.BigInteger(),
            sa.ForeignKey("notice_delivery_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "notice_id",
            sa.BigInteger(),
            sa.ForeignKey("notices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.BigInteger(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("target_handle", sa.String(256), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(32), nullable=True),
        sa.Column("error_message", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_notice_deliveries_batch_student_channel",
        "notice_deliveries",
        ["batch_id", "student_id", "channel"],
    )
    op.create_index("ix_notice_deliveries_batch_id", "notice_deliveries", ["batch_id"])
    op.create_index("ix_notice_deliveries_notice_id", "notice_deliveries", ["notice_id"])
    op.create_index("ix_notice_deliveries_student_id", "notice_deliveries", ["student_id"])
    op.create_index("ix_notice_deliveries_user_id", "notice_deliveries", ["user_id"])
    op.create_index("ix_notice_deliveries_channel", "notice_deliveries", ["channel"])
    op.create_index("ix_notice_deliveries_status", "notice_deliveries", ["status"])
    op.create_index("ix_notice_deliveries_notice_student", "notice_deliveries", ["notice_id", "student_id"])


def downgrade() -> None:
    op.drop_table("notice_deliveries")
    op.drop_table("notice_delivery_batches")
    op.drop_table("notice_tags")
    op.drop_table("notices")
