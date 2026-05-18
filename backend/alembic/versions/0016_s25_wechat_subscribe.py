"""s25 wechat subscribe authorizations

Revision ID: 0016_s25_wechat_subscribe
Revises: 0015_s23_workflow_reminder_v1
Create Date: 2026-05-18
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0016_s25_wechat_subscribe"
down_revision: str | None = "0015_s23_workflow_reminder_v1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wechat_subscribe_authorizations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=True),
        sa.Column("openid", sa.String(length=64), nullable=False),
        sa.Column("template_id", sa.String(length=128), nullable=False),
        sa.Column("scene", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "template_id",
            name="uq_wechat_subscribe_auth_user_template",
        ),
    )
    op.create_index(
        "ix_wechat_subscribe_authorizations_openid",
        "wechat_subscribe_authorizations",
        ["openid"],
    )
    op.create_index(
        "ix_wechat_subscribe_authorizations_scene",
        "wechat_subscribe_authorizations",
        ["scene"],
    )
    op.create_index(
        "ix_wechat_subscribe_authorizations_status",
        "wechat_subscribe_authorizations",
        ["status"],
    )
    op.create_index(
        "ix_wechat_subscribe_authorizations_student_id",
        "wechat_subscribe_authorizations",
        ["student_id"],
    )
    op.create_index(
        "ix_wechat_subscribe_authorizations_template_id",
        "wechat_subscribe_authorizations",
        ["template_id"],
    )
    op.create_index(
        "ix_wechat_subscribe_authorizations_user_id",
        "wechat_subscribe_authorizations",
        ["user_id"],
    )
    op.create_index(
        "ix_wechat_subscribe_auth_student_template",
        "wechat_subscribe_authorizations",
        ["student_id", "template_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_wechat_subscribe_auth_student_template",
        table_name="wechat_subscribe_authorizations",
    )
    op.drop_index(
        "ix_wechat_subscribe_authorizations_user_id",
        table_name="wechat_subscribe_authorizations",
    )
    op.drop_index(
        "ix_wechat_subscribe_authorizations_template_id",
        table_name="wechat_subscribe_authorizations",
    )
    op.drop_index(
        "ix_wechat_subscribe_authorizations_student_id",
        table_name="wechat_subscribe_authorizations",
    )
    op.drop_index(
        "ix_wechat_subscribe_authorizations_status",
        table_name="wechat_subscribe_authorizations",
    )
    op.drop_index(
        "ix_wechat_subscribe_authorizations_scene",
        table_name="wechat_subscribe_authorizations",
    )
    op.drop_index(
        "ix_wechat_subscribe_authorizations_openid",
        table_name="wechat_subscribe_authorizations",
    )
    op.drop_table("wechat_subscribe_authorizations")
