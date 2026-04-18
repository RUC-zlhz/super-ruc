"""knowledge: categories, sources, entries, tags, revisions, templates

Revision ID: 0002_knowledge
Revises: 0001_auth_audit
Create Date: 2026-04-15

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_knowledge"
down_revision: Union[str, None] = "0001_auth_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------- knowledge_categories --------
    op.create_table(
        "knowledge_categories",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("parent_code", sa.String(64), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_knowledge_categories_code", "knowledge_categories", ["code"])
    op.create_index("ix_knowledge_categories_code", "knowledge_categories", ["code"])
    op.create_index("ix_knowledge_categories_parent_code", "knowledge_categories", ["parent_code"])

    # seed 默认分类
    op.bulk_insert(
        sa.table(
            "knowledge_categories",
            sa.column("code", sa.String),
            sa.column("name", sa.String),
            sa.column("sort_order", sa.Integer),
        ),
        [
            {"code": "LEAVE", "name": "请假", "sort_order": 1},
            {"code": "CERTIFICATE", "name": "证明开具", "sort_order": 2},
            {"code": "STAMP", "name": "盖章", "sort_order": 3},
            {"code": "PARTY", "name": "党建", "sort_order": 4},
            {"code": "YOUTH_LEAGUE", "name": "团建", "sort_order": 5},
            {"code": "ACADEMIC", "name": "学业", "sort_order": 6},
            {"code": "SCHOLARSHIP", "name": "奖助学金", "sort_order": 7},
            {"code": "OTHER", "name": "其他", "sort_order": 99},
        ],
    )

    # -------- knowledge_sources --------
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source_name", sa.String(256), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("issuing_org", sa.String(128), nullable=True),
        sa.Column("version_label", sa.String(64), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # -------- knowledge_entries --------
    op.create_table(
        "knowledge_entries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("summary", sa.String(512), nullable=True),
        sa.Column("category_code", sa.String(64), nullable=True),
        sa.Column("applicable_condition", sa.Text(), nullable=True),
        sa.Column("required_materials", sa.Text(), nullable=True),
        sa.Column("process_steps", sa.Text(), nullable=True),
        sa.Column("body_md", sa.Text(), nullable=True),
        sa.Column(
            "source_id",
            sa.BigInteger(),
            sa.ForeignKey("knowledge_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("version_label", sa.String(64), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("ambiguity_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("manual_consult_hint", sa.String(256), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_by", sa.BigInteger(), nullable=True),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deprecated_by", sa.BigInteger(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_knowledge_entries_slug", "knowledge_entries", ["slug"])
    op.create_index("ix_knowledge_entries_slug", "knowledge_entries", ["slug"])
    op.create_index("ix_knowledge_entries_category_code", "knowledge_entries", ["category_code"])
    op.create_index("ix_knowledge_entries_status", "knowledge_entries", ["status"])
    op.create_index("ix_knowledge_entries_source_id", "knowledge_entries", ["source_id"])
    op.create_index(
        "ix_knowledge_entries_status_category", "knowledge_entries", ["status", "category_code"]
    )

    # -------- knowledge_entry_tags --------
    op.create_table(
        "knowledge_entry_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "entry_id",
            sa.BigInteger(),
            sa.ForeignKey("knowledge_entries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tag", sa.String(64), nullable=False),
    )
    op.create_unique_constraint(
        "uq_knowledge_entry_tags_entry_tag", "knowledge_entry_tags", ["entry_id", "tag"]
    )
    op.create_index("ix_knowledge_entry_tags_entry_id", "knowledge_entry_tags", ["entry_id"])
    op.create_index("ix_knowledge_entry_tags_tag", "knowledge_entry_tags", ["tag"])

    # -------- knowledge_revisions --------
    op.create_table(
        "knowledge_revisions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "entry_id",
            sa.BigInteger(),
            sa.ForeignKey("knowledge_entries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("version_label", sa.String(64), nullable=True),
        sa.Column("status_before", sa.String(16), nullable=True),
        sa.Column("status_after", sa.String(16), nullable=True),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("operator_id", sa.BigInteger(), nullable=True),
        sa.Column("operator_role", sa.String(32), nullable=True),
        sa.Column("note", sa.String(512), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_revisions_entry_id", "knowledge_revisions", ["entry_id"])

    # -------- template_assets --------
    op.create_table(
        "template_assets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("template_name", sa.String(256), nullable=False),
        sa.Column("template_type", sa.String(16), nullable=False),
        sa.Column("category_code", sa.String(64), nullable=True),
        sa.Column("applicable_scenario", sa.String(512), nullable=True),
        sa.Column("version_label", sa.String(64), nullable=True),
        sa.Column("object_bucket", sa.String(64), nullable=False),
        sa.Column("object_key", sa.String(512), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("uploaded_by", sa.BigInteger(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deprecated_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_template_assets_category_code", "template_assets", ["category_code"])
    op.create_index("ix_template_assets_status", "template_assets", ["status"])

    # -------- knowledge_entry_templates --------
    op.create_table(
        "knowledge_entry_templates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "entry_id",
            sa.BigInteger(),
            sa.ForeignKey("knowledge_entries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "template_id",
            sa.BigInteger(),
            sa.ForeignKey("template_assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_knowledge_entry_templates_pair",
        "knowledge_entry_templates",
        ["entry_id", "template_id"],
    )
    op.create_index(
        "ix_knowledge_entry_templates_entry_id", "knowledge_entry_templates", ["entry_id"]
    )
    op.create_index(
        "ix_knowledge_entry_templates_template_id", "knowledge_entry_templates", ["template_id"]
    )


def downgrade() -> None:
    op.drop_table("knowledge_entry_templates")
    op.drop_table("template_assets")
    op.drop_table("knowledge_revisions")
    op.drop_table("knowledge_entry_tags")
    op.drop_table("knowledge_entries")
    op.drop_table("knowledge_sources")
    op.drop_table("knowledge_categories")
