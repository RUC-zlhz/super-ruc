"""电子证明模板引擎的纯单元测试。

这些测试不依赖数据库，专门固定 S35 的占位符白名单、上下文构造和 HTML 转义规则。
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.auth.models import Student
from app.core.exceptions import BizError
from app.workflow.models import REQUEST_STATUS_APPROVED, ProofTemplate, Request, RequestType
from app.workflow.pdf_generator import (
    build_render_context,
    extract_placeholders,
    render_proof_html,
    render_template_html,
    validate_template_placeholders,
)


def _certificate_request() -> Request:
    request_type = RequestType(
        id=1,
        code="CERTIFICATE_IN_SCHOOL",
        name="在读证明",
        category="CERTIFICATE",
    )
    request = Request(
        id=10,
        request_no="CERT-260524-UNIT",
        type_id=request_type.id,
        type_code=request_type.code,
        applicant_user_id=1,
        applicant_student_id=1,
        title="在读证明申请",
        form_data={
            "purpose": "<交流项目申请>",
            "deliver_to": "接收单位",
            "extra": ["一", "二"],
        },
        summary="用于单元测试",
        status=REQUEST_STATUS_APPROVED,
        revision=2,
        submitted_at=datetime(2026, 5, 20, tzinfo=UTC),
        decided_at=datetime(2026, 5, 23, tzinfo=UTC),
        decision_comment="同意开具",
    )
    request.type_ref = request_type
    return request


def _student() -> Student:
    return Student(
        id=1,
        student_no="2024000001",
        full_name="张三",
        grade_code="2024",
        major_code="CS",
        class_code="CS2401",
        political_status="共青团员",
        enrollment_year=2024,
        expected_graduation_year=2028,
    )


def test_extract_placeholders_deduplicates_and_sorts() -> None:
    placeholders = extract_placeholders(
        "{{form.purpose}} {{student.full_name}} {{ form.purpose }}"
    )

    assert placeholders == ["form.purpose", "student.full_name"]


def test_validate_template_placeholders_rejects_sensitive_unknown_field() -> None:
    with pytest.raises(BizError) as exc_info:
        validate_template_placeholders("{{student.id_card_enc}}")

    assert "未授权占位符" in str(exc_info.value)


def test_render_template_html_escapes_form_values_and_formats_lists() -> None:
    context = build_render_context(
        _certificate_request(),
        _student(),
        now=datetime(2026, 5, 24, tzinfo=UTC),
    )

    html = render_template_html(
        "{{student.full_name}} {{form.purpose}} {{form.extra}} {{today}}",
        context,
    )

    assert html == "张三 &lt;交流项目申请&gt; 一，二 2026-05-24"
    assert "<交流项目申请>" not in html


def test_render_proof_html_uses_request_type_and_approval_context() -> None:
    template = ProofTemplate(
        code="CERTIFICATE_IN_SCHOOL_UNIT",
        name="在读证明单元模板",
        request_type_code="CERTIFICATE_IN_SCHOOL",
        version_label="unit",
        html_template=(
            "<h1>{{type.name}}</h1>"
            "<p>{{student.student_no}} {{request.request_no}}</p>"
            "<p>{{request.submitted_date}} {{request.decided_date}}</p>"
            "<p>{{request.decision_comment}}</p>"
        ),
        is_active=True,
        is_default=True,
    )

    html = render_proof_html(template, _certificate_request(), _student())

    assert "<h1>在读证明</h1>" in html
    assert "2024000001 CERT-260524-UNIT" in html
    assert "2026-05-20 2026-05-23" in html
    assert "同意开具" in html
