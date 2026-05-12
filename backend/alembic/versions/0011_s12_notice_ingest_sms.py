"""s12 notice ingest sources and delivery attempts

Revision ID: 0011_s12_notice_sms
Revises: 0010_audit_role_align
Create Date: 2026-05-11
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011_s12_notice_sms"
down_revision: str | None = "0010_audit_role_align"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notice_sources",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=False),
        sa.Column("category", sa.String(32), nullable=True),
        sa.Column("target_rule", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notice_sources_source_type", "notice_sources", ["source_type"])
    op.create_index("ix_notice_sources_is_active", "notice_sources", ["is_active"])

    op.create_table(
        "notice_ingest_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "source_id",
            sa.BigInteger(),
            sa.ForeignKey("notice_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="SUCCESS"),
        sa.Column("fetched_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(512), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
    )
    op.create_index("ix_notice_ingest_runs_source_id", "notice_ingest_runs", ["source_id"])
    op.create_index("ix_notice_ingest_runs_status", "notice_ingest_runs", ["status"])

    op.create_table(
        "notice_delivery_attempts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "delivery_id",
            sa.BigInteger(),
            sa.ForeignKey("notice_deliveries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("target_handle", sa.String(256), nullable=True),
        sa.Column("provider_message_id", sa.String(128), nullable=True),
        sa.Column("error_code", sa.String(32), nullable=True),
        sa.Column("error_message", sa.String(512), nullable=True),
        sa.Column("receipt_status", sa.String(32), nullable=True),
        sa.Column("receipt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_notice_delivery_attempt_no",
        "notice_delivery_attempts",
        ["delivery_id", "attempt_no"],
    )
    op.create_index("ix_notice_delivery_attempts_delivery_id", "notice_delivery_attempts", ["delivery_id"])
    op.create_index("ix_notice_delivery_attempts_status", "notice_delivery_attempts", ["status"])


def downgrade() -> None:
    op.drop_table("notice_delivery_attempts")
    op.drop_table("notice_ingest_runs")
    op.drop_table("notice_sources")
