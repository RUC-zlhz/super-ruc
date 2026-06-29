"""数据字典模型。

用于管理学生信息表单中的下拉选项（性别、年级、专业、班级、政治面貌等）。
每个 dict_type 对应一组选项列表。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DataDict(Base):
    """数据字典条目。"""

    __tablename__ = "data_dicts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dict_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True,
        comment="字典类型，如 student_gender / student_grade / political_status",
    )
    label: Mapped[str] = mapped_column(String(128), nullable=False, comment="显示文本")
    value: Mapped[str] = mapped_column(String(128), nullable=False, comment="存储值")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("dict_type", "value", name="uq_data_dicts_type_value"),
    )
