"""honor + profile: FR-017 / FR-018

Revision ID: 0006_honor_profile
Revises: 0005_exchange
Create Date: 2026-04-15

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_honor_profile"
down_revision: Union[str, None] = "0005_exchange"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==================================================
    # honor
    # ==================================================
    op.create_table(
        "honor_categories",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("description", sa.String(256), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_unique_constraint("uq_honor_categories_code", "honor_categories", ["code"])
    op.create_index("ix_honor_categories_code", "honor_categories", ["code"])

    op.create_table(
        "honor_records",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("category_code", sa.String(32), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("level", sa.String(16), nullable=False),
        sa.Column("awarded_by", sa.String(256), nullable=False),
        sa.Column("document_no", sa.String(128), nullable=True),
        sa.Column("announced_at", sa.Date(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_collective", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("summary", sa.String(512), nullable=True),
        sa.Column("story_md", sa.Text(), nullable=True),
        sa.Column("acceptance_speech", sa.Text(), nullable=True),
        sa.Column("cover_image_url", sa.String(512), nullable=True),
        sa.Column("media", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("consent_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by", sa.BigInteger(), nullable=True),
        sa.Column("archive_reason", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_honor_records_category_code", "honor_records", ["category_code"])
    op.create_index("ix_honor_records_status", "honor_records", ["status"])
    op.create_index("ix_honor_records_status_level", "honor_records", ["status", "level"])
    op.create_index("ix_honor_records_announced_at", "honor_records", ["announced_at"])

    op.create_table(
        "honor_recipients",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "record_id",
            sa.BigInteger(),
            sa.ForeignKey("honor_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.BigInteger(),
            sa.ForeignKey("students.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("student_no_snapshot", sa.String(32), nullable=True),
        sa.Column("display_name", sa.String(64), nullable=False),
        sa.Column("major_snapshot", sa.String(64), nullable=True),
        sa.Column("grade_snapshot", sa.String(16), nullable=True),
        sa.Column("class_snapshot", sa.String(32), nullable=True),
        sa.Column("role_in_collective", sa.String(64), nullable=True),
    )
    op.create_unique_constraint(
        "uq_honor_recipients_record_student_name",
        "honor_recipients", ["record_id", "student_id", "display_name"],
    )
    op.create_index("ix_honor_recipients_record_id", "honor_recipients", ["record_id"])
    op.create_index("ix_honor_recipients_student_id", "honor_recipients", ["student_id"])

    # ==================================================
    # profile
    # ==================================================
    op.create_table(
        "profile_facts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id",
            sa.BigInteger(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fact_type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("role_in_activity", sa.String(64), nullable=True),
        sa.Column("started_on", sa.Date(), nullable=True),
        sa.Column("ended_on", sa.Date(), nullable=True),
        sa.Column("hours", sa.Numeric(8, 2), nullable=True),
        sa.Column("rank_label", sa.String(32), nullable=True),
        sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="TEACHER_ENTRY"),
        sa.Column("source_ref", sa.String(256), nullable=True),
        sa.Column("approval_status", sa.String(16), nullable=False, server_default="APPROVED"),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("approved_by", sa.BigInteger(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_profile_facts_student_id", "profile_facts", ["student_id"])
    op.create_index("ix_profile_facts_fact_type", "profile_facts", ["fact_type"])
    op.create_index("ix_profile_facts_student_type", "profile_facts", ["student_id", "fact_type"])
    op.create_index("ix_profile_facts_approval", "profile_facts", ["approval_status"])

    op.create_table(
        "profile_corrections",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id",
            sa.BigInteger(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fact_id",
            sa.BigInteger(),
            sa.ForeignKey("profile_facts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("field_name", sa.String(64), nullable=False),
        sa.Column("current_value", sa.Text(), nullable=True),
        sa.Column("proposed_value", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("handled_by", sa.BigInteger(), nullable=True),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("handler_comment", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_profile_corrections_student_id", "profile_corrections", ["student_id"])
    op.create_index("ix_profile_corrections_fact_id", "profile_corrections", ["fact_id"])
    op.create_index("ix_profile_corrections_status", "profile_corrections", ["status"])


def downgrade() -> None:
    op.drop_table("profile_corrections")
    op.drop_table("profile_facts")
    op.drop_table("honor_recipients")
    op.drop_table("honor_records")
    op.drop_table("honor_categories")
