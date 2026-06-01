from __future__ import annotations

import pytest

from app.core.exceptions import BizError
from app.workflow.models import RequestType
from app.workflow.service import _validate_request_form_data


def _leave_type() -> RequestType:
    return RequestType(
        code="LEAVE_PERSONAL",
        name="个人请假",
        category="LEAVE",
        attachment_required=False,
        allow_withdraw=True,
        approver_roles="COUNSELOR",
    )


def _certificate_type() -> RequestType:
    return RequestType(
        code="CERTIFICATE_IN_SCHOOL",
        name="在读证明",
        category="CERTIFICATE",
        attachment_required=False,
        allow_withdraw=True,
        approver_roles="COUNSELOR",
    )


def test_leave_request_form_rejects_start_date_after_end_date() -> None:
    with pytest.raises(BizError) as exc_info:
        _validate_request_form_data(
            _leave_type(),
            {
                "reason": "日期顺序回归",
                "start_date": "2026-05-30",
                "end_date": "2026-05-29",
            },
        )

    assert exc_info.value.code == 40044


def test_leave_request_form_allows_valid_or_partial_dates() -> None:
    _validate_request_form_data(
        _leave_type(),
        {"start_date": "2026-05-29", "end_date": "2026-05-30"},
    )
    _validate_request_form_data(_leave_type(), {"start_date": "2026-05-29"})


def test_non_leave_request_form_ignores_date_like_fields() -> None:
    _validate_request_form_data(
        _certificate_type(),
        {"start_date": "2026-05-30", "end_date": "2026-05-29"},
    )
