"""targeted indexes for S4B list/report hotspots

Revision ID: 0009_s4b_targeted_indexes
Revises: 0008_quiz
Create Date: 2026-04-19
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0009_s4b_targeted_indexes"
down_revision: str | None = "0008_quiz"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # audit 日志列表：按实体 / 操作者过滤后再按 occurred_at 排序
    op.create_index(
        "ix_audit_logs_entity_code_occurred_at",
        "audit_logs",
        ["entity_code", "occurred_at"],
    )
    op.create_index(
        "ix_audit_logs_actor_user_id_occurred_at",
        "audit_logs",
        ["actor_user_id", "occurred_at"],
    )

    # 申请列表：管理员工作台按状态 + 提交时间排序；学生侧按申请人 + 更新时间排序
    op.create_index(
        "ix_requests_status_submitted_at_id",
        "requests",
        ["status", "submitted_at", "id"],
    )
    op.create_index(
        "ix_requests_applicant_user_id_updated_at",
        "requests",
        ["applicant_user_id", "updated_at"],
    )

    # 流程工作台：ACTIVE 列表按主键分页
    op.create_index(
        "ix_student_workflows_status_id",
        "student_workflows",
        ["status", "id"],
    )

    # 通知批次 / 收件箱：按 notice 查看批次，按 student + channel + read_at 查看收件箱
    op.create_index(
        "ix_notice_delivery_batches_notice_id_started_at",
        "notice_delivery_batches",
        ["notice_id", "started_at"],
    )
    op.create_index(
        "ix_notice_deliveries_student_id_channel_read_at",
        "notice_deliveries",
        ["student_id", "channel", "read_at"],
    )

    # 导入批次列表：按状态 / 类型过滤后按 id 分页
    op.create_index(
        "ix_import_batches_status_import_type_id",
        "import_batches",
        ["status", "import_type", "id"],
    )

    # 报表 / 学生筛选：学生聚合列表与学业缺口明细
    op.create_index(
        "ix_students_grade_major_student_no_id",
        "students",
        ["grade_code", "major_code", "student_no", "id"],
    )
    op.create_index(
        "ix_student_course_records_student_pass_term",
        "student_course_records",
        ["student_id", "pass_flag", "term_code"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_student_course_records_student_pass_term",
        table_name="student_course_records",
    )
    op.drop_index(
        "ix_students_grade_major_student_no_id",
        table_name="students",
    )
    op.drop_index(
        "ix_import_batches_status_import_type_id",
        table_name="import_batches",
    )
    op.drop_index(
        "ix_notice_deliveries_student_id_channel_read_at",
        table_name="notice_deliveries",
    )
    op.drop_index(
        "ix_notice_delivery_batches_notice_id_started_at",
        table_name="notice_delivery_batches",
    )
    op.drop_index(
        "ix_student_workflows_status_id",
        table_name="student_workflows",
    )
    op.drop_index(
        "ix_requests_applicant_user_id_updated_at",
        table_name="requests",
    )
    op.drop_index(
        "ix_requests_status_submitted_at_id",
        table_name="requests",
    )
    op.drop_index(
        "ix_audit_logs_actor_user_id_occurred_at",
        table_name="audit_logs",
    )
    op.drop_index(
        "ix_audit_logs_entity_code_occurred_at",
        table_name="audit_logs",
    )
