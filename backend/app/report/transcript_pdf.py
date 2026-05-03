"""成绩单 PDF 文本层保守分析。

本模块只产出人工核验候选，不生成可直接入库的正式成绩。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Any

_MAX_TEXT_CHARS = 20_000
_MAX_CANDIDATES = 30
_COURSE_CODE_RE = re.compile(r"\b[A-Z]{2,8}[-_]?\d{2,5}[A-Z]?\b")
_CREDIT_RE = re.compile(r"(?:学分|credit[s]?)\D{0,8}(\d+(?:\.\d+)?)", re.IGNORECASE)
_SCORE_RE = re.compile(r"(?:成绩|分数|score)\D{0,8}(\d+(?:\.\d+)?)", re.IGNORECASE)
_TERM_RE = re.compile(
    r"\b20\d{2}[-_/]?(?:SPRING|FALL|SUMMER|AUTUMN|[12])\b",
    re.IGNORECASE,
)
_GRADE_RE = re.compile(r"\b(A\+?|A-|B\+?|B-|C\+?|C-|D\+?|D-|F|P|NP)\b")


@dataclass
class TranscriptPdfCandidate:
    line_no: int
    raw_text: str
    course_code: str | None = None
    course_name: str | None = None
    credits: float | None = None
    term_code: str | None = None
    score: float | None = None
    grade_letter: str | None = None
    pass_flag: bool | None = None
    confidence: str = "LOW"


@dataclass
class TranscriptPdfAnalysis:
    extracted_text: str
    data_warnings: list[str]
    candidate_courses: list[TranscriptPdfCandidate]


def analyze_transcript_pdf(
    pdf_bytes: bytes,
    *,
    student_no: str,
    student_name: str,
) -> TranscriptPdfAnalysis:
    """尽力抽取文本层，并返回低置信度人工核验候选。"""
    text, extraction_warnings = _extract_pdf_text(pdf_bytes)
    warnings = [
        "成绩单 PDF 已保存为待人工核验记录；本次上传不会写入正式成绩表。",
        *extraction_warnings,
    ]

    normalized_text = _normalize_text(text)
    candidates = _parse_candidate_courses(normalized_text)

    if normalized_text:
        if student_no and student_no not in normalized_text:
            warnings.append("PDF 文本层未识别到当前登录学号，需人工核验上传人与成绩单归属。")
        if student_name and student_name not in normalized_text:
            warnings.append("PDF 文本层未识别到当前登录姓名，需人工核验上传人与成绩单归属。")

    if not normalized_text:
        warnings.append("未能从 PDF 文本层抽取成绩文本，可能为扫描件或图片化 PDF，需人工核验原件。")
    elif not candidates:
        warnings.append("未从 PDF 文本层识别出可核验的课程行，需人工核验原件。")
    else:
        warnings.append(
            f"已从 PDF 文本层识别 {len(candidates)} 条疑似课程记录，均需人工核验后才能入库。"
        )

    return TranscriptPdfAnalysis(
        extracted_text=normalized_text[:_MAX_TEXT_CHARS],
        data_warnings=_dedupe(warnings),
        candidate_courses=candidates[:_MAX_CANDIDATES],
    )


def _extract_pdf_text(pdf_bytes: bytes) -> tuple[str, list[str]]:
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        try:
            from PyPDF2 import PdfReader  # type: ignore[import-not-found,no-redef]
        except ModuleNotFoundError:
            return "", ["当前运行环境未安装 PDF 文本解析依赖，已保存上传记录，需人工核验。"]

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        parts: list[str] = []
        for page in reader.pages[:20]:
            page_text = page.extract_text() or ""
            if page_text:
                parts.append(page_text)
        return "\n".join(parts), []
    except Exception as exc:
        message = str(exc).strip() or exc.__class__.__name__
        return "", [f"PDF 文本抽取失败：{message[:120]}；已保存上传记录，需人工核验。"]


def _normalize_text(text: str) -> str:
    lines = []
    for raw in text.replace("\r", "\n").split("\n"):
        line = " ".join(raw.split())
        if line:
            lines.append(line)
    return "\n".join(lines)


def _parse_candidate_courses(text: str) -> list[TranscriptPdfCandidate]:
    candidates: list[TranscriptPdfCandidate] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if len(candidates) >= _MAX_CANDIDATES:
            break
        candidate = _parse_candidate_line(line_no, line)
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _parse_candidate_line(line_no: int, line: str) -> TranscriptPdfCandidate | None:
    course_code = _first_match(_COURSE_CODE_RE, line)
    if course_code is None:
        return None

    credits = _first_float(_CREDIT_RE, line)
    score = _first_float(_SCORE_RE, line)
    grade_letter = _first_match(_GRADE_RE, line)
    term_code = _first_match(_TERM_RE, line)
    pass_flag = _derive_pass_flag(score=score, grade_letter=grade_letter)
    course_name = _guess_course_name(line, course_code)

    return TranscriptPdfCandidate(
        line_no=line_no,
        raw_text=line[:300],
        course_code=course_code,
        course_name=course_name,
        credits=credits,
        term_code=term_code,
        score=score,
        grade_letter=grade_letter,
        pass_flag=pass_flag,
    )


def _first_match(pattern: re.Pattern[str], value: str) -> str | None:
    match = pattern.search(value)
    return match.group(0) if match else None


def _first_float(pattern: re.Pattern[str], value: str) -> float | None:
    match = pattern.search(value)
    if not match:
        return None
    try:
        return float(match.group(1))
    except (TypeError, ValueError):
        return None


def _derive_pass_flag(
    *,
    score: float | None,
    grade_letter: str | None,
) -> bool | None:
    if score is not None:
        return score >= 60
    if grade_letter is None:
        return None
    normalized = grade_letter.upper()
    if normalized == "P":
        return True
    if normalized in {"F", "NP"}:
        return False
    return None


def _guess_course_name(line: str, course_code: str) -> str | None:
    _, _, tail = line.partition(course_code)
    tokens = tail.strip(" :-：\t").split()
    name_parts = []
    for token in tokens:
        lower = token.lower()
        if lower in {"credits", "credit", "score"} or token in {"学分", "成绩", "分数"}:
            break
        if re.fullmatch(r"\d+(?:\.\d+)?", token):
            break
        name_parts.append(token)
    name = " ".join(name_parts).strip()
    return name[:128] or None


def candidate_to_dict(candidate: TranscriptPdfCandidate) -> dict[str, Any]:
    return {
        "line_no": candidate.line_no,
        "raw_text": candidate.raw_text,
        "course_code": candidate.course_code,
        "course_name": candidate.course_name,
        "credits": candidate.credits,
        "term_code": candidate.term_code,
        "score": candidate.score,
        "grade_letter": candidate.grade_letter,
        "pass_flag": candidate.pass_flag,
        "confidence": candidate.confidence,
    }


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
