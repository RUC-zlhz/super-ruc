"""formal proof template engine

Revision ID: 0018_proof_template_engine
Revises: 0017_admin_user_import
Create Date: 2026-05-23
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0018_proof_template_engine"
down_revision: str | None = "0017_admin_user_import"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "proof_templates",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("request_type_code", sa.String(length=64), nullable=False),
        sa.Column("version_label", sa.String(length=32), nullable=False),
        sa.Column("html_template", sa.Text(), nullable=False),
        sa.Column("field_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_proof_templates_code"),
        sa.UniqueConstraint(
            "request_type_code",
            "version_label",
            name="uq_proof_templates_type_version",
        ),
    )
    op.create_index("ix_proof_templates_code", "proof_templates", ["code"])
    op.create_index("ix_proof_templates_request_type_code", "proof_templates", ["request_type_code"])
    op.create_index("ix_proof_templates_is_active", "proof_templates", ["is_active"])
    op.create_index("ix_proof_templates_is_default", "proof_templates", ["is_default"])
    op.create_index(
        "ix_proof_templates_type_active_default",
        "proof_templates",
        ["request_type_code", "is_active", "is_default"],
    )


def downgrade() -> None:
    op.drop_index("ix_proof_templates_type_active_default", table_name="proof_templates")
    op.drop_index("ix_proof_templates_is_default", table_name="proof_templates")
    op.drop_index("ix_proof_templates_is_active", table_name="proof_templates")
    op.drop_index("ix_proof_templates_request_type_code", table_name="proof_templates")
    op.drop_index("ix_proof_templates_code", table_name="proof_templates")
    op.drop_table("proof_templates")
