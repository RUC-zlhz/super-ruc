"""admin user import and must-change-password flag

Revision ID: 0017_admin_user_import
Revises: 0016_s25_wechat_subscribe
Create Date: 2026-05-18
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0017_admin_user_import"
down_revision: str | None = "0016_s25_wechat_subscribe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_table(
        "admin_user_import_batches",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("batch_no", sa.String(length=48), nullable=False),
        sa.Column("filename", sa.String(length=256), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("ok_rows", sa.Integer(), nullable=False),
        sa.Column("warn_rows", sa.Integer(), nullable=False),
        sa.Column("fatal_rows", sa.Integer(), nullable=False),
        sa.Column("created_rows", sa.Integer(), nullable=False),
        sa.Column("existing_rows", sa.Integer(), nullable=False),
        sa.Column("role_granted_rows", sa.Integer(), nullable=False),
        sa.Column("unchanged_rows", sa.Integer(), nullable=False),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("operator_id", sa.BigInteger(), nullable=True),
        sa.Column("operator_role", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("batch_no", name="uq_admin_user_import_batches_batch_no"),
    )
    op.create_index(
        "ix_admin_user_import_batches_batch_no",
        "admin_user_import_batches",
        ["batch_no"],
    )
    op.create_index(
        "ix_admin_user_import_batches_status",
        "admin_user_import_batches",
        ["status"],
    )

    op.create_table(
        "admin_user_import_rows",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("batch_id", sa.BigInteger(), nullable=False),
        sa.Column("row_no", sa.Integer(), nullable=False),
        sa.Column("work_no", sa.String(length=32), nullable=True),
        sa.Column("role_code", sa.String(length=32), nullable=True),
        sa.Column("scope_code", sa.String(length=64), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("normalized_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("severity", sa.String(length=8), nullable=False),
        sa.Column("result", sa.String(length=24), nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=True),
        sa.Column("message", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["admin_user_import_batches.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_user_import_rows_batch_id",
        "admin_user_import_rows",
        ["batch_id"],
    )
    op.create_index(
        "ix_admin_user_import_rows_role_code",
        "admin_user_import_rows",
        ["role_code"],
    )
    op.create_index(
        "ix_admin_user_import_rows_work_no",
        "admin_user_import_rows",
        ["work_no"],
    )
    op.create_index(
        "ix_admin_user_import_rows_batch_severity",
        "admin_user_import_rows",
        ["batch_id", "severity"],
    )
    op.create_index(
        "ix_admin_user_import_rows_batch_result",
        "admin_user_import_rows",
        ["batch_id", "result"],
    )


def downgrade() -> None:
    op.drop_index("ix_admin_user_import_rows_batch_result", table_name="admin_user_import_rows")
    op.drop_index("ix_admin_user_import_rows_batch_severity", table_name="admin_user_import_rows")
    op.drop_index("ix_admin_user_import_rows_work_no", table_name="admin_user_import_rows")
    op.drop_index("ix_admin_user_import_rows_role_code", table_name="admin_user_import_rows")
    op.drop_index("ix_admin_user_import_rows_batch_id", table_name="admin_user_import_rows")
    op.drop_table("admin_user_import_rows")
    op.drop_index("ix_admin_user_import_batches_status", table_name="admin_user_import_batches")
    op.drop_index("ix_admin_user_import_batches_batch_no", table_name="admin_user_import_batches")
    op.drop_table("admin_user_import_batches")
    op.drop_column("users", "must_change_password")
