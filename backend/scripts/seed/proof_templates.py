"""电子证明模板种子（S35）。"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.workflow.models import ProofTemplate
from scripts.seed import SeedResult
from scripts.seed._upsert import upsert_by_code

DOMAIN = "proof_templates"

_IN_SCHOOL_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <title>在读证明</title>
  <style>
    @page { size: A4; margin: 2.5cm; }
    body { font-family: "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; color: #111; }
    .doc { min-height: 24cm; position: relative; }
    h1 { text-align: center; font-size: 24pt; margin: 18pt 0 36pt; letter-spacing: 0; }
    p { font-size: 13pt; line-height: 2.0; text-indent: 2em; margin: 0 0 12pt; }
    .meta { margin-top: 28pt; font-size: 11pt; color: #555; line-height: 1.8; }
    .signature { margin-top: 72pt; text-align: right; font-size: 13pt; line-height: 2; }
    .watermark { position: fixed; top: 38%; left: 12%; color: #eee; font-size: 72pt; transform: rotate(-28deg); z-index: -1; }
  </style>
</head>
<body>
  <div class="doc">
    <div class="watermark">PREVIEW</div>
    <h1>在读证明</h1>
    <p>兹证明 {{student.full_name}}，学号 {{student.student_no}}，现为中国人民大学信息学院 {{student.grade_code}} 级 {{student.major_code}} 专业学生，所在班级 {{student.class_code}}。</p>
    <p>该生当前学籍状态符合学院在读证明开具条件。本证明用途：{{form.purpose}}；递交单位：{{form.deliver_to}}。</p>
    <p>本证明由学院学生综合服务与党团管理平台依据已审批通过的线上申请自动生成，仅用于申请编号 {{request.request_no}} 对应事项。</p>
    <div class="meta">
      申请标题：{{request.title}}<br/>
      审批日期：{{request.decided_date}}<br/>
      审批意见：{{request.decision_comment}}
    </div>
    <div class="signature">
      中国人民大学信息学院<br/>
      {{today}}
    </div>
  </div>
</body>
</html>
"""

_PROOF_TEMPLATES: list[dict] = [
    {
        "code": "CERTIFICATE_IN_SCHOOL_V1",
        "name": "在读证明正式模板",
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
