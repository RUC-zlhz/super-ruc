"""s75: index student_workflows.status for admin workbench list

审批工作台列表 (list_pending_workflows_admin) 每次按 status='ACTIVE' 过滤；
原 (student_id, template_id) 复合索引无法服务 status-only 过滤，补单列索引。

Revision ID: 0021_s75_sw_status_index
Revises: 0020_s49_quiz_source
Create Date: 2026-06-26
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0021_s75_sw_status_index"
down_revision: str | None = "0020_s49_quiz_source"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_student_workflows_status",
        "student_workflows",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_student_workflows_status",
        table_name="student_workflows",
    )
