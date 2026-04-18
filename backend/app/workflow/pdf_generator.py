"""证明类申请的 PDF 预览生成（FR-006 / v1.5）。

职责单一：给定 Request 及相关实体，渲染一份可预览的 PDF 字节流，由 router 层返回。

- 默认使用 weasyprint（HTML → PDF），模板用内联 Jinja-like f-string；
- 未安装 weasyprint 时抛 BizError（依赖在 pyproject.toml 里是强依赖，
  但 Windows 开发机可能没装 GTK 运行时，需给一个可读的报错）。

业务规则：
- 仅 APPROVED 状态的证明类（category=="CERTIFICATE" 或 type_code 以 "CERT" 开头）
  允许预览；其他返回 BizError。
"""
from __future__ import annotations

import html as html_escape
import io
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student
from app.core.exceptions import BizError, NotFoundError
from app.workflow import repository as repo
from app.workflow.models import REQUEST_STATUS_APPROVED, Request

logger = logging.getLogger(__name__)


_CERTIFICATE_CATEGORY = "CERTIFICATE"


def _is_certificate_request(req: Request) -> bool:
    rt = req.type_ref
    if rt is None:
        return False
    if rt.category == _CERTIFICATE_CATEGORY:
        return True
    return (req.type_code or "").upper().startswith("CERT")


def _render_html(req: Request, student: Student | None) -> str:
    e = html_escape.escape
    now_text = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = e(req.title or "证明")
    type_name = e(req.type_ref.name if req.type_ref else req.type_code)
    student_block = ""
    if student is not None:
        student_block = f"""
        <div class="row"><label>姓名</label><span>{e(student.full_name or "")}</span></div>
        <div class="row"><label>学号</label><span>{e(student.student_no or "")}</span></div>
        """
    decided_at = (
        req.decided_at.strftime("%Y-%m-%d") if req.decided_at else now_text
    )
    summary = e(req.summary or "")
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"/><title>{title}</title>
<style>
@page {{ size: A4; margin: 2cm; }}
body {{ font-family: "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; color: #222; }}
h1 {{ text-align: center; font-size: 22pt; margin-bottom: 28pt; }}
.row {{ display: flex; margin: 8pt 0; font-size: 12pt; }}
.row label {{ width: 90pt; color: #555; }}
.summary {{ margin-top: 20pt; line-height: 1.8; font-size: 12pt; white-space: pre-wrap; }}
.footer {{ margin-top: 60pt; text-align: right; font-size: 12pt; }}
.watermark {{ position: fixed; top: 40%; left: 20%; color: #eee; font-size: 72pt; transform: rotate(-30deg); z-index: -1; }}
</style></head>
<body>
<div class="watermark">预览 PREVIEW</div>
<h1>{title}</h1>
<div class="row"><label>申请类型</label><span>{type_name}</span></div>
<div class="row"><label>申请编号</label><span>{e(req.request_no)}</span></div>
{student_block}
<div class="row"><label>审批状态</label><span>已批准</span></div>
<div class="row"><label>审批日期</label><span>{decided_at}</span></div>
<div class="summary">{summary}</div>
<div class="footer">信息学院 · {now_text}</div>
</body></html>
"""


def _html_to_pdf_bytes(html: str) -> bytes:
    try:
        from weasyprint import HTML  # type: ignore
    except Exception as e:  # noqa: BLE001
        logger.warning("weasyprint unavailable: %s", e)
        raise BizError(
            "PDF 生成依赖未就绪（weasyprint + GTK 运行时），请联系运维", code=50003, http_status=500
        ) from e
    buf = io.BytesIO()
    HTML(string=html).write_pdf(buf)
    return buf.getvalue()


async def generate_proof_pdf(
    db: AsyncSession, request_id: int
) -> tuple[bytes, str]:
    """生成证明 PDF 预览。

    返回 (pdf_bytes, filename)。由 router 以 StreamingResponse 返回。
    """
    req = await repo.get_request(db, request_id)
    if req is None:
        raise NotFoundError("申请不存在")
    if not _is_certificate_request(req):
        raise BizError("该申请类型不支持生成证明 PDF", code=40028)
    if req.status != REQUEST_STATUS_APPROVED:
        raise BizError(
            f"仅已批准的申请可预览证明 PDF，当前状态 {req.status}", code=40029
        )
    student: Student | None = None
    if req.applicant_student_id is not None:
        student = await db.get(Student, req.applicant_student_id)

    html = _render_html(req, student)
    pdf_bytes = _html_to_pdf_bytes(html)
    filename = f"proof-{req.request_no}.pdf"
    return pdf_bytes, filename
