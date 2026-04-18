"""学生主档行校验（IMPORT_TYPE_STUDENT）。"""
from __future__ import annotations

from typing import Any

from app.exchange.validators._common import OK_RESULT, ValidationResult, require_non_empty


def validate_student_row(row: dict[str, Any]) -> ValidationResult:
    for field, label in (("student_no", "学号"), ("full_name", "姓名")):
        err = require_non_empty(row, field, label)
        if err is not None:
            return err
    return OK_RESULT
