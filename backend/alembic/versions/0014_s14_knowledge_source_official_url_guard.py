"""s14 knowledge source official url guard

Revision ID: 0014_s14_knowledge_source_url_guard
Revises: 0013_s14_auth_token_binding
Create Date: 2026-05-14
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_s14_knowledge_source_url_guard"
down_revision: str | None = "0013_s14_auth_token_binding"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE knowledge_sources
            SET is_official = FALSE
            WHERE is_official = TRUE
              AND (source_url IS NULL OR btrim(source_url) = '')
            """
        )
    )
    op.create_check_constraint(
        "ck_knowledge_sources_official_requires_url",
        "knowledge_sources",
        "is_official = FALSE OR (source_url IS NOT NULL AND btrim(source_url) <> '')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_knowledge_sources_official_requires_url",
        "knowledge_sources",
        type_="check",
    )
