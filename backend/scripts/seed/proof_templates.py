"""电子证明模板种子（S35）。"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.workflow.models import ProofTemplate
from scripts.seed import SeedResult
from scripts.seed._upsert import upsert_by_code

DOMAIN = "proof_templates"

_IN_SCHOOL_TEMPLATE = """
<p>兹证明 <strong>{{student.full_name}}</strong>，学号 <strong>{{student.student_no}}</strong>，现为中国人民大学信息学院 {{student.grade_code}} 级 {{student.major_code}} 专业学生，所在班级 {{student.class_code}}。</p>
<p>该生当前学籍状态符合学院在读证明开具条件。本证明用途：{{form.purpose}}；递交单位：{{form.deliver_to}}。</p>
<p>本证明由学院学生综合服务与党团管理平台依据已审批通过的线上申请自动生成，仅用于申请编号 {{request.request_no}} 对应事项。</p>
<div class="meta-grid">
  <div class="meta-cell"><span class="label">申请标题</span>{{request.title}}</div>
  <div class="meta-cell"><span class="label">申请编号</span>{{request.request_no}}</div>
  <div class="meta-cell"><span class="label">审批日期</span>{{request.decided_date}}</div>
  <div class="meta-cell"><span class="label">审批意见</span>{{request.decision_comment}}</div>
</div>
<div class="notice">本证明为平台生成的电子预览件，正式使用时应按学院线下盖章或电子签章管理要求完成复核。</div>
<div class="signature">
  中国人民大学信息学院<br/>
  {{today}}
</div>
"""

_PROOF_TEMPLATES: list[dict] = [
    {
        "code": "CERTIFICATE_IN_SCHOOL_V1",
        "name": "在读证明",
        "request_type_code": "CERTIFICATE_IN_SCHOOL",
        "version_label": "v1",
        "html_template": _IN_SCHOOL_TEMPLATE,
        "field_schema": {
            "placeholders": [
                "student.full_name",
                "student.student_no",
                "student.grade_code",
                "student.major_code",
                "student.class_code",
                "form.purpose",
                "form.deliver_to",
                "request.request_no",
                "request.title",
                "request.decided_date",
                "request.decision_comment",
                "today",
            ]
        },
        "is_active": True,
        "is_default": True,
    }
]


async def seed(db: AsyncSession) -> SeedResult:
    outcome = await upsert_by_code(
        db,
        ProofTemplate,
        _PROOF_TEMPLATES,
        update_fields=(
            "name",
            "request_type_code",
            "html_template",
            "field_schema",
            "is_active",
            "is_default",
        ),
    )
    return SeedResult(
        domain=DOMAIN,
        inserted=outcome.inserted,
        updated=outcome.updated,
        skipped=outcome.skipped,
    )
