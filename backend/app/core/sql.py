"""SQL helper functions with better cross-database compatibility."""
from __future__ import annotations

from sqlalchemy.sql.elements import ColumnElement


def order_by_nulls_last_desc(column: ColumnElement):
    """Emulate ``DESC NULLS LAST`` without relying on dialect-specific syntax."""
    return column.is_(None), column.desc()


def order_by_nulls_last_asc(column: ColumnElement):
    """Emulate ``ASC NULLS LAST`` without relying on dialect-specific syntax."""
    return column.is_(None), column.asc()
