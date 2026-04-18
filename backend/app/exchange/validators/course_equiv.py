"""课程等价/替代关系行校验（IMPORT_TYPE_COURSE_EQUIV）。"""
from __future__ import annotations

from typing import Any

from app.exchange.validators._common import OK_RESULT, ValidationResult, require_non_empty


def validate_course_equiv_row(row: dict[str, Any]) -> ValidationResult:
    for field, label in (
        ("source_course_code", "源课程代码"),
        ("target_course_code", "替代课程代码"),
    ):
        err = require_non_empty(row, field, label)
        if err is not None:
            return err
    return OK_RESULT
