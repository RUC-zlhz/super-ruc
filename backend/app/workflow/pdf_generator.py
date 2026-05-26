"""电子证明模板渲染与 PDF 生成（FR-006 / S35）。"""
from __future__ import annotations

import html
import re
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student
from app.core import pdf_branding
from app.core.exceptions import BizError, NotFoundError
from app.workflow import repository as repo
from app.workflow.models import REQUEST_STATUS_APPROVED, ProofTemplate, Request

_CERTIFICATE_CATEGORY = "CERTIFICATE"
_PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)*)\s*}}")
_FIXED_ALLOWED_PLACEHOLDERS = {
    "today",
    "student.full_name",
    "student.student_no",
    "student.grade_code",
    "student.major_code",
    "student.class_code",
    "student.political_status",
    "student.enrollment_year",
    "student.expected_graduation_year",
    "request.request_no",
    "request.title",
    "request.summary",
    "request.status",
    "request.revision",
    "request.submitted_date",
    "request.decided_date",
    "request.decision_comment",
    "type.code",
    "type.name",
    "type.category",
}


def _is_certificate_request(req: Request) -> bool:
    rt = req.type_ref
    if rt is None:
        return False
    if rt.category == _CERTIFICATE_CATEGORY:
        return True
    return (req.type_code or "").upper().startswith("CERT")


def extract_placeholders(template: str) -> list[str]:
    return sorted(set(_PLACEHOLDER_RE.findall(template or "")))


def validate_template_placeholders(template: str) -> list[str]:
    placeholders = extract_placeholders(template)
    unknown = [
        key
        for key in placeholders
        if key not in _FIXED_ALLOWED_PLACEHOLDERS and not key.startswith("form.")
    ]
    if unknown:
        raise BizError(
            "证明模板包含未授权占位符：" + "、".join(sorted(unknown)),
            code=40041,
        )
    return placeholders


def _format_date(value: datetime | date | None) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d")


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime | date):
        return _format_date(value)
    if isinstance(value, list | tuple):
        return "，".join(_stringify(item) for item in value)
    if isinstance(value, dict):
        return "，".join(f"{k}: {_stringify(v)}" for k, v in value.items())
    return str(value)


def _context_get(context: dict[str, Any], path: str) -> Any:
    value: Any = context
    for part in path.split("."):
        if isinstance(value, dict):
            value = value.get(part)
            continue
        return None
    return value


def render_template_html(template: str, context: dict[str, Any]) -> str:
    validate_template_placeholders(template)

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return html.escape(_stringify(_context_get(context, key)))

    return _PLACEHOLDER_RE.sub(replace, template)


def build_render_context(
    req: Request,
    student: Student | None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = now or datetime.now(UTC)
    return {
        "today": current.strftime("%Y-%m-%d"),
        "student": {
            "full_name": student.full_name if student else "",
            "student_no": student.student_no if student else "",
            "grade_code": student.grade_code if student else "",
            "major_code": student.major_code if student else "",
            "class_code": student.class_code if student else "",
            "political_status": student.political_status if student else "",
            "enrollment_year": student.enrollment_year if student else "",
            "expected_graduation_year": (
                student.expected_graduation_year if student else ""
            ),
        },
        "request": {
            "request_no": req.request_no,
            "title": req.title,
            "summary": req.summary,
            "status": req.status,
            "revision": req.revision,
            "submitted_date": _format_date(req.submitted_at),
            "decided_date": _format_date(req.decided_at),
            "decision_comment": req.decision_comment,
        },
        "type": {
            "code": req.type_code,
            "name": req.type_ref.name if req.type_ref else req.type_code,
            "category": req.type_ref.category if req.type_ref else "",
        },
        "form": req.form_data or {},
    }


def render_proof_html(
    template: ProofTemplate,
    req: Request,
    student: Student | None,
) -> str:
    context = build_render_context(req, student)
    body_html = render_template_html(template.html_template, context)
    return pdf_branding.official_document_html(
        title=template.name or "电子证明",
        subtitle="电子证明 · 审批通过后生成",
        body_html=body_html,
        document_code=req.request_no,
        generated_at=datetime.now(UTC),
        watermark="信息学院",
    )


def _html_to_pdf_bytes(html_text: str) -> bytes:
    return pdf_branding.html_to_pdf_bytes(html_text)


async def _get_approved_certificate_request(
    db: AsyncSession, request_id: int
) -> Request:
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    if not _is_certificate_request(req):
        raise BizError("该申请类型不支持生成证明 PDF", code=40028)
    if req.status != REQUEST_STATUS_APPROVED:
        raise BizError(
            f"仅已批准的申请可预览证明 PDF，当前状态 {req.status}",
            code=40029,
        )
    return req


async def render_proof_html_for_request(db: AsyncSession, request_id: int) -> str:
    req = await _get_approved_certificate_request(db, request_id)
    template = await repo.get_active_proof_template(db, req.type_code)
    if template is None:
        raise BizError(
            f"申请类型 {req.type_code} 未配置有效电子证明模板",
            code=40040,
        )
    student: Student | None = None
    if req.applicant_student_id is not None:
        student = await db.get(Student, req.applicant_student_id)
    return render_proof_html(template, req, student)


async def generate_proof_pdf(
    db: AsyncSession, request_id: int
) -> tuple[bytes, str]:
    """生成证明 PDF 预览。

    返回 (pdf_bytes, filename)。由 router 以 StreamingResponse 返回。
    """
    req = await _get_approved_certificate_request(db, request_id)
    template = await repo.get_active_proof_template(db, req.type_code)
    if template is None:
        raise BizError(
            f"申请类型 {req.type_code} 未配置有效电子证明模板",
            code=40040,
        )
    student: Student | None = None
    if req.applicant_student_id is not None:
        student = await db.get(Student, req.applicant_student_id)

    html_text = render_proof_html(template, req, student)
    pdf_bytes = _html_to_pdf_bytes(html_text)
    filename = f"proof-{req.request_no}.pdf"
    return pdf_bytes, filename
