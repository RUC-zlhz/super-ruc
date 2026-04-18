"""initial: auth (users/roles/user_roles/students) + audit (audit_logs/role_field_policies)

Revision ID: 0001_auth_audit
Revises:
Create Date: 2026-04-15

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_auth_audit"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------- students --------
    op.create_table(
        "students",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("student_no", sa.String(32), nullable=False),
        sa.Column("full_name", sa.String(64), nullable=False),
        sa.Column("id_card_enc", sa.Text(), nullable=True),
        sa.Column("phone_enc", sa.Text(), nullable=True),
        sa.Column("email", sa.String(128), nullable=True),
        sa.Column("gender", sa.String(8), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("grade_code", sa.String(16), nullable=True),
        sa.Column("major_code", sa.String(32), nullable=True),
        sa.Column("class_code", sa.String(32), nullable=True),
        sa.Column("political_status", sa.String(32), nullable=True),
        sa.Column("enrollment_year", sa.Integer(), nullable=True),
        sa.Column("expected_graduation_year", sa.Integer(), nullable=True),
        sa.Column("graduation_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(16), nullable=False, server_default="IN_SCHOOL"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_students_student_no", "students", ["student_no"])
    op.create_index("ix_students_student_no", "students", ["student_no"])
    op.create_index("ix_students_grade_code", "students", ["grade_code"])
    op.create_index("ix_students_major_code", "students", ["major_code"])
    op.create_index("ix_students_class_code", "students", ["class_code"])
    op.create_index(
        "ix_students_grade_major_class", "students", ["grade_code", "major_code", "class_code"]
    )

    # -------- users --------
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("openid", sa.String(64), nullable=True),
        sa.Column("unionid", sa.String(64), nullable=True),
        sa.Column("work_no", sa.String(32), nullable=True),
        sa.Column("password_hash", sa.String(128), nullable=True),
        sa.Column("display_name", sa.String(64), nullable=False, server_default=""),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("phone_enc", sa.Text(), nullable=True),
        sa.Column("email", sa.String(128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "student_id",
            sa.BigInteger(),
            sa.ForeignKey("students.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_users_openid", "users", ["openid"])
    op.create_unique_constraint("uq_users_unionid", "users", ["unionid"])
    op.create_unique_constraint("uq_users_work_no", "users", ["work_no"])
    op.create_index("ix_users_openid", "users", ["openid"])
    op.create_index("ix_users_work_no", "users", ["work_no"])
    op.create_index("ix_users_student_id", "users", ["student_id"])

    # -------- roles --------
    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("description", sa.String(256), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_roles_code", "roles", ["code"])
    op.create_index("ix_roles_code", "roles", ["code"])

    # seed 默认角色
    op.bulk_insert(
        sa.table(
            "roles",
            sa.column("code", sa.String),
            sa.column("name", sa.String),
            sa.column("level", sa.Integer),
            sa.column("description", sa.String),
        ),
        [
            {"code": "SUPER_ADMIN", "name": "超级管理员", "level": 1, "description": "L1"},
            {"code": "COLLEGE_LEADER", "name": "学院领导", "level": 2, "description": "L2"},
            {"code": "COUNSELOR", "name": "辅导员", "level": 3, "description": "L3"},
            {"code": "HEAD_TEACHER", "name": "班主任", "level": 3, "description": "L3"},
            {"code": "YOUTH_LEAGUE_TEACHER", "name": "团委老师", "level": 3, "description": "L3"},
            {"code": "PARTY_BUILD_TEACHER", "name": "党建老师", "level": 3, "description": "L3"},
            {"code": "CLASS_CADRE", "name": "班团骨干", "level": 4, "description": "L4"},
            {"code": "STUDENT", "name": "学生", "level": 5, "description": "L5"},
        ],
    )

    # -------- user_roles --------
    op.create_table(
        "user_roles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role_code", sa.String(32), nullable=False),
        sa.Column("scope_code", sa.String(64), nullable=True),
        sa.Column("granted_by", sa.BigInteger(), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_user_roles_user_role_scope", "user_roles", ["user_id", "role_code", "scope_code"]
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_code", "user_roles", ["role_code"])

    # -------- audit_logs --------
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("entity_code", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("actor_role", sa.String(32), nullable=True),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("result_code", sa.String(16), nullable=False, server_default="SUCCESS"),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(256), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_entity_code", "audit_logs", ["entity_code"])
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_occurred_at", "audit_logs", ["occurred_at"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_code", "entity_id"])

    # -------- role_field_policies --------
    op.create_table(
        "role_field_policies",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("role_code", sa.String(32), nullable=False),
        sa.Column("entity_code", sa.String(64), nullable=False),
        sa.Column("field_name", sa.String(64), nullable=False),
        sa.Column("can_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_write", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("mask_strategy", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_role_field_policies_role_code", "role_field_policies", ["role_code"])
    op.create_index("ix_role_field_policies_entity_code", "role_field_policies", ["entity_code"])
    op.create_index(
        "uq_role_field_policies_role_entity_field",
        "role_field_policies",
        ["role_code", "entity_code", "field_name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("role_field_policies")
    op.drop_table("audit_logs")
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("users")
    op.drop_table("students")
