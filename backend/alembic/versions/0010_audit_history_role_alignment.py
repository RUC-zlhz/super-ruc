"""add audit history composite indexes and align class monitor role code

Revision ID: 0010_audit_role_align
Revises: 0009_s4b_targeted_indexes
Create Date: 2026-05-06
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_audit_role_align"
down_revision: str | None = "0009_s4b_targeted_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ROLE_CODE_CLASS_MONITOR = "CLASS_MONITOR"
_LEGACY_ROLE_CODE_CLASS_CADRE = "CLASS_CADRE"


def _sync_role_code(*, source_code: str, target_code: str) -> None:
    bind = op.get_bind()
    roles = sa.table(
        "roles",
        sa.column("id", sa.BigInteger()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("level", sa.Integer()),
        sa.column("description", sa.String()),
        sa.column("is_active", sa.Boolean()),
    )
    source_exists = bind.execute(
        sa.select(roles.c.id).where(roles.c.code == source_code)
    ).scalar_one_or_none()
    target_exists = bind.execute(
        sa.select(roles.c.id).where(roles.c.code == target_code)
    ).scalar_one_or_none()

    if target_exists is None:
        if source_exists is not None:
            _ = bind.execute(
                sa.update(roles)
                .where(roles.c.code == source_code)
                .values(code=target_code, name="班长", level=4, description="L4")
            )
        else:
            _ = bind.execute(
                sa.insert(roles).values(
                    code=target_code,
                    name="班长",
                    level=4,
                    description="L4",
                    is_active=True,
                )
            )
    else:
        _ = bind.execute(
            sa.update(roles)
            .where(roles.c.code == target_code)
            .values(name="班长", level=4, description="L4")
        )

    _ = bind.execute(
        sa.text(
            """
            DELETE FROM user_roles
            WHERE role_code = :source_code
              AND EXISTS (
                SELECT 1
                FROM user_roles canonical
                WHERE canonical.user_id = user_roles.user_id
                  AND canonical.role_code = :target_code
                  AND (
                    canonical.scope_code = user_roles.scope_code
                    OR (
                      canonical.scope_code IS NULL
                      AND user_roles.scope_code IS NULL
                    )
                  )
              )
            """
        ),
        {"source_code": source_code, "target_code": target_code},
    )
    _ = bind.execute(
        sa.text(
            """
            UPDATE user_roles
            SET role_code = :target_code
            WHERE role_code = :source_code
            """
        ),
        {"source_code": source_code, "target_code": target_code},
    )

    _ = bind.execute(
        sa.text(
            """
            DELETE FROM role_field_policies
            WHERE role_code = :source_code
              AND EXISTS (
                SELECT 1
                FROM role_field_policies canonical
                WHERE canonical.role_code = :target_code
                  AND canonical.entity_code = role_field_policies.entity_code
                  AND canonical.field_name = role_field_policies.field_name
              )
            """
        ),
        {"source_code": source_code, "target_code": target_code},
    )
    _ = bind.execute(
        sa.text(
            """
            UPDATE role_field_policies
            SET role_code = :target_code
            WHERE role_code = :source_code
            """
        ),
        {"source_code": source_code, "target_code": target_code},
    )

    _ = bind.execute(
        sa.text("DELETE FROM roles WHERE code = :source_code"),
        {"source_code": source_code},
    )


def upgrade() -> None:
    op.create_index(
        "ix_audit_log_history_entity_code_occurred_at",
        "audit_log_history",
        ["entity_code", "occurred_at"],
    )
    op.create_index(
        "ix_audit_log_history_actor_user_id_occurred_at",
        "audit_log_history",
        ["actor_user_id", "occurred_at"],
    )
    _sync_role_code(
        source_code=_LEGACY_ROLE_CODE_CLASS_CADRE,
        target_code=_ROLE_CODE_CLASS_MONITOR,
    )


def downgrade() -> None:
    _sync_role_code(
        source_code=_ROLE_CODE_CLASS_MONITOR,
        target_code=_LEGACY_ROLE_CODE_CLASS_CADRE,
    )
    op.drop_index(
        "ix_audit_log_history_actor_user_id_occurred_at",
        table_name="audit_log_history",
    )
    op.drop_index(
        "ix_audit_log_history_entity_code_occurred_at",
        table_name="audit_log_history",
    )
