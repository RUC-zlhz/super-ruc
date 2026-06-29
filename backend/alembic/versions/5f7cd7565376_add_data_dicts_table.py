"""add data_dicts table

Revision ID: 5f7cd7565376
Revises: 0022_template_tags
Create Date: 2026-06-29 21:48:44.151563

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '5f7cd7565376'
down_revision: Union[str, None] = '0022_template_tags'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'data_dicts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('dict_type', sa.String(length=64), nullable=False, comment='字典类型，如 student_gender / student_grade / political_status'),
        sa.Column('label', sa.String(length=128), nullable=False, comment='显示文本'),
        sa.Column('value', sa.String(length=128), nullable=False, comment='存储值'),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_data_dicts')),
        sa.UniqueConstraint('dict_type', 'value', name='uq_data_dicts_type_value'),
    )
    op.create_index(op.f('ix_data_dicts_dict_type'), 'data_dicts', ['dict_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_data_dicts_dict_type'), table_name='data_dicts')
    op.drop_table('data_dicts')
