"""workflow: party/youth + request pipeline (FR-004~008)

Revision ID: 0003_workflow
Revises: 0002_knowledge
Create Date: 2026-04-15

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_workflow"
down_revision: Union[str, None] = "0002_knowledge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------- workflow_templates --------
    op.create_table(
        "workflow_templates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("version_label", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_workflow_templates_code", "workflow_templates", ["code"])
    op.create_index("ix_workflow_templates_code", "workflow_templates", ["code"])
    op.create_index("ix_workflow_templates_kind", "workflow_templates", ["kind"])

    # -------- workflow_nodes --------
    op.create_table(
        "workflow_nodes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "template_id",
            sa.BigInteger(),
            sa.ForeignKey("workflow_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stage_group", sa.String(32), nullable=True),
        sa.Column("required_task", sa.Text(), nullable=True),
        sa.Column("trigger_rule", sa.String(32), nullable=False, server_default="PREV_DONE"),
        sa.Column("due_rule_days", sa.Integer(), nullable=True),
        sa.Column("reminder_lead_days", sa.Integer(), nullable=True),
        sa.Column("is_terminal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_workflow_nodes_template_code", "workflow_nodes", ["template_id", "code"]
    )
    op.create_index("ix_workflow_nodes_template_id", "workflow_nodes", ["template_id"])
    op.create_index("ix_workflow_nodes_template_sort", "workflow_nodes", ["template_id", "sort_order"])

    # -------- student_workflows --------
    op.create_table(
        "student_workflows",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id",
            sa.BigInteger(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "template_id",
            sa.BigInteger(),
            sa.ForeignKey("workflow_templates.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "current_node_id",
            sa.BigInteger(),
            sa.ForeignKey("workflow_nodes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_student_workflows_student_id", "student_workflows", ["student_id"])
    op.create_index("ix_student_workflows_template_id", "student_workflows", ["template_id"])
    op.create_index(
        "ix_student_workflows_student_template",
        "student_workflows",
        ["student_id", "template_id"],
    )

    # -------- student_workflow_nodes --------
    op.create_table(
        "student_workflow_nodes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "workflow_id",
            sa.BigInteger(),
            sa.ForeignKey("student_workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "node_id",
            sa.BigInteger(),
            sa.ForeignKey("workflow_nodes.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by", sa.BigInteger(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_student_workflow_nodes_pair",
        "student_workflow_nodes",
        ["workflow_id", "node_id"],
    )
    op.create_index("ix_student_workflow_nodes_workflow_id", "student_workflow_nodes", ["workflow_id"])
    op.create_index("ix_student_workflow_nodes_node_id", "student_workflow_nodes", ["node_id"])
    op.create_index("ix_student_workflow_nodes_status", "student_workflow_nodes", ["status"])

    # -------- workflow_reminders --------
    op.create_table(
        "workflow_reminders",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "workflow_node_state_id",
            sa.BigInteger(),
            sa.ForeignKey("student_workflow_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.BigInteger(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reminder_date", sa.Date(), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False, server_default="IN_APP"),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workflow_reminders_student_id", "workflow_reminders", ["student_id"])
    op.create_index("ix_workflow_reminders_state_id", "workflow_reminders", ["workflow_node_state_id"])
    op.create_index("ix_workflow_reminders_date", "workflow_reminders", ["reminder_date"])
    op.create_index("ix_workflow_reminders_status", "workflow_reminders", ["status"])

    # -------- request_types --------
    op.create_table(
        "request_types",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("form_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attachment_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allow_withdraw", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("withdraw_hours_limit", sa.Integer(), nullable=True),
        sa.Column("approver_roles", sa.String(256), nullable=False, server_default="COUNSELOR"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_request_types_code", "request_types", ["code"])
    op.create_index("ix_request_types_code", "request_types", ["code"])

    # seed 常见事务类型
    op.bulk_insert(
        sa.table(
            "request_types",
            sa.column("code", sa.String),
            sa.column("name", sa.String),
            sa.column("category", sa.String),
            sa.column("attachment_required", sa.Boolean),
            sa.column("allow_withdraw", sa.Boolean),
            sa.column("withdraw_hours_limit", sa.Integer),
            sa.column("approver_roles", sa.String),
        ),
        [
            {
                "code": "LEAVE_NORMAL", "name": "普通请假", "category": "LEAVE",
                "attachment_required": False, "allow_withdraw": True,
                "withdraw_hours_limit": 24, "approver_roles": "COUNSELOR,HEAD_TEACHER",
            },
            {
                "code": "LEAVE_SICK", "name": "病假", "category": "LEAVE",
                "attachment_required": True, "allow_withdraw": True,
                "withdraw_hours_limit": 24, "approver_roles": "COUNSELOR,HEAD_TEACHER",
            },
            {
                "code": "CERTIFICATE_IN_SCHOOL", "name": "在读证明", "category": "CERTIFICATE",
                "attachment_required": False, "allow_withdraw": True,
                "withdraw_hours_limit": 48, "approver_roles": "COUNSELOR",
            },
            {
                "code": "STAMP_FORM", "name": "文件盖章", "category": "STAMP",
                "attachment_required": True, "allow_withdraw": True,
                "withdraw_hours_limit": 48, "approver_roles": "COUNSELOR,COLLEGE_LEADER",
            },
            {
                "code": "REG_ACTIVITY", "name": "活动报名", "category": "REGISTRATION",
                "attachment_required": False, "allow_withdraw": True,
                "withdraw_hours_limit": 72, "approver_roles": "COUNSELOR,YOUTH_LEAGUE_TEACHER",
            },
            {
                "code": "MATERIAL_SUBMIT", "name": "材料提交", "category": "MATERIAL",
                "attachment_required": True, "allow_withdraw": True,
                "withdraw_hours_limit": 24, "approver_roles": "COUNSELOR",
            },
        ],
    )

    # -------- requests --------
    op.create_table(
        "requests",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("request_no", sa.String(32), nullable=False),
        sa.Column(
            "type_id",
            sa.BigInteger(),
            sa.ForeignKey("request_types.id"),
            nullable=False,
        ),
        sa.Column("type_code", sa.String(64), nullable=False),
        sa.Column(
            "applicant_user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "applicant_student_id",
            sa.BigInteger(),
            sa.ForeignKey("students.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("form_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("summary", sa.String(512), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", sa.BigInteger(), nullable=True),
        sa.Column("decision_comment", sa.Text(), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_requests_request_no", "requests", ["request_no"])
    op.create_index("ix_requests_request_no", "requests", ["request_no"])
    op.create_index("ix_requests_type_id", "requests", ["type_id"])
    op.create_index("ix_requests_type_code", "requests", ["type_code"])
    op.create_index("ix_requests_applicant_user_id", "requests", ["applicant_user_id"])
    op.create_index("ix_requests_applicant_student_id", "requests", ["applicant_student_id"])
    op.create_index("ix_requests_status", "requests", ["status"])
    op.create_index("ix_requests_status_type", "requests", ["status", "type_code"])
    op.create_index("ix_requests_applicant_status", "requests", ["applicant_user_id", "status"])

    # -------- request_attachments --------
    op.create_table(
        "request_attachments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "request_id",
            sa.BigInteger(),
            sa.ForeignKey("requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(256), nullable=False),
        sa.Column("object_bucket", sa.String(64), nullable=False),
        sa.Column("object_key", sa.String(512), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("uploaded_by", sa.BigInteger(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_request_attachments_request_id", "request_attachments", ["request_id"])

    # -------- request_approval_records --------
    op.create_table(
        "request_approval_records",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "request_id",
            sa.BigInteger(),
            sa.ForeignKey("requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("status_before", sa.String(16), nullable=True),
        sa.Column("status_after", sa.String(16), nullable=True),
        sa.Column("operator_id", sa.BigInteger(), nullable=True),
        sa.Column("operator_role", sa.String(64), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_request_approval_records_request_id", "request_approval_records", ["request_id"])
    op.create_index("ix_request_approval_records_action", "request_approval_records", ["action"])
    op.create_index("ix_request_approval_records_occurred_at", "request_approval_records", ["occurred_at"])


def downgrade() -> None:
    op.drop_table("request_approval_records")
    op.drop_table("request_attachments")
    op.drop_table("requests")
    op.drop_table("request_types")
    op.drop_table("workflow_reminders")
    op.drop_table("student_workflow_nodes")
    op.drop_table("student_workflows")
    op.drop_table("workflow_nodes")
    op.drop_table("workflow_templates")
