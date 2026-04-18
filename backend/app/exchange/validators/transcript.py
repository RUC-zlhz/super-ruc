"""成绩/课程记录行校验（IMPORT_TYPE_TRANSCRIPT）。"""
from __future__ import annotations

from typing import Any

from app.exchange.validators._common import (
    OK_RESULT,
    ValidationResult,
    fatal,
    require_non_empty,
)


def validate_transcript_row(row: dict[str, Any]) -> ValidationResult:
    for field, label in (("student_no", "学号"), ("course_code", "课程代码")):
        err = require_non_empty(row, field, label)
        if err is not None:
            return err
    try:
        credits = float(row.get("credits") or 0)
    except (TypeError, ValueError):
        return fatal("credits", "学分格式错误")
    if credits < 0:
        return fatal("credits", "学分必须 ≥ 0")
    return OK_RESULT
