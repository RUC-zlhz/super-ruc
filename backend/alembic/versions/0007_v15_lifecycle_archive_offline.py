"""v1.5 additions: enrollment_status / audit archive / offline-handled

- students.enrollment_status + 相关元数据（FR-018 / 4.2 设计约束）
- audit_log_history 冷备份表（NFR-002）
- OFFLINE_HANDLED 仅为 requests.status 取值扩展，无 DDL；
  同样 requests.decision_comment 被复用作线下联系方式承载，不新增字段。

Revision ID: 0007_v15_lifecycle
Revises: 0006_honor_profile
Create Date: 2026-04-15
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_v15_lifecycle"
down_revision: Union[str, None] = "0006_honor_profile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------
    # students: enrollment_status
    # ------------------------------------------------------
    op.add_column(
        "students",
        sa.Column(
            "enrollment_status",
            sa.String(length=16),
            nullable=False,
            server_default="ACTIVE",
        ),
    )
    op.add_column(
        "students",
        sa.Column(
            "enrollment_status_updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "students",
        sa.Column(
            "enrollment_status_reason",
            sa.String(length=256),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_students_enrollment_status",
        "students",
        ["enrollment_status"],
    )

    # ------------------------------------------------------
    # audit_log_history: 冷备份
    # ------------------------------------------------------
    op.create_table(
        "audit_log_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("entity_code", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("actor_role", sa.String(32), nullable=True),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("result_code", sa.String(16), nullable=False, server_default="SUCCESS"),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(256), nullable=True),
        sa.Column("detail", postgresql.JSONB(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "archived_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_audit_log_history_event_type", "audit_log_history", ["event_type"])
    op.create_index("ix_audit_log_history_entity_code", "audit_log_history", ["entity_code"])
    op.create_index("ix_audit_log_history_actor_user_id", "audit_log_history", ["actor_user_id"])
    op.create_index("ix_audit_log_history_occurred_at", "audit_log_history", ["occurred_at"])
    op.create_index("ix_audit_log_history_archived_at", "audit_log_history", ["archived_at"])
    op.create_index(
        "ix_audit_log_history_entity",
        "audit_log_history",
        ["entity_code", "entity_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_log_history_entity", table_name="audit_log_history")
    op.drop_index("ix_audit_log_history_archived_at", table_name="audit_log_history")
    op.drop_index("ix_audit_log_history_occurred_at", table_name="audit_log_history")
    op.drop_index("ix_audit_log_history_actor_user_id", table_name="audit_log_history")
    op.drop_index("ix_audit_log_history_entity_code", table_name="audit_log_history")
    op.drop_index("ix_audit_log_history_event_type", table_name="audit_log_history")
    op.drop_table("audit_log_history")

    op.drop_index("ix_students_enrollment_status", table_name="students")
    op.drop_column("students", "enrollment_status_reason")
    op.drop_column("students", "enrollment_status_updated_at")
    op.drop_column("students", "enrollment_status")
