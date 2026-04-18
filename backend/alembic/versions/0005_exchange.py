"""exchange: import batches + curriculum domain (FR-009/015)

Revision ID: 0005_exchange
Revises: 0004_notice
Create Date: 2026-04-15

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_exchange"
down_revision: Union[str, None] = "0004_notice"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------- import_batches --------
    op.create_table(
        "import_batches",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("batch_no", sa.String(32), nullable=False),
        sa.Column("import_type", sa.String(32), nullable=False),
        sa.Column("filename", sa.String(256), nullable=False),
        sa.Column("object_bucket", sa.String(64), nullable=True),
        sa.Column("object_key", sa.String(512), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ok_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warn_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fatal_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="PROCESSING"),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("note", sa.String(512), nullable=True),
        sa.Column("operator_id", sa.BigInteger(), nullable=True),
        sa.Column("operator_role", sa.String(64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_import_batches_batch_no", "import_batches", ["batch_no"])
    op.create_index("ix_import_batches_batch_no", "import_batches", ["batch_no"])
    op.create_index("ix_import_batches_import_type", "import_batches", ["import_type"])
    op.create_index("ix_import_batches_status", "import_batches", ["status"])

    # -------- import_batch_rows --------
    op.create_table(
        "import_batch_rows",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "batch_id",
            sa.BigInteger(),
            sa.ForeignKey("import_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("row_no", sa.Integer(), nullable=False),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("severity", sa.String(8), nullable=False, server_default="INFO"),
        sa.Column("result", sa.String(16), nullable=False, server_default="OK"),
        sa.Column("field_name", sa.String(64), nullable=True),
        sa.Column("message", sa.String(512), nullable=True),
    )
    op.create_index("ix_import_batch_rows_batch_id", "import_batch_rows", ["batch_id"])
    op.create_index(
        "ix_import_batch_rows_batch_severity",
        "import_batch_rows",
        ["batch_id", "severity"],
    )

    # -------- curriculum_plans --------
    op.create_table(
        "curriculum_plans",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("grade_code", sa.String(16), nullable=False),
        sa.Column("major_code", sa.String(32), nullable=False),
        sa.Column("plan_name", sa.String(256), nullable=False),
        sa.Column("version_label", sa.String(32), nullable=True),
        sa.Column("total_credits_required", sa.Numeric(6, 2), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_curriculum_plans_grade_major_ver", "curriculum_plans",
        ["grade_code", "major_code", "version_label"],
    )
    op.create_index("ix_curriculum_plans_grade_code", "curriculum_plans", ["grade_code"])
    op.create_index("ix_curriculum_plans_major_code", "curriculum_plans", ["major_code"])

    # -------- curriculum_modules --------
    op.create_table(
        "curriculum_modules",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "plan_id",
            sa.BigInteger(),
            sa.ForeignKey("curriculum_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("module_code", sa.String(64), nullable=False),
        sa.Column("module_name", sa.String(128), nullable=False),
        sa.Column("module_type", sa.String(32), nullable=False),
        sa.Column("credits_required", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("courses", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_unique_constraint(
        "uq_curriculum_modules_plan_code", "curriculum_modules",
        ["plan_id", "module_code"],
    )
    op.create_index("ix_curriculum_modules_plan_id", "curriculum_modules", ["plan_id"])

    # -------- course_equivalences --------
    op.create_table(
        "course_equivalences",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("grade_code", sa.String(16), nullable=True),
        sa.Column("major_code", sa.String(32), nullable=True),
        sa.Column("source_course_code", sa.String(64), nullable=False),
        sa.Column("source_course_name", sa.String(128), nullable=True),
        sa.Column("target_course_code", sa.String(64), nullable=False),
        sa.Column("target_course_name", sa.String(128), nullable=True),
        sa.Column("ratio", sa.Numeric(4, 2), nullable=False, server_default="1.0"),
        sa.Column("note", sa.String(256), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_course_equivalences_grade_code", "course_equivalences", ["grade_code"])
    op.create_index("ix_course_equivalences_major_code", "course_equivalences", ["major_code"])
    op.create_index("ix_course_equivalences_source_course_code", "course_equivalences", ["source_course_code"])
    op.create_index("ix_course_equivalences_target_course_code", "course_equivalences", ["target_course_code"])
    op.create_index("ix_course_equivalences_grade_major", "course_equivalences", ["grade_code", "major_code"])

    # -------- course_offerings --------
    op.create_table(
        "course_offerings",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("term_code", sa.String(16), nullable=False),
        sa.Column("course_code", sa.String(64), nullable=False),
        sa.Column("course_name", sa.String(128), nullable=False),
        sa.Column("credits", sa.Numeric(4, 2), nullable=False, server_default="0"),
        sa.Column("course_type", sa.String(32), nullable=True),
        sa.Column("major_codes", sa.String(256), nullable=True),
        sa.Column("grade_codes", sa.String(64), nullable=True),
        sa.Column("teacher", sa.String(128), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(256), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_course_offerings_term_course", "course_offerings",
        ["term_code", "course_code"],
    )
    op.create_index("ix_course_offerings_term_code", "course_offerings", ["term_code"])
    op.create_index("ix_course_offerings_course_code", "course_offerings", ["course_code"])

    # -------- student_course_records --------
    op.create_table(
        "student_course_records",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id",
            sa.BigInteger(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("term_code", sa.String(16), nullable=True),
        sa.Column("course_code", sa.String(64), nullable=False),
        sa.Column("course_name", sa.String(128), nullable=False),
        sa.Column("credits", sa.Numeric(4, 2), nullable=False, server_default="0"),
        sa.Column("course_type", sa.String(32), nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("grade_letter", sa.String(4), nullable=True),
        sa.Column("pass_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("note", sa.String(256), nullable=True),
        sa.Column(
            "imported_batch_id",
            sa.BigInteger(),
            sa.ForeignKey("import_batches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_student_course_records_student_course_term", "student_course_records",
        ["student_id", "course_code", "term_code"],
    )
    op.create_index("ix_student_course_records_student_id", "student_course_records", ["student_id"])
    op.create_index("ix_student_course_records_term_code", "student_course_records", ["term_code"])
    op.create_index("ix_student_course_records_course_code", "student_course_records", ["course_code"])


def downgrade() -> None:
    op.drop_table("student_course_records")
    op.drop_table("course_offerings")
    op.drop_table("course_equivalences")
    op.drop_table("curriculum_modules")
    op.drop_table("curriculum_plans")
    op.drop_table("import_batch_rows")
    op.drop_table("import_batches")
