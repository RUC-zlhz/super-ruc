"""s23 workflow reminder v1

Revision ID: 0015_s23_workflow_reminder_v1
Revises: 0014_s14_knowledge_source_url_guard
Create Date: 2026-05-17
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015_s23_workflow_reminder_v1"
down_revision: str | None = "0014_s14_knowledge_source_url_guard"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workflow_nodes",
        sa.Column("reminder_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "workflow_nodes",
        sa.Column("reminder_channel", sa.String(length=16), nullable=False, server_default="IN_APP"),
    )
    op.add_column(
        "workflow_nodes",
        sa.Column("repeat_interval_days", sa.Integer(), nullable=True),
    )
    op.add_column(
        "workflow_nodes",
        sa.Column("max_reminders", sa.Integer(), nullable=True, server_default="1"),
    )

    op.create_table(
        "workflow_reminder_runs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False, server_default="IN_APP"),
        sa.Column("trigger_mode", sa.String(length=16), nullable=False, server_default="MANUAL"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="RUNNING"),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cancelled_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(length=512), nullable=True),
        sa.Column("operator_id", sa.BigInteger(), nullable=True),
        sa.Column("operator_role", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workflow_reminder_runs_as_of_date",
        "workflow_reminder_runs",
        ["as_of_date"],
    )
    op.create_index(
        "ix_workflow_reminder_runs_status",
        "workflow_reminder_runs",
        ["status"],
    )

    op.add_column(
        "workflow_reminders",
        sa.Column("run_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "workflow_reminders",
        sa.Column("cancel_reason", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "workflow_reminders",
        sa.Column("error_message", sa.String(length=512), nullable=True),
    )
    op.create_foreign_key(
        "fk_workflow_reminders_run_id_workflow_reminder_runs",
        "workflow_reminders",
        "workflow_reminder_runs",
        ["run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_workflow_reminders_run_id", "workflow_reminders", ["run_id"])
    op.create_unique_constraint(
        "uq_workflow_reminders_state_date_channel",
        "workflow_reminders",
        ["workflow_node_state_id", "reminder_date", "channel"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_workflow_reminders_state_date_channel",
        "workflow_reminders",
        type_="unique",
    )
    op.drop_index("ix_workflow_reminders_run_id", table_name="workflow_reminders")
    op.drop_constraint(
        "fk_workflow_reminders_run_id_workflow_reminder_runs",
        "workflow_reminders",
        type_="foreignkey",
    )
    op.drop_column("workflow_reminders", "error_message")
    op.drop_column("workflow_reminders", "cancel_reason")
    op.drop_column("workflow_reminders", "run_id")

    op.drop_index("ix_workflow_reminder_runs_status", table_name="workflow_reminder_runs")
    op.drop_index("ix_workflow_reminder_runs_as_of_date", table_name="workflow_reminder_runs")
    op.drop_table("workflow_reminder_runs")

    op.drop_column("workflow_nodes", "max_reminders")
    op.drop_column("workflow_nodes", "repeat_interval_days")
    op.drop_column("workflow_nodes", "reminder_channel")
    op.drop_column("workflow_nodes", "reminder_enabled")
