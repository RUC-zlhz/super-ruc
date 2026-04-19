"""行级校验器注册表。

按 import_type 分派到具体校验函数；从 service.py 独立出来便于单测。

每个校验函数接收一行字典（header → 值），返回
``(severity, result, field_name, message)`` 四元组：

- severity ∈ {INFO, WARN, FATAL}
- result   ∈ {OK, FAILED, SKIPPED}
- field_name / message 可为 None
"""
from __future__ import annotations

from typing import Any, Callable

from app.exchange.models import (
    IMPORT_TYPE_COURSE_EQUIV,
    IMPORT_TYPE_COURSE_OFFERING,
    IMPORT_TYPE_CURRICULUM_MODULE,
    IMPORT_TYPE_HONOR,
    IMPORT_TYPE_STUDENT,
    IMPORT_TYPE_TRANSCRIPT,
)
from app.exchange.validators.course_equiv import validate_course_equiv_row
from app.exchange.validators.course_offering import validate_course_offering_row
from app.exchange.validators.curriculum_module import validate_curriculum_module_row
from app.exchange.validators.honor import validate_honor_row
from app.exchange.validators.students import validate_student_row
from app.exchange.validators.transcript import validate_transcript_row

RowValidator = Callable[
    [dict[str, Any]], tuple[str, str, str | None, str | None]
]

VALIDATORS: dict[str, RowValidator] = {
    IMPORT_TYPE_STUDENT: validate_student_row,
    IMPORT_TYPE_TRANSCRIPT: validate_transcript_row,
    IMPORT_TYPE_CURRICULUM_MODULE: validate_curriculum_module_row,
    IMPORT_TYPE_COURSE_EQUIV: validate_course_equiv_row,
    IMPORT_TYPE_COURSE_OFFERING: validate_course_offering_row,
    IMPORT_TYPE_HONOR: validate_honor_row,
}


def get_validator(import_type: str) -> RowValidator | None:
    return VALIDATORS.get(import_type)


__all__ = [
    "RowValidator",
    "VALIDATORS",
    "get_validator",
    "validate_course_equiv_row",
    "validate_course_offering_row",
    "validate_curriculum_module_row",
    "validate_honor_row",
    "validate_student_row",
    "validate_transcript_row",
]
