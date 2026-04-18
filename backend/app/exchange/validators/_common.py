"""校验器公用常量与简单工具。"""
from __future__ import annotations

from typing import Any

from app.exchange.models import (
    ROW_RESULT_FAILED,
    ROW_RESULT_OK,
    ROW_SEVERITY_FATAL,
    ROW_SEVERITY_INFO,
)

ValidationResult = tuple[str, str, str | None, str | None]

OK_RESULT: ValidationResult = (ROW_SEVERITY_INFO, ROW_RESULT_OK, None, None)


def fatal(field: str, message: str) -> ValidationResult:
    return (ROW_SEVERITY_FATAL, ROW_RESULT_FAILED, field, message)


def require_non_empty(row: dict[str, Any], field: str, label: str | None = None) -> ValidationResult | None:
    if not row.get(field):
        return fatal(field, f"{label or field} 不能为空")
    return None
