"""荣誉导入行校验（IMPORT_TYPE_HONOR）。"""
from __future__ import annotations

from datetime import datetime

from app.exchange.validators._common import OK_RESULT, ValidationResult, fatal, require_non_empty

_ALLOWED_LEVELS = {"NATIONAL", "PROVINCIAL", "MINISTERIAL", "SCHOOL"}


def validate_honor_row(row: dict[str, object]) -> ValidationResult:
    for field, label in (
        ("category_code", "类别编码"),
        ("title", "荣誉名称"),
        ("level", "荣誉级别"),
        ("awarded_by", "授予单位"),
        ("announced_at", "公示日期"),
    ):
        err = require_non_empty(row, field, label)
        if err is not None:
            return err

    level = str(row.get("level") or "").strip().upper()
    if level not in _ALLOWED_LEVELS:
        return fatal("level", "荣誉级别仅支持 NATIONAL/PROVINCIAL/MINISTERIAL/SCHOOL")

    announced_at = row.get("announced_at")
    try:
        if announced_at not in (None, ""):
            datetime.strptime(str(announced_at), "%Y-%m-%d")
    except ValueError:
        return fatal("announced_at", "公示日期必须为 YYYY-MM-DD")

    for field_name in ("effective_from", "effective_to"):
        value = row.get(field_name)
        if value in (None, ""):
            continue
        try:
            datetime.strptime(str(value), "%Y-%m-%d")
        except ValueError:
            return fatal(field_name, f"{field_name} 必须为 YYYY-MM-DD")

    student_no = str(row.get("student_no") or "").strip()
    display_name = str(row.get("display_name") or "").strip()
    if not student_no and not display_name:
        return fatal("student_no", "student_no 与 display_name 至少提供一项")
    return OK_RESULT
