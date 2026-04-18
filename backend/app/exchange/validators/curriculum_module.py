"""培养方案模块行校验（IMPORT_TYPE_CURRICULUM_MODULE）。"""
from __future__ import annotations

from typing import Any

from app.exchange.validators._common import OK_RESULT, ValidationResult, require_non_empty


def validate_curriculum_module_row(row: dict[str, Any]) -> ValidationResult:
    for field in ("grade_code", "major_code", "module_code", "module_name"):
        err = require_non_empty(row, field)
        if err is not None:
            return err
    return OK_RESULT
