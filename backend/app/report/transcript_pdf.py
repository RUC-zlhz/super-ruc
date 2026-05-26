"""成绩单 PDF 文本层保守分析。

本模块只产出人工核验候选，不生成可直接入库的正式成绩。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Any

_MAX_TEXT_CHARS = 20_000
_MAX_CANDIDATES = 100
_COURSE_CODE_RE = re.compile(r"\b[A-Z]{2,8}[-_]?\d{2,5}[A-Z]?\b")
_CREDIT_RE = re.compile(r"(?:学分|credit[s]?)\D{0,8}(\d+(?:\.\d+)?)", re.IGNORECASE)
_SCORE_RE = re.compile(r"(?:成绩|分数|score)\D{0,8}(\d+(?:\.\d+)?)", re.IGNORECASE)
_TERM_RE = re.compile(
    r"\b20\d{2}[-_/]?(?:SPRING|FALL|SUMMER|AUTUMN|[12])\b",
    re.IGNORECASE,
)
_GRADE_RE = re.compile(r"\b(A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D-|D|F|NP|P)\b")
_RUC_COMPACT_TRANSCRIPT_SCORE_RE = re.compile(
    r"^(?P<prefix>.*?)"
    r"(?P<credits>\d+(?:\.\d+)?)\s+"
    r"(?P<grade>\d+(?:\.\d+)?|A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D-|D|F|NP|P)\s+"
    r"(?P<points>\d+(?:\.\d+)?)$"
)
_RUC_TRANSCRIPT_ROW_RE = re.compile(
    r"^(?P<prefix>.*?)\s*"
    r"(?P<credits>\d+(?:\.\d+)?)\s+"
    r"(?P<results>"
    r"(?:\d+(?:\.\d+)?|A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D-|D|F|NP|P)"
    r"(?:\s+(?:\d+(?:\.\d+)?|A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D-|D|F|NP|P)){0,6}"
    r")\s+"
    r"(?P<points>\d+(?:\.\d+)?)$"
)
_RUC_TERM_RE = re.compile(
    r"(?P<year>20\d{2}\s*-\s*20\d{2})\s*学年\s*(?P<season>春季|夏季|秋季|冬季)\s*学期"
)
_RUC_COURSE_PROPERTY_LABELS = tuple(
    sorted(
        {
            "数据与信息技术平台课",
            "公共外语（拓展类课程）",
            "思想政治理论课",
            "科研与实践环节",
            "职业生涯规划",
            "心理健康教育",
            "新生研讨课",
            "个性化选修",
            "公共选修课",
            "专业核心课",
            "专业基础课",
            "专业选修课",
            "部类基础",
            "部类共同",
            "公共外语",
            "公共数学",
            "军事课",
            "公共体育",
            "美育课程",
        },
        key=len,
        reverse=True,
    )
)


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
    ruc_candidates = _parse_ruc_transcript_courses(text)
    if ruc_candidates:
        return ruc_candidates

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


def _parse_ruc_transcript_courses(text: str) -> list[TranscriptPdfCandidate]:
    compact_text = _compact_course_text(text)
    legacy_candidates = _parse_legacy_ruc_transcript_courses(text, compact_text)
    if legacy_candidates:
        return legacy_candidates
    if "课程名称" not in compact_text or "学分绩点" not in compact_text:
        return []
    if "学号" not in compact_text and "学生成绩单" not in compact_text:
        return []

    candidates: list[TranscriptPdfCandidate] = []
    pending_lines: list[str] = []
    current_term: str | None = None
    in_course_area = False
    current_term_start_index = 0

    for line_no, line in enumerate(text.splitlines(), start=1):
        score_line = " ".join(line.split())
        compact = _compact_course_text(line)
        if not compact:
            continue
        if "课程名称" in compact and "学分绩点" in compact:
            in_course_area = True
            pending_lines.clear()
            continue
        if not in_course_area:
            continue
        summary_term = _extract_ruc_summary_term(compact)
        if summary_term is not None:
            for candidate in candidates[current_term_start_index:]:
                if candidate.term_code is None:
                    candidate.term_code = summary_term
            current_term = None
            current_term_start_index = len(candidates)
            pending_lines.clear()
            if "各学期汇总" in compact:
                break
            continue
        if "各学期汇总" in compact:
            break

        pending_lines.append(score_line)
        joined_line = " ".join(part for part in pending_lines if part)
        score_match = _RUC_TRANSCRIPT_ROW_RE.fullmatch(joined_line)
        if score_match is None:
            continue

        raw_prefix = score_match.group("prefix").strip()
        compact_prefix = _compact_course_text(raw_prefix)
        course_name, detected_term = _take_ruc_course_name(
            compact_value=compact_prefix,
            raw_value=raw_prefix,
        )
        pending_lines.clear()
        if detected_term is not None:
            current_term = detected_term
        if not course_name:
            continue

        credits = _safe_float(score_match.group("credits"))
        result_tokens = score_match.group("results").split()
        final_token = result_tokens[-1]
        score = _safe_float(final_token)
        grade_letter = None if score is not None else final_token
        candidates.append(
            TranscriptPdfCandidate(
                line_no=line_no,
                raw_text=(
                    f"{course_name} 学分 {score_match.group('credits')} "
                    f"成绩 {final_token} 绩点 {score_match.group('points')}"
                )[:300],
                course_name=course_name,
                credits=credits,
                term_code=current_term,
                score=score,
                grade_letter=grade_letter,
                pass_flag=_derive_pass_flag(score=score, grade_letter=grade_letter),
                confidence="MEDIUM",
            )
        )
        if len(candidates) >= _MAX_CANDIDATES:
            break

    return candidates


def _parse_legacy_ruc_transcript_courses(
    text: str,
    compact_text: str,
) -> list[TranscriptPdfCandidate]:
    if "学生成绩单" not in compact_text or "总取得学分" not in compact_text:
        return []

    candidates: list[TranscriptPdfCandidate] = []
    pending_parts: list[str] = []
    current_term: str | None = None
    in_course_area = False

    for line_no, line in enumerate(text.splitlines(), start=1):
        score_line = " ".join(line.split())
        compact = _compact_course_text(line)
        if not compact:
            continue
        if "课程名称" in compact and "学分绩点" in compact:
            in_course_area = True
            pending_parts.clear()
            continue
        if "总取得学分" in compact:
            break
        if not in_course_area:
            continue

        score_match = _RUC_COMPACT_TRANSCRIPT_SCORE_RE.fullmatch(score_line)
        if score_match is None:
            pending_parts.append(compact)
            continue

        prefix = _compact_course_text(score_match.group("prefix"))
        if prefix:
            pending_parts.append(prefix)
        course_name, detected_term = _take_ruc_compact_course_name(pending_parts)
        pending_parts.clear()
        if detected_term is not None:
            current_term = detected_term
        if not course_name:
            continue

        credits = _safe_float(score_match.group("credits"))
        grade_token = score_match.group("grade")
        score = _safe_float(grade_token)
        grade_letter = None if score is not None else grade_token
        candidates.append(
            TranscriptPdfCandidate(
                line_no=line_no,
                raw_text=(
                    f"{course_name} 学分 {score_match.group('credits')} "
                    f"成绩 {grade_token} 绩点 {score_match.group('points')}"
                )[:300],
                course_name=course_name,
                credits=credits,
                term_code=current_term,
                score=score,
                grade_letter=grade_letter,
                pass_flag=_derive_pass_flag(score=score, grade_letter=grade_letter),
                confidence="MEDIUM",
            )
        )
        if len(candidates) >= _MAX_CANDIDATES:
            break

    return candidates


def _extract_ruc_summary_term(compact: str) -> str | None:
    if "学期" not in compact or "学分" not in compact:
        return None
    if "已取得总学分" not in compact and "总取得学分" not in compact and "总学分绩点" not in compact:
        return None
    term_match = _RUC_TERM_RE.search(compact)
    if term_match is None:
        return None
    year = term_match.group("year").replace(" ", "")
    return _ruc_term_code(year, term_match.group("season"))


def _take_ruc_compact_course_name(parts: list[str]) -> tuple[str | None, str | None]:
    joined = _compact_course_text("".join(parts))
    if not joined:
        return None, None

    detected_term = None
    term_match = _RUC_TERM_RE.search(joined)
    if term_match is not None:
        year = term_match.group("year").replace(" ", "")
        detected_term = _ruc_term_code(year, term_match.group("season"))
        joined = joined[term_match.end() :]

    joined = _strip_ruc_noise(joined)
    if not joined:
        return None, detected_term
    return joined[:128], detected_term


def _take_ruc_course_name(*, compact_value: str, raw_value: str) -> tuple[str | None, str | None]:
    if not compact_value:
        return None, None

    detected_term = None
    term_match = _RUC_TERM_RE.search(compact_value)
    if term_match is not None:
        year = term_match.group("year").replace(" ", "")
        detected_term = _ruc_term_code(year, term_match.group("season"))
        compact_value = compact_value[term_match.end() :]

    compact_value = _strip_ruc_noise(compact_value)
    raw_tokens = [token.strip() for token in raw_value.split() if token.strip()]
    raw_tokens, had_property_label = _strip_ruc_course_property_tokens(raw_tokens)
    if had_property_label:
        compact_value = _strip_ruc_noise(_compact_course_text("".join(raw_tokens)))
        course_tokens: list[str] = []
        for token in raw_tokens:
            if course_tokens and _looks_like_teacher_token(token):
                break
            course_tokens.append(token)
        if course_tokens:
            compact_value = _strip_ruc_noise(_compact_course_text("".join(course_tokens)))
    if not compact_value:
        return None, detected_term
    return compact_value[:128], detected_term


def _strip_ruc_noise(value: str) -> str:
    value = value.strip(" ：:-")
    value = value.replace("课程名称", "")
    value = value.replace("学分绩点", "")
    value = value.replace("学分", "")
    value = value.replace("成绩", "")
    return value.strip(" ：:-")


def _strip_ruc_course_property_tokens(tokens: list[str]) -> tuple[list[str], bool]:
    for start_index in range(len(tokens)):
        suffix = _compact_course_text("".join(tokens[start_index:]))
        if suffix in _RUC_COURSE_PROPERTY_LABELS:
            return tokens[:start_index], True
    return tokens, False


def _looks_like_teacher_token(token: str) -> bool:
    compact = _compact_course_text(token).strip(",，")
    if not compact:
        return False
    if re.fullmatch(r"[\u4e00-\u9fff]{2,4}", compact):
        return True
    if re.fullmatch(r"[\u4e00-\u9fff]{1,4}(?:[,，][\u4e00-\u9fff]{1,4})+", compact):
        return True
    return False


def _ruc_term_code(year_range: str, season: str) -> str:
    start_year = year_range.split("-", 1)[0]
    season_code = {
        "春季": "SPRING",
        "夏季": "SUMMER",
        "秋季": "FALL",
        "冬季": "WINTER",
    }.get(season, season.upper())
    return f"{start_year}-{season_code}"


def _compact_course_text(value: str) -> str:
    return re.sub(r"\s+", "", value).strip()


def _safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


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
    if normalized in {"A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"}:
        return True
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
