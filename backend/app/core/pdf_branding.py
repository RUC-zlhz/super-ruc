"""Shared official-style PDF branding for generated documents."""
from __future__ import annotations

import base64
import html
import io
import logging
import os
import re
from datetime import UTC, datetime
from functools import lru_cache
from html.parser import HTMLParser
from importlib import resources
from pathlib import Path

logger = logging.getLogger(__name__)

RUC_RED = "#ae0b2a"
DARK_RED = "#7f1022"
INK = "#1f2933"
MUTED = "#667085"

_CJK_FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\simsun.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
)

_REPORTLAB_TTF_FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\simsun.ttc"),
    Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
)


@lru_cache(maxsize=8)
def _asset_data_uri(filename: str, mime_type: str) -> str:
    try:
        asset = resources.files("app.pdf_assets").joinpath(filename)
        data = asset.read_bytes()
    except Exception:  # noqa: BLE001
        logger.warning("PDF brand asset unavailable: %s", filename, exc_info=True)
        return ""
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def ruc_logo_uri() -> str:
    return _asset_data_uri("ruc-logo-red.png", "image/png")


def info_logo_uri() -> str:
    return _asset_data_uri("info-logo.png", "image/png")


def _asset_path(filename: str) -> Path | None:
    try:
        return Path(str(resources.files("app.pdf_assets").joinpath(filename)))
    except Exception:  # noqa: BLE001
        logger.warning("PDF brand asset path unavailable: %s", filename, exc_info=True)
        return None


def generated_at_label(value: datetime | None = None) -> str:
    current = value or datetime.now(UTC)
    return current.strftime("%Y-%m-%d %H:%M")


def official_document_html(
    *,
    title: str,
    subtitle: str,
    body_html: str,
    document_code: str | None = None,
    generated_at: datetime | None = None,
    footer_note: str = "本文件由信息学院学生综合服务与党团管理平台生成，可结合审批记录、审计日志或原始数据复核。",
    watermark: str | None = None,
) -> str:
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    safe_code = html.escape(document_code or "")
    safe_footer = html.escape(footer_note)
    safe_generated = generated_at_label(generated_at)
    watermark_html = (
        f'<div class="watermark">{html.escape(watermark)}</div>' if watermark else ""
    )
    code_html = (
        f'<div class="doc-code">编号：{safe_code}</div>' if safe_code else ""
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <title>{safe_title}</title>
  <style>
    @page {{
      size: A4;
      margin: 18mm 18mm 18mm 18mm;
      @bottom-center {{
        content: "第 " counter(page) " 页 / 共 " counter(pages) " 页";
        font-size: 8.5pt;
        color: #98a2b3;
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: {INK};
      font-family: "Noto Sans CJK SC", "Microsoft YaHei", "SimSun", sans-serif;
      font-size: 11pt;
      line-height: 1.72;
      background: #fff;
    }}
    .brand-strip {{
      height: 14mm;
      background: linear-gradient(90deg, {DARK_RED} 0%, {RUC_RED} 58%, #c63a4d 100%);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 9mm;
      color: #fff;
    }}
    .brand-strip .identity {{
      font-size: 9pt;
      letter-spacing: 0;
      opacity: .95;
    }}
    .info-logo {{
      max-width: 44mm;
      max-height: 8mm;
      object-fit: contain;
    }}
    .doc-shell {{
      position: relative;
      min-height: 238mm;
      padding: 11mm 9mm 8mm;
      border-left: 1px solid #f0d8dc;
      border-right: 1px solid #f0d8dc;
      border-bottom: 1px solid #f0d8dc;
    }}
    .title-row {{
      display: flex;
      align-items: center;
      padding-bottom: 8mm;
      border-bottom: 2px solid {RUC_RED};
    }}
    .ruc-logo {{
      width: 42mm;
      max-height: 20mm;
      margin-right: 8mm;
      object-fit: contain;
    }}
    .doc-kicker {{
      color: {RUC_RED};
      font-size: 10pt;
      font-weight: 700;
      margin-bottom: 2mm;
    }}
    h1 {{
      margin: 0;
      color: #111827;
      font-size: 22pt;
      font-weight: 700;
      line-height: 1.2;
      letter-spacing: 0;
    }}
    .subtitle {{
      margin-top: 2mm;
      color: {MUTED};
      font-size: 10pt;
    }}
    .doc-code {{
      margin-top: 4mm;
      color: {MUTED};
      font-size: 9.5pt;
    }}
    .content {{
      padding-top: 10mm;
      position: relative;
      z-index: 1;
    }}
    .content h2 {{
      color: {RUC_RED};
      font-size: 13pt;
      margin: 8mm 0 3mm;
      padding-left: 3mm;
      border-left: 3px solid {RUC_RED};
    }}
    .content p {{
      margin: 0 0 4mm;
      text-indent: 2em;
    }}
    .meta-grid {{
      display: flex;
      flex-wrap: wrap;
      border: 1px solid #e4e7ec;
      border-bottom: 0;
      margin: 4mm 0 6mm;
    }}
    .meta-cell {{
      width: 50%;
      min-height: 10mm;
      padding: 3mm 3.5mm;
      border-bottom: 1px solid #e4e7ec;
    }}
    .meta-cell:nth-child(odd) {{
      border-right: 1px solid #e4e7ec;
    }}
    .label {{
      display: inline-block;
      min-width: 22mm;
      color: {MUTED};
    }}
    .notice {{
      margin-top: 7mm;
      padding: 3.5mm 4mm;
      color: #6941c6;
      background: #f9f5ff;
      border-left: 3px solid #7f56d9;
      font-size: 9.5pt;
    }}
    .signature {{
      margin-top: 16mm;
      text-align: right;
      line-height: 2;
      font-size: 12pt;
    }}
    .snapshot-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 3mm;
      font-size: 9.5pt;
    }}
    .snapshot-table th,
    .snapshot-table td {{
      border: 1px solid #e4e7ec;
      padding: 2.5mm 3mm;
      text-align: left;
      vertical-align: top;
    }}
    .snapshot-table th {{
      color: #344054;
      background: #f9fafb;
      font-weight: 700;
    }}
    .metric-row {{
      display: flex;
      justify-content: space-between;
      margin: 4mm 0 8mm;
    }}
    .metric-card {{
      width: 19%;
      border: 1px solid #ead0d5;
      border-top: 3px solid {RUC_RED};
      padding: 3mm 2mm;
      text-align: center;
      background: #fffafa;
    }}
    .metric-card .name {{
      color: {MUTED};
      font-size: 8.5pt;
    }}
    .metric-card .value {{
      display: block;
      margin-top: 1.5mm;
      color: {RUC_RED};
      font-size: 16pt;
      font-weight: 700;
    }}
    .watermark {{
      position: fixed;
      left: 22mm;
      top: 112mm;
      width: 160mm;
      text-align: center;
      transform: rotate(-28deg);
      color: rgba(174, 11, 42, 0.055);
      font-size: 38pt;
      font-weight: 700;
      z-index: 0;
    }}
    .footer-note {{
      margin-top: 11mm;
      padding-top: 4mm;
      border-top: 1px solid #e4e7ec;
      color: #98a2b3;
      font-size: 8.5pt;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="brand-strip">
    <div class="identity">RENMIN UNIVERSITY OF CHINA · SCHOOL OF INFORMATION</div>
    <img class="info-logo" src="{info_logo_uri()}" alt="中国人民大学信息学院"/>
  </div>
  <main class="doc-shell">
    {watermark_html}
    <section class="title-row">
      <img class="ruc-logo" src="{ruc_logo_uri()}" alt="中国人民大学"/>
      <div>
        <div class="doc-kicker">中国人民大学信息学院</div>
        <h1>{safe_title}</h1>
        <div class="subtitle">{safe_subtitle}</div>
        {code_html}
      </div>
    </section>
    <section class="content">{body_html}</section>
    <div class="footer-note">{safe_footer} 生成时间：{safe_generated}</div>
  </main>
</body>
</html>
"""


def html_to_pdf_bytes(html_text: str) -> bytes:
    if os.name == "nt":
        return _reportlab_pdf_bytes(html_text)
    if not _has_cjk_font_file():
        logger.warning("CJK font file unavailable; using reportlab CID fallback")
        return _reportlab_pdf_bytes(html_text)
    try:
        from weasyprint import HTML  # type: ignore
    except Exception as exc:  # noqa: BLE001
        logger.warning("weasyprint unavailable; falling back to reportlab PDF renderer: %s", exc)
        return _reportlab_pdf_bytes(html_text)

    buf = io.BytesIO()
    HTML(string=html_text).write_pdf(buf)
    return buf.getvalue()


def _has_cjk_font_file() -> bool:
    return any(path.exists() for path in _CJK_FONT_CANDIDATES)


class _PlainTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        if tag in {"style", "script"}:
            self._skip_depth += 1
            return
        if tag == "br":
            self.parts.append("\n")
        if tag in {"p", "div", "h1", "h2", "tr", "li"}:
            self.parts.append("\n")
        if tag in {"td", "th"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"style", "script"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag in {"p", "div", "h1", "h2", "tr", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = html.unescape(data)
        if text.strip():
            self.parts.append(text)

    def text(self) -> str:
        raw = "".join(self.parts)
        raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
        raw = re.sub(r"\n\s*\n+", "\n", raw)
        return raw.strip()


def _register_reportlab_font() -> str:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont

    for path in _REPORTLAB_TTF_FONT_CANDIDATES:
        if not path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("SIP-CJK", str(path)))
            return "SIP-CJK"
        except Exception:  # noqa: BLE001
            logger.warning("failed to register PDF font: %s", path, exc_info=True)
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"
    except Exception:  # noqa: BLE001
        logger.warning("failed to register built-in PDF CID font", exc_info=True)
    return "Helvetica"


def _wrap_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    lines: list[str] = []
    current = ""
    for char in text:
        current += char
        if len(current) >= max_chars:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines


def _plain_text(fragment: str) -> str:
    parser = _PlainTextExtractor()
    parser.feed(fragment)
    return parser.text()


def _first_text(html_text: str, pattern: str, default: str = "") -> str:
    match = re.search(pattern, html_text, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return default
    return _plain_text(match.group(1)) or default


def _content_html(html_text: str) -> str:
    match = re.search(
        r'<section\s+class="content">(.*?)</section>\s*<div\s+class="footer-note">',
        html_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return match.group(1) if match else html_text


def _find_matching_end(text: str, start: int, tag: str) -> int:
    open_re = re.compile(rf"<{tag}\b", re.IGNORECASE)
    close_re = re.compile(rf"</{tag}\s*>", re.IGNORECASE)
    pos = start
    depth = 0
    while True:
        next_open = open_re.search(text, pos)
        next_close = close_re.search(text, pos)
        if next_close is None:
            return len(text)
        if next_open is not None and next_open.start() < next_close.start():
            depth += 1
            pos = next_open.end()
            continue
        depth -= 1
        pos = next_close.end()
        if depth <= 0:
            return pos


def _extract_meta_cells(fragment: str) -> list[tuple[str, str]]:
    cells: list[tuple[str, str]] = []
    for match in re.finditer(
        r'<div\s+class="meta-cell">(.*?)</div>',
        fragment,
        flags=re.DOTALL | re.IGNORECASE,
    ):
        cell_html = match.group(1)
        label = _first_text(
            cell_html,
            r'<span\s+class="label">(.*?)</span>',
            default="",
        )
        value_html = re.sub(
            r'<span\s+class="label">.*?</span>',
            "",
            cell_html,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )
        value = _plain_text(value_html)
        if label or value:
            cells.append((label, value))
    return cells


def _extract_metric_cards(fragment: str) -> list[tuple[str, str]]:
    cards: list[tuple[str, str]] = []
    for match in re.finditer(
        r'<div\s+class="metric-card">(.*?)</div>',
        fragment,
        flags=re.DOTALL | re.IGNORECASE,
    ):
        card_html = match.group(1)
        name = _first_text(card_html, r'<span\s+class="name">(.*?)</span>')
        value = _first_text(card_html, r'<span\s+class="value">(.*?)</span>')
        if name or value:
            cards.append((name, value))
    return cards


def _extract_table_rows(fragment: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for row_match in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", fragment, flags=re.DOTALL | re.IGNORECASE):
        cells = [
            _plain_text(cell_match.group(1))
            for cell_match in re.finditer(
                r"<t[dh]\b[^>]*>(.*?)</t[dh]>",
                row_match.group(1),
                flags=re.DOTALL | re.IGNORECASE,
            )
        ]
        if cells:
            rows.append(cells)
    return rows


def _parse_reportlab_blocks(html_text: str) -> list[tuple[str, object]]:
    body = _content_html(html_text)
    markers = [
        ('<div class="meta-grid"', "meta", "div"),
        ('<div class="metric-row"', "metrics", "div"),
        ('<div class="notice"', "notice", "div"),
        ('<div class="signature"', "signature", "div"),
        ('<table class="snapshot-table"', "table", "table"),
        ("<h2", "heading", "h2"),
        ("<p", "paragraph", "p"),
    ]
    blocks: list[tuple[str, object]] = []
    pos = 0
    while pos < len(body):
        found: tuple[int, str, str] | None = None
        lower_body = body.lower()
        for marker, kind, tag in markers:
            index = lower_body.find(marker, pos)
            if index == -1:
                continue
            if found is None or index < found[0]:
                found = (index, kind, tag)
        if found is None:
            break
        start, kind, tag = found
        end = _find_matching_end(body, start, tag)
        fragment = body[start:end]
        if kind == "meta":
            cells = _extract_meta_cells(fragment)
            if cells:
                blocks.append((kind, cells))
        elif kind == "metrics":
            cards = _extract_metric_cards(fragment)
            if cards:
                blocks.append((kind, cards))
        elif kind == "table":
            rows = _extract_table_rows(fragment)
            if rows:
                blocks.append((kind, rows))
        else:
            text = _plain_text(fragment)
            if text:
                blocks.append((kind, text))
        pos = end
    if blocks:
        return blocks
    text = _plain_text(html_text)
    return [("paragraph", line) for line in text.splitlines() if line.strip()]


def _reportlab_pdf_bytes(html_text: str) -> bytes:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    title = _first_text(html_text, r"<title>(.*?)</title>", "信息学院电子文档")
    subtitle = _first_text(html_text, r'<div\s+class="subtitle">(.*?)</div>')
    document_code = _first_text(html_text, r'<div\s+class="doc-code">编号：(.*?)</div>')
    footer_note = _first_text(
        html_text,
        r'<div\s+class="footer-note">(.*?)</div>',
        default=f"本文件由信息学院学生综合服务与党团管理平台生成 · {generated_at_label()}",
    )
    blocks = _parse_reportlab_blocks(html_text)
    font_name = _register_reportlab_font()
    ruc_logo = _asset_path("ruc-logo-red.png") or _asset_path("ruc-logo.png")
    info_logo = _asset_path("info-logo.png")

    buf = io.BytesIO()
    page_width, page_height = A4
    margin_x = 18 * mm

    styles = {
        "body": ParagraphStyle(
            "body",
            fontName=font_name,
            fontSize=10.5,
            leading=18,
            textColor=HexColor(INK),
            firstLineIndent=18,
            spaceAfter=8,
        ),
        "heading": ParagraphStyle(
            "heading",
            fontName=font_name,
            fontSize=13,
            leading=17,
            textColor=HexColor(RUC_RED),
            borderColor=HexColor(RUC_RED),
            borderWidth=0,
            borderPadding=0,
            leftIndent=0,
            spaceBefore=10,
            spaceAfter=7,
        ),
        "cell_label": ParagraphStyle(
            "cell_label",
            fontName=font_name,
            fontSize=8,
            leading=10,
            textColor=HexColor(MUTED),
        ),
        "cell_value": ParagraphStyle(
            "cell_value",
            fontName=font_name,
            fontSize=10,
            leading=13,
            textColor=HexColor(INK),
        ),
        "notice": ParagraphStyle(
            "notice",
            fontName=font_name,
            fontSize=9.3,
            leading=14,
            textColor=HexColor("#6941c6"),
        ),
        "signature": ParagraphStyle(
            "signature",
            fontName=font_name,
            fontSize=11.5,
            leading=22,
            alignment=2,
            textColor=HexColor(INK),
        ),
        "table": ParagraphStyle(
            "table",
            fontName=font_name,
            fontSize=8.7,
            leading=12,
            textColor=HexColor(INK),
        ),
    }

    def para(text: str, style: str = "body") -> Paragraph:
        return Paragraph(html.escape(text).replace("\n", "<br/>"), styles[style])

    def draw_page(canvas, doc) -> None:  # noqa: ANN001
        canvas.saveState()
        canvas.setFillColor(HexColor(DARK_RED))
        canvas.rect(0, page_height - 14 * mm, page_width, 14 * mm, fill=1, stroke=0)
        canvas.setFillColor(HexColor(RUC_RED))
        canvas.rect(page_width * 0.40, page_height - 14 * mm, page_width * 0.60, 14 * mm, fill=1, stroke=0)
        canvas.setFillColor("white")
        canvas.setFont(font_name, 8.5)
        canvas.drawString(margin_x, page_height - 8.8 * mm, "RENMIN UNIVERSITY OF CHINA · SCHOOL OF INFORMATION")
        if info_logo and info_logo.exists():
            canvas.drawImage(
                ImageReader(str(info_logo)),
                page_width - margin_x - 44 * mm,
                page_height - 11.4 * mm,
                width=44 * mm,
                height=7.5 * mm,
                preserveAspectRatio=True,
                mask="auto",
            )
        title_y = page_height - 30 * mm
        if ruc_logo and ruc_logo.exists():
            canvas.drawImage(
                ImageReader(str(ruc_logo)),
                margin_x,
                title_y - 8 * mm,
                width=42 * mm,
                height=18 * mm,
                preserveAspectRatio=True,
                mask="auto",
            )
        title_x = margin_x + 49 * mm
        canvas.setFillColor(HexColor(RUC_RED))
        canvas.setFont(font_name, 10)
        canvas.drawString(title_x, title_y + 7 * mm, "中国人民大学信息学院")
        canvas.setFillColor(HexColor(INK))
        canvas.setFont(font_name, 20)
        canvas.drawString(title_x, title_y - 1 * mm, title[:26])
        canvas.setFillColor(HexColor(MUTED))
        canvas.setFont(font_name, 9)
        if subtitle:
            canvas.drawString(title_x, title_y - 8 * mm, subtitle[:42])
        if document_code:
            canvas.drawString(title_x, title_y - 14 * mm, f"编号：{document_code[:48]}")
        canvas.setStrokeColor(HexColor(RUC_RED))
        canvas.setLineWidth(1.4)
        canvas.line(margin_x, title_y - 19 * mm, page_width - margin_x, title_y - 19 * mm)

        canvas.saveState()
        canvas.setFillColor(HexColor(RUC_RED))
        try:
            canvas.setFillAlpha(0.045)
        except Exception:  # noqa: BLE001
            logger.debug("reportlab alpha transparency unavailable", exc_info=True)
        canvas.setFont(font_name, 40)
        canvas.translate(page_width / 2, page_height / 2)
        canvas.rotate(32)
        canvas.drawCentredString(0, 0, "中国人民大学信息学院")
        canvas.restoreState()

        canvas.setStrokeColor(HexColor("#e4e7ec"))
        canvas.line(margin_x, 16 * mm, page_width - margin_x, 16 * mm)
        canvas.setFillColor(HexColor(MUTED))
        canvas.setFont(font_name, 7.8)
        footer = footer_note
        if len(footer) > 88:
            footer = footer[:87] + "..."
        canvas.drawCentredString(page_width / 2, 10.5 * mm, footer)
        canvas.drawRightString(page_width - margin_x, 5.2 * mm, f"第 {doc.page} 页")
        canvas.restoreState()

    story: list[object] = []
    content_width = page_width - 2 * margin_x
    for kind, value in blocks:
        if kind == "heading":
            heading_table = Table(
                [[Paragraph("", styles["heading"]), para(str(value), "heading")]],
                colWidths=[3 * mm, content_width - 3 * mm],
            )
            heading_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), HexColor(RUC_RED)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.extend([heading_table, Spacer(1, 3 * mm)])
        elif kind == "paragraph":
            story.append(para(str(value), "body"))
        elif kind == "meta":
            cells = list(value)  # type: ignore[arg-type]
            rows = []
            for i in range(0, len(cells), 2):
                row = []
                for label, cell_value in cells[i : i + 2]:
                    row.append([para(str(label), "cell_label"), para(str(cell_value or "-"), "cell_value")])
                while len(row) < 2:
                    row.append("")
                rows.append(row)
            table = Table(rows, colWidths=[content_width / 2, content_width / 2])
            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.45, HexColor("#e4e7ec")),
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#fffafa")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.extend([table, Spacer(1, 7 * mm)])
        elif kind == "metrics":
            cards = list(value)  # type: ignore[arg-type]
            row = []
            for name, metric_value in cards:
                row.append([para(str(name), "cell_label"), para(str(metric_value), "heading")])
            table = Table([row], colWidths=[content_width / max(len(row), 1)] * len(row))
            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.55, HexColor("#ead0d5")),
                ("LINEABOVE", (0, 0), (-1, 0), 2.0, HexColor(RUC_RED)),
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#fffafa")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            story.extend([table, Spacer(1, 7 * mm)])
        elif kind == "table":
            rows = list(value)  # type: ignore[arg-type]
            data = [[para(str(cell), "table") for cell in row] for row in rows]
            col_count = max(len(row) for row in rows)
            table = Table(data, colWidths=[content_width / col_count] * col_count, repeatRows=1)
            table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.45, HexColor("#e4e7ec")),
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f9fafb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#344054")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(table)
        elif kind == "notice":
            table = Table([[para(str(value), "notice")]], colWidths=[content_width])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f9f5ff")),
                ("LINEBEFORE", (0, 0), (0, -1), 2.0, HexColor("#7f56d9")),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            story.extend([Spacer(1, 3 * mm), table, Spacer(1, 8 * mm)])
        elif kind == "signature":
            story.extend([Spacer(1, 10 * mm), para(str(value), "signature")])
    if not story:
        story.append(para("暂无可导出的文档内容。"))
    story.append(PageBreak())
    story.pop()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=margin_x,
        rightMargin=margin_x,
        topMargin=55 * mm,
        bottomMargin=22 * mm,
    )
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return buf.getvalue()
