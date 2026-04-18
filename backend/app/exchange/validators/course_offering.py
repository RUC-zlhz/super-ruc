"""开课信息行校验（IMPORT_TYPE_COURSE_OFFERING）。"""
from __future__ import annotations

from typing import Any

from app.exchange.validators._common import OK_RESULT, ValidationResult, require_non_empty


def validate_course_offering_row(row: dict[str, Any]) -> ValidationResult:
    for field in ("term_code", "course_code", "course_name"):
        err = require_non_empty(row, field)
        if err is not None:
            return err
    return OK_RESULT
