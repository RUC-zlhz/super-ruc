"""report 服务层 — FR-014 学业缺口 / FR-016 运营看板。

FR-014 原则：
- 输出明确的学分缺口与未满足模块清单，不输出"可以毕业"。
- 如果培养方案缺失或成绩数据为空 → data_warnings 明确提示。
- 使用 CourseEquivalence 做等价折算（ratio × 实际学分）。

FR-016：
- 按状态/类型聚合 requests / notices / workflows。不暴露个人敏感字段。
"""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.service import build_audit_detail, log_action
from app.auth import repository as auth_repo
from app.auth.models import Student, User
from app.auth.role_codes import normalize_role_code, normalize_role_codes
from app.auth.scopes import StudentScopeSet, split_student_scope_codes, student_in_scope
from app.core.cache import cache_get_text, cache_set_text
from app.core.config import settings
from app.core.exceptions import BizError, NotFoundError, PermissionError
from app.core.sql import order_by_nulls_last_desc
from app.core.storage import put_object
from app.exchange import repository as exchange_repo
from app.exchange.models import (
    BATCH_STATUS_COMMITTED,
    BATCH_STATUS_VALIDATED,
    IMPORT_TYPE_TRANSCRIPT_PDF_REVIEW,
    ROW_RESULT_SKIPPED,
    ROW_SEVERITY_WARN,
    CourseEquivalence,
    CourseOffering,
    CurriculumModule,
    CurriculumPlan,
    StudentCourseRecord,
)
from app.notice.models import Notice, NoticeDelivery, NoticeDeliveryBatch
from app.report.schemas import (
    AcademicGapAggregateItem,
    AcademicGapResult,
    AcademicModuleGap,
    KVMetric,
    NoticeSummary,
    OverviewResult,
    RequestSummary,
    TranscriptPdfCandidateCourse,
    TranscriptPdfReviewCommitIn,
    TranscriptPdfReviewCommitResult,
    TranscriptPdfUploadResult,
    WorkflowSummary,
)
from app.report.transcript_pdf import analyze_transcript_pdf, candidate_to_dict
from app.workflow.models import (
    REQUEST_STATUS_APPROVED,
    REQUEST_STATUS_DRAFT,
    REQUEST_STATUS_IN_REVIEW,
    REQUEST_STATUS_REJECTED,
    REQUEST_STATUS_SUBMITTED,
    REQUEST_STATUS_WITHDRAWN,
    WORKFLOW_NODE_DONE,
    WORKFLOW_NODE_OVERDUE,
    WORKFLOW_NODE_PENDING,
    Request,
    RequestType,
    StudentWorkflow,
    StudentWorkflowNode,
    WorkflowTemplate,
)

logger = logging.getLogger(__name__)

_REPORT_GLOBAL_ROLES = {"SUPER_ADMIN", "COLLEGE_LEADER"}
_REPORT_SCOPED_ROLES = {
    "COUNSELOR",
    "HEAD_TEACHER",
    "YOUTH_LEAGUE_TEACHER",
    "PARTY_BUILD_TEACHER",
}


async def _report_scope_for_viewer(
    db: AsyncSession,
    *,
    viewer_user_id: int,
    viewer_roles: list[str],
) -> StudentScopeSet | None:
    roles = set(normalize_role_codes(viewer_roles))
    if roles & _REPORT_GLOBAL_ROLES:
        return None
    scoped_roles = roles & _REPORT_SCOPED_ROLES
    if not scoped_roles:
        return StudentScopeSet()

    rows = await auth_repo.list_user_roles(db, viewer_user_id)
    scope_codes = [
        row.scope_code
        for row in rows
        if normalize_role_code(row.role_code) in scoped_roles and row.scope_code
    ]
    return split_student_scope_codes(scope_codes)


def _apply_report_student_scope(stmt, scope: StudentScopeSet | None):
    if scope is None:
        return stmt
    if scope.is_empty():
        return None
    scope_conds = []
    if scope.class_codes:
        scope_conds.append(Student.class_code.in_(sorted(scope.class_codes)))
    if scope.major_codes:
        scope_conds.append(Student.major_code.in_(sorted(scope.major_codes)))
    if scope.grade_codes:
        scope_conds.append(Student.grade_code.in_(sorted(scope.grade_codes)))
    if scope.legacy_codes:
        legacy = sorted(scope.legacy_codes)
        scope_conds.extend(
            [
                Student.class_code.in_(legacy),
                Student.major_code.in_(legacy),
                Student.grade_code.in_(legacy),
            ]
        )
    return stmt.where(or_(*scope_conds)) if scope_conds else None

# ============================================================
# FR-014 学业缺口
# ============================================================
_TRANSCRIPT_PDF_MAX_BYTES = 10 * 1024 * 1024
_TERM_CODE_PATTERN = re.compile(r"(\d{4})-(SPRING|SUMMER|FALL|WINTER)")
_BEIJING_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
_TRANSCRIPT_RECOMMENDATION_LIMIT = 5
_TRANSCRIPT_MATCH_DEFAULT_VERSION = "2024-default"
_TRANSCRIPT_MATCH_MIN_SCORE = 0.72
_TRANSCRIPT_MATCH_EXCLUDED_MAJOR_CODES = {"源文件全量课程池"}
_TRANSCRIPT_NAME_NOISE_RE = re.compile(r"[\s\-_—·•,，.。:：;；、/\\|]+")
_TRANSCRIPT_BRACKET_RE = re.compile(r"[\\(（【\\[].*?[\\)）】\\]]")


@dataclass(slots=True)
class _TranscriptCourseCatalogEntry:
    course_code: str
    course_name: str
    credits: float | None
    grade_codes: set[str]
    major_codes: set[str]
    module_names: set[str]
    plan_names: set[str]
    aliases: set[str]


def _generate_transcript_pdf_batch_no() -> str:
    return f"IM-TPDF-{datetime.now(UTC).strftime('%y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def _safe_filename(filename: str | None) -> str:
    value = (filename or "transcript.pdf").strip() or "transcript.pdf"
    value = value.replace("\\", "_").replace("/", "_")
    if not value.lower().endswith(".pdf"):
        value = f"{value}.pdf"
    return value[:180]


def _normalize_term_code(term_code: str | None) -> str | None:
    if term_code is None:
        return None
    normalized = term_code.strip().upper()
    if not normalized or not _TERM_CODE_PATTERN.fullmatch(normalized):
        raise BizError(
            "term_code 格式必须为 YYYY-SPRING|SUMMER|FALL|WINTER",
            code=42210,
            http_status=422,
            data={"term_code": term_code},
        )
    return normalized


def _derive_current_recommendation_term_code(now: datetime | None = None) -> str:
    current = (now or datetime.now(UTC)).astimezone(_BEIJING_TZ)
    year = current.year
    month = current.month
    if month == 1:
        return f"{year - 1}-WINTER"
    if 2 <= month < 7:
        return f"{year - 1}-SPRING"
    if 7 <= month < 9:
        return f"{year - 1}-SUMMER"
    return f"{year}-FALL"


def _effective_recommendation_term_code(term_code: str | None) -> str:
    explicit = _normalize_term_code(term_code)
    if explicit:
        return explicit
    configured = (settings.ACADEMIC_CURRENT_TERM_CODE or "").strip()
    if configured:
        normalized = _normalize_term_code(configured)
        assert normalized is not None
        return normalized
    return _derive_current_recommendation_term_code()


def _iter_module_courses(raw: Any) -> list[dict[str, Any]]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


def _split_code_filter(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {item.strip() for item in re.split(r"[,，;；、\s]+", raw) if item.strip()}


def _code_filter_matches(raw: str | None, value: str | None) -> bool:
    codes = _split_code_filter(raw)
    if not codes:
        return True
    if not value:
        return False
    return value.strip() in codes


def _offering_visible_to_student(offering: CourseOffering, student: Student) -> bool:
    return _code_filter_matches(offering.major_codes, student.major_code) and _code_filter_matches(
        offering.grade_codes,
        student.grade_code,
    )


def _course_name_from_curriculum(course: dict[str, Any], code: str) -> str:
    return str(course.get("name") or course.get("course_name") or code).strip()


def _opening_term_hint(course: dict[str, Any]) -> str | None:
    hint = str(course.get("opening_term") or "").strip()
    return hint or None


def _normalize_transcript_course_code(value: str | None) -> str:
    return unicodedata.normalize("NFKC", (value or "")).strip().upper()


def _normalize_transcript_course_name(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", (value or "")).strip().upper()
    text = _TRANSCRIPT_NAME_NOISE_RE.sub("", text)
    return text


def _build_transcript_course_aliases(value: str | None) -> set[str]:
    original = unicodedata.normalize("NFKC", (value or "")).strip().upper()
    if not original:
        return set()
    alias_inputs = {
        original,
        _TRANSCRIPT_BRACKET_RE.sub("", original),
    }
    return {
        normalized
        for item in alias_inputs
        if (normalized := _normalize_transcript_course_name(item))
    }


def _transcript_name_bigram_set(value: str) -> set[str]:
    if len(value) < 2:
        return {value} if value else set()
    return {value[index : index + 2] for index in range(len(value) - 1)}


def _transcript_name_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    ratio = SequenceMatcher(None, left, right).ratio()
    if left in right or right in left:
        ratio = max(ratio, 0.93)
    left_bigrams = _transcript_name_bigram_set(left)
    right_bigrams = _transcript_name_bigram_set(right)
    union = left_bigrams | right_bigrams
    jaccard = (len(left_bigrams & right_bigrams) / len(union)) if union else 0.0
    return max(ratio, ratio * 0.65 + jaccard * 0.35)


async def _load_transcript_course_catalog(
    db: AsyncSession,
    *,
    student: Student,
) -> dict[str, _TranscriptCourseCatalogEntry]:
    catalog: dict[str, _TranscriptCourseCatalogEntry] = {}
    plans: list[CurriculumPlan] = []
    seen_plan_ids: set[int] = set()

    if student.grade_code and student.major_code:
        student_plan_stmt = (
            select(CurriculumPlan)
            .where(
                CurriculumPlan.is_active.is_(True),
                CurriculumPlan.grade_code == student.grade_code,
                CurriculumPlan.major_code == student.major_code,
            )
            .options(selectinload(CurriculumPlan.modules))
            .order_by(*order_by_nulls_last_desc(CurriculumPlan.effective_from))
            .limit(1)
        )
        student_plan = (await db.execute(student_plan_stmt)).scalar_one_or_none()
        if student_plan is not None:
            plans.append(student_plan)
            seen_plan_ids.add(student_plan.id)

    default_plans_stmt = (
        select(CurriculumPlan)
        .where(
            CurriculumPlan.is_active.is_(True),
            CurriculumPlan.version_label == _TRANSCRIPT_MATCH_DEFAULT_VERSION,
            CurriculumPlan.major_code.notin_(sorted(_TRANSCRIPT_MATCH_EXCLUDED_MAJOR_CODES)),
        )
        .options(selectinload(CurriculumPlan.modules))
        .order_by(CurriculumPlan.grade_code.asc(), CurriculumPlan.major_code.asc())
    )
    default_plans = (await db.execute(default_plans_stmt)).scalars().all()
    for plan in default_plans:
        if plan.id in seen_plan_ids:
            continue
        plans.append(plan)
        seen_plan_ids.add(plan.id)

    for plan in plans:
        grade_code = (plan.grade_code or "").strip()
        major_code = (plan.major_code or "").strip()
        plan_name = (plan.plan_name or "").strip()
        for module in plan.modules:
            module_name = (module.module_name or "").strip()
            for course in _iter_module_courses(module.courses):
                code = _normalize_transcript_course_code(str(course.get("code") or ""))
                name = str(course.get("name") or "").strip()
                if not code or not name:
                    continue
                entry = catalog.get(code)
                if entry is None:
                    credits_raw = course.get("credits")
                    credits = None if credits_raw in (None, "") else float(credits_raw)
                    entry = _TranscriptCourseCatalogEntry(
                        course_code=code,
                        course_name=name,
                        credits=credits,
                        grade_codes=set(),
                        major_codes=set(),
                        module_names=set(),
                        plan_names=set(),
                        aliases=set(),
                    )
                    catalog[code] = entry
                if grade_code:
                    entry.grade_codes.add(grade_code)
                if major_code:
                    entry.major_codes.add(major_code)
                if module_name:
                    entry.module_names.add(module_name)
                if plan_name:
                    entry.plan_names.add(plan_name)
                entry.aliases.update(_build_transcript_course_aliases(name))
    return catalog


def _score_transcript_course_match(
    candidate: dict[str, Any],
    entry: _TranscriptCourseCatalogEntry,
    *,
    student: Student,
) -> tuple[float, str] | None:
    candidate_code = _normalize_transcript_course_code(str(candidate.get("course_code") or ""))
    candidate_name_aliases = _build_transcript_course_aliases(str(candidate.get("course_name") or ""))

    if candidate_code and candidate_code == entry.course_code:
        score = 1.0
        reasons = ["课程编码精确匹配"]
    else:
        best_score = 0.0
        best_reason: str | None = None
        if not candidate_name_aliases:
            return None
        for candidate_alias in candidate_name_aliases:
            for course_alias in entry.aliases:
                if candidate_alias == course_alias:
                    best_score = 0.98
                    best_reason = "课程名称精确匹配"
                    break
                if candidate_alias in course_alias or course_alias in candidate_alias:
                    if best_score < 0.93:
                        best_score = 0.93
                        best_reason = "课程名称包含匹配"
                similarity = _transcript_name_similarity(candidate_alias, course_alias)
                if similarity > best_score:
                    best_score = similarity
                    best_reason = "课程名称相似匹配"
            if best_score >= 0.98:
                break
        if best_score < _TRANSCRIPT_MATCH_MIN_SCORE:
            return None
        score = best_score
        reasons = [best_reason or "课程名称相似匹配"]

    credits_raw = candidate.get("credits")
    candidate_credits = None if credits_raw in (None, "") else float(credits_raw)
    if candidate_credits is not None and entry.credits is not None:
        diff = abs(candidate_credits - entry.credits)
        if diff < 0.01:
            score += 0.03
            reasons.append("学分一致")
        elif diff > 0.51:
            score -= 0.08

    student_major_code = (student.major_code or "").strip()
    if student_major_code and student_major_code in entry.major_codes:
        score += 0.03
        reasons.append("命中学生专业方案")
    student_grade_code = (student.grade_code or "").strip()
    if student_grade_code and student_grade_code in entry.grade_codes:
        score += 0.02

    return min(score, 1.0), " + ".join(reasons)


def _attach_transcript_course_recommendations(
    candidate_rows: list[dict[str, Any]],
    *,
    catalog: dict[str, _TranscriptCourseCatalogEntry],
    student: Student,
) -> list[dict[str, Any]]:
    enriched_rows: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        enriched = dict(candidate)
        ranked: list[tuple[float, str, dict[str, Any]]] = []
        for code, entry in catalog.items():
            matched = _score_transcript_course_match(enriched, entry, student=student)
            if matched is None:
                continue
            score, reason = matched
            ranked.append(
                (
                    score,
                    code,
                    {
                        "course_code": entry.course_code,
                        "course_name": entry.course_name,
                        "credits": entry.credits,
                        "match_score": round(score, 4),
                        "match_reason": reason,
                        "major_codes": sorted(entry.major_codes),
                        "module_names": sorted(entry.module_names),
                    },
                )
            )
        ranked.sort(key=lambda item: (-item[0], item[1]))
        enriched["course_recommendations"] = [
            payload for _, _, payload in ranked[:_TRANSCRIPT_RECOMMENDATION_LIMIT]
        ]
        enriched_rows.append(enriched)
    return enriched_rows


async def upload_transcript_pdf_for_review(
    db: AsyncSession,
    *,
    student_id: int,
    operator_id: int,
    operator_role: str | None,
    filename: str | None,
    content: bytes,
    content_type: str | None,
) -> TranscriptPdfUploadResult:
    """学生上传成绩单 PDF 的最小闭环：存文件、建核验批次、不写正式成绩。"""
    student = (await db.execute(select(Student).where(Student.id == student_id))).scalar_one_or_none()
    if student is None:
        raise NotFoundError("学生不存在")
    if not content:
        raise BizError("成绩单 PDF 文件为空", code=40070)
    max_bytes = min(settings.UPLOAD_MAX_SIZE_BYTES, _TRANSCRIPT_PDF_MAX_BYTES)
    if len(content) > max_bytes:
        raise BizError(
            f"成绩单 PDF 文件超过 {max_bytes // 1024 // 1024} MB 上限",
            code=41310,
            http_status=413,
        )
    if not content[:1024].lstrip().startswith(b"%PDF"):
        raise BizError("仅支持上传 PDF 格式的成绩单文件", code=40071)

    safe_name = _safe_filename(filename)
    checksum = hashlib.sha256(content).hexdigest()
    object_bucket = settings.MINIO_BUCKET_ATTACHMENT
    object_key = f"transcripts/pdf-review/{student.id}/{uuid.uuid4().hex}_{safe_name}"
    try:
        put_object(
            bucket=object_bucket,
            object_key=object_key,
            data=content,
            length=len(content),
            content_type=content_type or "application/pdf",
        )
    except Exception as e:
        logger.exception("Transcript PDF object storage upload failed")
        raise BizError("成绩单 PDF 上传失败，请稍后重试或联系管理员", code=50072, http_status=500) from e

    analysis = analyze_transcript_pdf(
        content,
        student_no=student.student_no,
        student_name=student.full_name,
    )
    candidate_rows = [candidate_to_dict(candidate) for candidate in analysis.candidate_courses]
    catalog = await _load_transcript_course_catalog(db, student=student)
    candidate_rows = _attach_transcript_course_recommendations(
        candidate_rows,
        catalog=catalog,
        student=student,
    )
    warnings = list(analysis.data_warnings)
    if not catalog:
        warnings.append("当前未加载可用于课程匹配的培养方案课程库，教师需手工填写课程代码。")

    batch = await exchange_repo.create_batch(
        db,
        batch_no=_generate_transcript_pdf_batch_no(),
        import_type=IMPORT_TYPE_TRANSCRIPT_PDF_REVIEW,
        filename=safe_name,
        object_bucket=object_bucket,
        object_key=object_key,
        file_size=len(content),
        mime_type=content_type or "application/pdf",
        operator_id=operator_id,
        operator_role=operator_role,
    )

    row_no = 1
    for warning in warnings:
        await exchange_repo.add_batch_row(
            db,
            batch_id=batch.id,
            row_no=row_no,
            severity=ROW_SEVERITY_WARN,
            result=ROW_RESULT_SKIPPED,
            field_name="data_warnings",
            message=warning,
            raw_data={"warning": warning},
        )
        row_no += 1
    for candidate in candidate_rows:
        await exchange_repo.add_batch_row(
            db,
            batch_id=batch.id,
            row_no=row_no,
            severity=ROW_SEVERITY_WARN,
            result=ROW_RESULT_SKIPPED,
            field_name="parsed_courses",
            message="PDF 文本层疑似课程记录，仅供人工核验，不写入正式成绩。",
            raw_data=candidate,
        )
        row_no += 1

    await exchange_repo.finalize_batch(
        db,
        batch,
        status=BATCH_STATUS_VALIDATED,
        total_rows=row_no - 1,
        ok_rows=0,
        warn_rows=row_no - 1,
        fatal_rows=0,
        summary={
            "source": "STUDENT_TRANSCRIPT_PDF",
            "review_required": True,
            "formal_records_written": 0,
            "student_id": student.id,
            "student_no": student.student_no,
            "student_name": student.full_name,
            "sha256": checksum,
            "parsed_text_chars": len(analysis.extracted_text),
            "parsed_courses_count": len(candidate_rows),
            "candidate_courses": candidate_rows,
            "data_warnings": warnings,
            "text_preview": analysis.extracted_text[:1000],
        },
    )
    await log_action(
        db,
        event_type="REPORT",
        entity_code="TRANSCRIPT_PDF",
        action="UPLOAD_TRANSCRIPT_PDF_REVIEW",
        entity_id=batch.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail=build_audit_detail(
            target={
                "student_id": student.id,
                "student_no": student.student_no,
                "filename": safe_name,
            },
            metrics={
                "file_size": len(content),
                "parsed_text_chars": len(analysis.extracted_text),
                "parsed_courses_count": len(candidate_rows),
                "formal_records_written": 0,
            },
            refs=[{"object_bucket": object_bucket, "object_key": object_key}],
        ),
    )
    await db.commit()
    await db.refresh(batch)

    return TranscriptPdfUploadResult(
        upload_id=batch.id,
        batch_no=batch.batch_no,
        status="PENDING_REVIEW",
        student_no=student.student_no,
        student_name=student.full_name,
        filename=batch.filename,
        file_size=len(content),
        mime_type=batch.mime_type,
        object_key=batch.object_key,
        parsed_text_chars=len(analysis.extracted_text),
        parsed_courses_count=len(candidate_rows),
        parsed_courses=[TranscriptPdfCandidateCourse(**candidate) for candidate in candidate_rows],
        review_required=True,
        formal_records_written=0,
        data_warnings=warnings,
        uploaded_at=batch.finished_at or datetime.now(UTC),
    )


async def commit_transcript_pdf_review(
    db: AsyncSession,
    batch_id: int,
    payload: TranscriptPdfReviewCommitIn,
    *,
    operator_id: int,
    operator_role: str | None,
) -> TranscriptPdfReviewCommitResult:
    """教师人工核验 PDF 候选课程后写入正式成绩。"""
    batch = await exchange_repo.get_batch(db, batch_id)
    if batch is None:
        raise NotFoundError("成绩单 PDF 核验批次不存在")
    if batch.import_type != IMPORT_TYPE_TRANSCRIPT_PDF_REVIEW:
        raise BizError("该批次不是成绩单 PDF 核验批次", code=40073)
    if batch.status == BATCH_STATUS_COMMITTED:
        raise BizError("该成绩单 PDF 核验批次已提交", code=40074)
    if batch.status != BATCH_STATUS_VALIDATED:
        raise BizError(f"批次状态 {batch.status} 不可提交核验结果", code=40075)
    if not payload.records:
        raise BizError("请至少选择一条核验后的课程记录", code=40076)

    summary = dict(batch.summary or {})
    student_id = int(summary.get("student_id") or 0)
    student = await db.get(Student, student_id) if student_id else None
    if student is None:
        raise NotFoundError("核验批次对应的学生不存在")

    written = 0
    for record in payload.records:
        course_code = (record.course_code or "").strip()
        course_name = (record.course_name or "").strip()
        if not course_code or not course_name:
            raise BizError("核验课程必须包含课程编码和课程名称", code=40077)
        term_code = _normalize_term_code(record.term_code)
        await exchange_repo.upsert_student_course_record(
            db,
            {
                "student_id": student.id,
                "term_code": term_code,
                "course_code": course_code,
                "course_name": course_name,
                "credits": float(record.credits or 0),
                "course_type": None,
                "score": record.score,
                "grade_letter": record.grade_letter,
                "pass_flag": bool(record.pass_flag),
                "imported_batch_id": batch.id,
                "note": record.note or payload.note or "成绩单 PDF 人工核验写入",
            },
        )
        written += 1

    summary["formal_records_written"] = written
    summary["reviewed_by"] = operator_id
    summary["reviewed_at"] = datetime.now(UTC).isoformat()
    summary["review_note"] = payload.note
    batch.summary = summary
    if payload.note:
        batch.note = payload.note
    await exchange_repo.mark_batch_committed(db, batch)
    await log_action(
        db,
        event_type="REPORT",
        entity_code="TRANSCRIPT_PDF",
        action="COMMIT_TRANSCRIPT_PDF_REVIEW",
        entity_id=batch.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail=build_audit_detail(
            target={"student_id": student.id, "student_no": student.student_no},
            metrics={"formal_records_written": written},
        ),
    )
    await db.commit()
    await db.refresh(batch)
    return TranscriptPdfReviewCommitResult(
        batch_id=batch.id,
        batch_no=batch.batch_no,
        status=batch.status,
        student_id=student.id,
        student_no=student.student_no,
        formal_records_written=written,
        committed_at=batch.finished_at or datetime.now(UTC),
    )


async def compute_academic_gap(
    db: AsyncSession,
    student_id: int,
    *,
    term_code: str | None = None,
) -> AcademicGapResult:
    student = (await db.execute(select(Student).where(Student.id == student_id))).scalar_one_or_none()
    if student is None:
        raise NotFoundError("学生不存在")

    data_warnings: list[str] = []
    recommendation_term_code = _effective_recommendation_term_code(term_code)

    plan = None
    if student.grade_code and student.major_code:
        stmt = (
            select(CurriculumPlan)
            .where(
                CurriculumPlan.grade_code == student.grade_code,
                CurriculumPlan.major_code == student.major_code,
                CurriculumPlan.is_active.is_(True),
            )
            .order_by(*order_by_nulls_last_desc(CurriculumPlan.effective_from))
            .limit(1)
        )
        plan = (await db.execute(stmt)).scalar_one_or_none()

    if plan is None:
        data_warnings.append("未找到该学生对应的培养方案（grade_code + major_code）；")
        result = AcademicGapResult(
            student_no=student.student_no,
            student_name=student.full_name,
            grade_code=student.grade_code,
            major_code=student.major_code,
            recommendation_term_code=recommendation_term_code,
            data_warnings=data_warnings,
            generated_at=datetime.now(UTC),
        )
        result.credits_gap = _compute_gap_value(result)
        result.risk_level = _derive_risk_level(result)
        result.conclusion_text = _build_academic_gap_conclusion(result)
        return result

    modules = (
        (
            await db.execute(
                select(CurriculumModule)
                .where(CurriculumModule.plan_id == plan.id)
                .order_by(CurriculumModule.sort_order.asc())
            )
        )
        .scalars()
        .all()
    )

    records = (
        (
            await db.execute(
                select(StudentCourseRecord).where(
                    StudentCourseRecord.student_id == student_id,
                    StudentCourseRecord.pass_flag.is_(True),
                )
            )
        )
        .scalars()
        .all()
    )

    if not records:
        data_warnings.append("暂无已通过的课程记录；所有模块标记为缺口以供人工核验。")

    equivs = (
        (
            await db.execute(
                select(CourseEquivalence).where(
                    CourseEquivalence.is_active.is_(True),
                    (
                        (CourseEquivalence.grade_code == student.grade_code)
                        | (CourseEquivalence.grade_code.is_(None))
                    ),
                    (
                        (CourseEquivalence.major_code == student.major_code)
                        | (CourseEquivalence.major_code.is_(None))
                    ),
                )
            )
        )
        .scalars()
        .all()
    )
    equiv_map: dict[str, list[tuple[str, float]]] = {}
    for e in equivs:
        equiv_map.setdefault(e.source_course_code, []).append((e.target_course_code, float(e.ratio or 1.0)))

    credit_buckets: list[dict[str, Any]] = []
    total_passed_credits = 0.0
    for r in records:
        credits = float(r.credits or 0)
        total_passed_credits += credits
        coverage = {r.course_code: credits}
        for target, ratio in equiv_map.get(r.course_code, []):
            coverage[target] = max(coverage.get(target, 0.0), credits * ratio)
        credit_buckets.append(
            {
                "course_code": r.course_code,
                "remaining": credits,
                "coverage": coverage,
            }
        )

    module_gaps: list[AcademicModuleGap] = []
    total_earned = 0.0
    flexible_credit_balance = total_passed_credits
    for m in modules:
        allowed_codes: list[str] = []
        seen_allowed_codes: set[str] = set()
        for c in _iter_module_courses(m.courses):
            code = c.get("code")
            if code and str(code) not in seen_allowed_codes:
                allowed_codes.append(str(code))
                seen_allowed_codes.add(str(code))
        module_earned = 0.0
        passed: list[str] = []
        if allowed_codes:
            required = float(m.credits_required or 0)
            for code in allowed_codes:
                for bucket in credit_buckets:
                    if module_earned >= required:
                        break
                    available = min(
                        float(bucket["remaining"]),
                        float(bucket["coverage"].get(code, 0.0)),
                    )
                    # 修复 Logic Bug: 避免贪婪消耗超出模块所需学分，导致溢出学分被困住无法给后续模块（如自由选修）使用
                    available = min(available, required - module_earned)
                    if available <= 0:
                        continue
                    bucket["remaining"] = max(float(bucket["remaining"]) - available, 0.0)
                    module_earned += available
                    real_code = str(bucket["course_code"])
                    if real_code not in passed:
                        passed.append(real_code)
            flexible_credit_balance = sum(float(bucket["remaining"]) for bucket in credit_buckets)
        else:
            required = float(m.credits_required or 0)
            module_earned = min(required, flexible_credit_balance)
            flexible_credit_balance = max(flexible_credit_balance - module_earned, 0.0)

            # 修复 Logic Bug: 必须同步从 credit_buckets 中扣除，否则下一个带白名单的模块会重新 sum 导致学分双重计算
            deduct_left = module_earned
            for bucket in credit_buckets:
                if deduct_left <= 0:
                    break
                b_rem = float(bucket["remaining"])
                if b_rem > 0:
                    deducted = min(b_rem, deduct_left)
                    bucket["remaining"] = max(b_rem - deducted, 0.0)
                    deduct_left -= deducted

            data_warnings.append(f"模块 {m.module_code} 未配置课程白名单，已按未归属已修学分粗略抵扣。")

        module_earned = round(module_earned, 2)
        required = float(m.credits_required or 0)
        gap = max(required - module_earned, 0.0)
        total_earned += module_earned
        module_gaps.append(
            AcademicModuleGap(
                module_code=m.module_code,
                module_name=m.module_name,
                module_type=m.module_type,
                credits_required=required,
                credits_earned=module_earned,
                credits_gap=round(gap, 2),
                passed_courses=passed,
                note=m.note,
            )
        )

    # 建议课程：真实开课优先；无开课表或部分课程缺少开课记录时，补充“培养方案候选”但显式标明非本学期开课。
    ranked_suggestions: list[tuple[int, float, int, int, str, dict[str, Any]]] = []
    offered = (
        (
            await db.execute(
                select(CourseOffering).where(
                    CourseOffering.is_active.is_(True),
                    CourseOffering.term_code == recommendation_term_code,
                )
            )
        )
        .scalars()
        .all()
    )
    offer_map = {o.course_code: o for o in offered if _offering_visible_to_student(o, student)}
    if not offered:
        data_warnings.append(
            f"当前未配置 {recommendation_term_code} 本学期开课数据，已改为返回培养方案候选课程；"
            "这些候选不能代表本学期实际开课、容量或时间安排。"
        )
    module_map = {module.module_code: module for module in modules}
    module_gap_map = {gap.module_code: gap.credits_gap for gap in module_gaps}
    module_priority_map = {
        "REQUIRED": 0,
        "PRACTICE": 1,
        "GENERAL": 2,
        "ELECTIVE": 3,
    }
    used_curriculum_fallback = False
    for module_order, gap in enumerate(module_gaps):
        if gap.credits_gap <= 0:
            continue
        module = module_map.get(gap.module_code)
        if module is None:
            continue
        module_priority = module_priority_map.get(module.module_type, 9)
        for course in _iter_module_courses(module.courses):
            code = str(course.get("code") or "").strip()
            if not code or code in gap.passed_courses:
                continue
            offering = offer_map.get(code)
            course_warnings: list[str] = []
            opening_hint = _opening_term_hint(course)
            if offering is not None:
                rank_score = 60
                term_value = offering.term_code
                course_name = offering.course_name
                credits = float(offering.credits or course.get("credits") or 0)
                course_type = offering.course_type or module.module_type
                capacity = offering.capacity
                capacity_status = "已配置" if capacity is not None else "数据未配置"
                if capacity is not None:
                    rank_score += 10
                schedule_status = f"{recommendation_term_code} 本学期开课"
                recommendation_basis = "CURRENT_TERM_OFFERING"
                recommendation_basis_label = "本学期开课"
                is_current_term_offering = True
                if capacity is None:
                    course_warnings.append("容量数据未配置")
                course_warnings.extend(["先修要求数据未配置", "时间冲突数据未配置", "学生偏好数据未配置"])
                data_status = "PARTIAL" if course_warnings else "COMPLETE"
                teacher = offering.teacher
            else:
                used_curriculum_fallback = True
                rank_score = 25 + (5 if opening_hint else 0)
                term_value = None
                course_name = _course_name_from_curriculum(course, code)
                credits = float(course.get("credits") or 0)
                course_type = str(course.get("course_type") or module.module_type)
                capacity = None
                capacity_status = "无本学期开课数据"
                schedule_status = f"未确认 {recommendation_term_code} 开课"
                recommendation_basis = "CURRICULUM_CANDIDATE"
                recommendation_basis_label = "培养方案候选"
                is_current_term_offering = False
                teacher = None
                course_warnings.extend(
                    [
                        f"未找到 {recommendation_term_code} 本学期开课记录",
                        "不能确认容量、上课时间、先修要求或本学期是否可选",
                    ]
                )
                data_status = "REFERENCE_ONLY"
            ranked_suggestions.append(
                (
                    rank_score,
                    module_gap_map.get(gap.module_code, 0.0),
                    module_priority,
                    module_order,
                    code,
                    {
                        "module_code": gap.module_code,
                        "module_name": gap.module_name,
                        "course_code": code,
                        "course_name": course_name,
                        "credits": credits,
                        "term_code": term_value,
                        "course_type": course_type,
                        "capacity": capacity,
                        "capacity_status": capacity_status,
                        "teacher": teacher,
                        "opening_term_hint": opening_hint,
                        "schedule_status": schedule_status,
                        "prerequisite_status": "数据未配置",
                        "conflict_status": "数据未配置",
                        "preference_status": "数据未配置",
                        "rank_score": rank_score,
                        "recommendation_basis": recommendation_basis,
                        "recommendation_basis_label": recommendation_basis_label,
                        "is_current_term_offering": is_current_term_offering,
                        "data_status": data_status,
                        "data_warnings": course_warnings,
                        "reason": (
                            f"模块 {gap.module_name} 尚有 {format(gap.credits_gap, '.1f')} 学分差额；"
                            f"依据：{recommendation_basis_label}"
                        ),
                    },
                )
            )
    if used_curriculum_fallback and offered:
        data_warnings.append(
            f"部分缺口课程缺少 {recommendation_term_code} 本学期开课记录，已补充培养方案候选课程；"
            "候选课程需以教务开课表和老师审核为准。"
        )
    if not ranked_suggestions:
        data_warnings.append("当前缺口模块缺少课程清单或可匹配开课记录，暂无法生成选课参考。")
    ranked_suggestions.sort(key=lambda item: (-item[0], -item[1], item[2], item[3], item[4]))
    suggested = [item for _, _, _, _, _, item in ranked_suggestions]

    result = AcademicGapResult(
        student_no=student.student_no,
        student_name=student.full_name,
        grade_code=student.grade_code,
        major_code=student.major_code,
        plan_id=plan.id,
        plan_name=plan.plan_name,
        total_credits_required=float(plan.total_credits_required or 0),
        total_credits_earned=round(total_earned, 2),
        modules=module_gaps,
        suggested_courses=suggested[:30],
        recommendation_term_code=recommendation_term_code,
        data_warnings=data_warnings,
        generated_at=datetime.now(UTC),
    )
    result.credits_gap = _compute_gap_value(result)
    result.risk_level = _derive_risk_level(result)
    result.conclusion_text = _build_academic_gap_conclusion(result)
    return result


def _compute_gap_value(result: AcademicGapResult) -> float | None:
    if result.total_credits_required is None:
        return None
    return round(
        max(result.total_credits_required - result.total_credits_earned, 0.0),
        2,
    )


def _derive_risk_level(result: AcademicGapResult) -> str:
    gap = _compute_gap_value(result)
    if gap is None:
        return "HIGH" if result.data_warnings else "MEDIUM"
    if gap <= 0 and not result.data_warnings:
        return "LOW"
    if result.total_credits_required and result.total_credits_required > 0:
        ratio = gap / result.total_credits_required
    else:
        ratio = 1.0 if gap > 0 else 0.0
    if gap >= 6 or ratio >= 0.3:
        return "HIGH"
    return "MEDIUM"


def _build_academic_gap_conclusion(result: AcademicGapResult) -> str:
    gap = _compute_gap_value(result)
    if gap is None:
        return "当前缺少匹配培养方案，无法形成学分差额结论。"
    if gap <= 0 and not result.data_warnings:
        return "按当前已核验成绩与培养方案口径，未发现总学分差额。"
    if gap <= 0:
        return "按当前数据未发现总学分差额，但存在数据提示，需人工复核后确认。"
    module_count = sum(1 for item in result.modules if item.credits_gap > 0)
    return f"按当前已核验成绩与培养方案口径，仍有 {gap:.1f} 学分缺口，涉及 {module_count} 个模块。"


async def list_academic_gap_overview(
    db: AsyncSession,
    *,
    keyword: str | None,
    grade_code: str | None,
    major_code: str | None,
    risk_level: str | None,
    term_code: str | None,
    page: int,
    page_size: int,
    viewer_user_id: int | None = None,
    viewer_roles: list[str] | None = None,
) -> tuple[list[AcademicGapAggregateItem], int]:
    stmt = select(Student).where(Student.deleted_at.is_(None))
    if viewer_user_id is not None and viewer_roles is not None:
        scope = await _report_scope_for_viewer(
            db,
            viewer_user_id=viewer_user_id,
            viewer_roles=viewer_roles,
        )
        scoped_stmt = _apply_report_student_scope(stmt, scope)
        if scoped_stmt is None:
            return [], 0
        stmt = scoped_stmt
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Student.student_no.ilike(like),
                Student.full_name.ilike(like),
            )
        )
    if grade_code:
        stmt = stmt.where(Student.grade_code == grade_code)
    if major_code:
        stmt = stmt.where(Student.major_code == major_code)

    # 先计算满足基础条件的总人数
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total_students_count = (await db.execute(total_stmt)).scalar_one()

    if total_students_count == 0:
        return [], 0

    # 修复崩溃类 Bug: 取消全量内存计算，改为仅在当前分页内进行学业缺口计算
    # 这里我们通过学号和 ID 进行稳定排序后分页。
    # 由于不进行全量计算就无法得知精确的 risk_level 和 credits_gap，
    # 我们如果遇到 risk_level 过滤，目前只能通过逐页向后扫描的方式来满足过滤条件，
    # 为了防止死循环或超时，我们设定一个扫描上限。但在没有 risk_level 过滤时，直接走数据库分页。

    desired_risk = risk_level.upper() if risk_level else None

    if not desired_risk:
        # 没有 risk_level 过滤时，直接数据库分页，极大提升性能
        start = max(page - 1, 0) * page_size
        paged_students = (
            (
                await db.execute(
                    stmt.order_by(Student.student_no.asc(), Student.id.asc()).offset(start).limit(page_size)
                )
            )
            .scalars()
            .all()
        )

        items: list[AcademicGapAggregateItem] = []
        for student in paged_students:
            result = await compute_academic_gap(db, student.id, term_code=term_code)
            current_risk = _derive_risk_level(result)
            gap = _compute_gap_value(result)
            item = AcademicGapAggregateItem(
                student_id=student.id,
                student_no=result.student_no,
                student_name=result.student_name,
                grade_code=result.grade_code,
                major_code=result.major_code,
                total_credits_required=result.total_credits_required,
                total_credits_earned=result.total_credits_earned,
                credits_gap=gap,
                risk_level=current_risk,
                conclusion_text=_build_academic_gap_conclusion(result),
                data_warnings=result.data_warnings,
                generated_at=result.generated_at,
            )
            items.append(item)

        return items, total_students_count

    # 存在 risk_level 过滤时，必须返回过滤后的精准 total，避免前端分页失真。
    # 风险等级依赖 compute_academic_gap，当前只能按基础条件分块计算。
    items: list[AcademicGapAggregateItem] = []
    chunk_size = 100
    offset = 0
    target_start_index = max(page - 1, 0) * page_size
    matched_count = 0

    while offset < total_students_count:
        chunk_students = (
            (
                await db.execute(
                    stmt.order_by(Student.student_no.asc(), Student.id.asc()).offset(offset).limit(chunk_size)
                )
            )
            .scalars()
            .all()
        )

        if not chunk_students:
            break

        offset += chunk_size

        for student in chunk_students:
            result = await compute_academic_gap(db, student.id, term_code=term_code)
            current_risk = _derive_risk_level(result)

            if current_risk != desired_risk:
                continue

            matched_count += 1
            if matched_count <= target_start_index:
                # 还没到当前页的起始位置，跳过
                continue

            gap = _compute_gap_value(result)
            item = AcademicGapAggregateItem(
                student_id=student.id,
                student_no=result.student_no,
                student_name=result.student_name,
                grade_code=result.grade_code,
                major_code=result.major_code,
                total_credits_required=result.total_credits_required,
                total_credits_earned=result.total_credits_earned,
                credits_gap=gap,
                risk_level=current_risk,
                conclusion_text=_build_academic_gap_conclusion(result),
                data_warnings=result.data_warnings,
                generated_at=result.generated_at,
            )
            items.append(item)

            if len(items) > page_size:
                items = items[:page_size]

    return items, matched_count


async def ensure_academic_gap_student_visible(
    db: AsyncSession,
    *,
    student_id: int,
    viewer_user_id: int,
    viewer_roles: list[str],
) -> None:
    scope = await _report_scope_for_viewer(
        db,
        viewer_user_id=viewer_user_id,
        viewer_roles=viewer_roles,
    )
    if scope is None:
        return
    if scope.is_empty():
        raise PermissionError("无权查看该学生学业缺口", code=40306)
    student = await db.get(Student, student_id)
    if student is None:
        raise NotFoundError(f"学生不存在：{student_id}")
    if not student_in_scope(student, scope):
        raise PermissionError("无权查看该学生学业缺口", code=40306)


# ============================================================
# FR-016 运营看板
# ============================================================
def _term_code_date_range(term_code: str | None) -> tuple[datetime, datetime] | None:
    normalized = _normalize_term_code(term_code)
    if normalized is None:
        return None
    match = _TERM_CODE_PATTERN.fullmatch(normalized)
    assert match is not None
    year = int(match.group(1))
    season = match.group(2)
    ranges = {
        "SPRING": ((2, 1), (7, 1)),
        "SUMMER": ((7, 1), (9, 1)),
        "FALL": ((9, 1), (1, 1)),
        "WINTER": ((1, 1), (2, 1)),
    }
    (start_month, start_day), (end_month, end_day) = ranges[season]

    # 修复 Logic Bug: 春/夏/冬学期均属于跨年后的日历年
    start_year = year if season == "FALL" else year + 1
    end_year = year + 1 if season == "FALL" else year + 1

    return (
        datetime(start_year, start_month, start_day, tzinfo=UTC),
        datetime(end_year, end_month, end_day, tzinfo=UTC),
    )


async def build_overview(
    db: AsyncSession,
    *,
    term_code: str | None = None,
    viewer_user_id: int | None = None,
    viewer_roles: list[str] | None = None,
) -> OverviewResult:
    """看板概览（带 Redis 缓存，TTL = REPORT_OVERVIEW_CACHE_TTL_SECONDS）。

    缓存键包含 viewer_user_id —— 概览数据按查看者数据范围过滤，**绝不可跨用户共享**，
    否则会造成越权数据泄露。缓存故障时自动降级为直算（见 app.core.cache）。
    陈旧度上界为 TTL（默认 60s），适合看板这类对短延迟容忍度高的聚合视图。
    """
    cache_key = (
        "report:overview:v1:"
        f"{viewer_user_id if viewer_user_id is not None else 'all'}:"
        f"{_normalize_term_code(term_code) or 'default'}"
    )
    cached = await cache_get_text(cache_key)
    if cached is not None:
        parsed = _parse_cached_overview(cached)
        if parsed is not None:
            return parsed

    result = await _build_overview_uncached(
        db,
        term_code=term_code,
        viewer_user_id=viewer_user_id,
        viewer_roles=viewer_roles,
    )
    await cache_set_text(
        cache_key,
        result.model_dump_json(),
        settings.REPORT_OVERVIEW_CACHE_TTL_SECONDS,
    )
    return result


def _parse_cached_overview(raw: str) -> OverviewResult | None:
    try:
        return OverviewResult.model_validate_json(raw)
    except Exception as exc:  # noqa: BLE001 — 缓存损坏/schema 漂移则直算覆盖
        logger.warning("overview cache parse failed, recomputing: %s", exc)
        return None


async def _build_overview_uncached(
    db: AsyncSession,
    *,
    term_code: str | None = None,
    viewer_user_id: int | None = None,
    viewer_roles: list[str] | None = None,
) -> OverviewResult:
    normalized_term_code = _normalize_term_code(term_code)
    term_range = _term_code_date_range(normalized_term_code)

    scope = None
    if viewer_user_id is not None and viewer_roles is not None:
        scope = await _report_scope_for_viewer(
            db, viewer_user_id=viewer_user_id, viewer_roles=viewer_roles
        )
        if scope is not None and scope.is_empty():
            return OverviewResult(
                term_code=normalized_term_code,
                metrics=[],
                requests=[],
                notices=NoticeSummary(
                    total_notices=0,
                    published_notices=0,
                    total_batches=0,
                    total_deliveries=0,
                    sent=0,
                    failed=0,
                    skipped=0,
                    read=0,
                ),
                workflows=[],
                generated_at=datetime.now(UTC),
            )

    # --- requests 按类型 × 状态聚合 ---
    stmt = select(
        Request.type_code,
        Request.status,
        func.count().label("cnt"),
    )
    if scope is not None:
        stmt = stmt.join(User, Request.applicant_user_id == User.id).join(Student, User.student_id == Student.id)
        stmt = _apply_report_student_scope(stmt, scope)
    stmt = stmt.group_by(Request.type_code, Request.status)
    if term_range:
        stmt = stmt.where(Request.created_at >= term_range[0], Request.created_at < term_range[1])
    grouped = (await db.execute(stmt)).all()

    types = (await db.execute(select(RequestType))).scalars().all()
    type_map = {t.code: t for t in types}

    summary_map: dict[str, RequestSummary] = {}
    for type_code, status, cnt in grouped:
        s = summary_map.setdefault(
            type_code,
            RequestSummary(
                type_code=type_code,
                type_name=(type_map.get(type_code).name if type_code in type_map else type_code),
            ),
        )
        if status == REQUEST_STATUS_DRAFT:
            s.draft += cnt
        elif status == REQUEST_STATUS_SUBMITTED:
            s.submitted += cnt
        elif status == REQUEST_STATUS_IN_REVIEW:
            s.in_review += cnt
        elif status == REQUEST_STATUS_APPROVED:
            s.approved += cnt
        elif status == REQUEST_STATUS_REJECTED:
            s.rejected += cnt
        elif status == REQUEST_STATUS_WITHDRAWN:
            s.withdrawn += cnt
        s.total += cnt
    requests_summary = list(summary_map.values())

    # --- notices ---
    notice_count_stmt = select(func.count(func.distinct(Notice.id))).select_from(Notice)
    published_notice_stmt = select(func.count(func.distinct(Notice.id))).select_from(Notice).where(Notice.status == "PUBLISHED")
    batch_count_stmt = select(func.count(func.distinct(NoticeDeliveryBatch.id))).select_from(NoticeDeliveryBatch)
    delivery_stmt = select(NoticeDelivery.status, func.count(func.distinct(NoticeDelivery.id))).select_from(NoticeDelivery)

    if scope is not None:
        notice_count_stmt = notice_count_stmt.join(NoticeDelivery, NoticeDelivery.notice_id == Notice.id).join(Student, NoticeDelivery.student_id == Student.id)
        notice_count_stmt = _apply_report_student_scope(notice_count_stmt, scope)

        published_notice_stmt = published_notice_stmt.join(NoticeDelivery, NoticeDelivery.notice_id == Notice.id).join(Student, NoticeDelivery.student_id == Student.id)
        published_notice_stmt = _apply_report_student_scope(published_notice_stmt, scope)

        batch_count_stmt = batch_count_stmt.join(NoticeDelivery, NoticeDelivery.batch_id == NoticeDeliveryBatch.id).join(Student, NoticeDelivery.student_id == Student.id)
        batch_count_stmt = _apply_report_student_scope(batch_count_stmt, scope)

        delivery_stmt = delivery_stmt.join(Student, NoticeDelivery.student_id == Student.id)
        delivery_stmt = _apply_report_student_scope(delivery_stmt, scope)

    delivery_stmt = delivery_stmt.group_by(NoticeDelivery.status)

    if term_range:
        notice_count_stmt = notice_count_stmt.where(
            Notice.created_at >= term_range[0], Notice.created_at < term_range[1]
        )
        published_notice_stmt = published_notice_stmt.where(
            Notice.created_at >= term_range[0], Notice.created_at < term_range[1]
        )
        batch_count_stmt = batch_count_stmt.where(
            NoticeDeliveryBatch.started_at >= term_range[0],
            NoticeDeliveryBatch.started_at < term_range[1],
        )
        delivery_stmt = delivery_stmt.where(
            NoticeDelivery.created_at >= term_range[0],
            NoticeDelivery.created_at < term_range[1],
        )
    total_notices = (await db.execute(notice_count_stmt)).scalar_one()
    published_notices = (await db.execute(published_notice_stmt)).scalar_one()
    total_batches = (await db.execute(batch_count_stmt)).scalar_one()
    delivery_rows = (await db.execute(delivery_stmt)).all()
    sent = failed = skipped = read = 0
    total_deliveries = 0
    for st, c in delivery_rows:
        total_deliveries += c
        if st == "SENT":
            sent += c
        elif st == "FAILED":
            failed += c
        elif st == "SKIPPED":
            skipped += c
        elif st == "READ":
            read += c
    notices_summary = NoticeSummary(
        total_notices=total_notices,
        published_notices=published_notices,
        total_batches=total_batches,
        total_deliveries=total_deliveries,
        sent=sent,
        failed=failed,
        skipped=skipped,
        read=read,
    )

    # --- workflows ---
    templates = (await db.execute(select(WorkflowTemplate))).scalars().all()
    workflows: list[WorkflowSummary] = []
    for t in templates:
        workflow_count_stmt = (
            select(func.count()).select_from(StudentWorkflow).where(StudentWorkflow.template_id == t.id)
        )
        if scope is not None:
            workflow_count_stmt = workflow_count_stmt.join(Student, StudentWorkflow.student_id == Student.id)
            workflow_count_stmt = _apply_report_student_scope(workflow_count_stmt, scope)
        if term_range:
            workflow_count_stmt = workflow_count_stmt.where(
                StudentWorkflow.started_at >= term_range[0],
                StudentWorkflow.started_at < term_range[1],
            )
        total_students_workflow = (await db.execute(workflow_count_stmt)).scalar_one()
        
        node_stmt = (
            select(StudentWorkflowNode.status, func.count())
            .join(StudentWorkflow, StudentWorkflow.id == StudentWorkflowNode.workflow_id)
            .where(StudentWorkflow.template_id == t.id)
        )
        if scope is not None:
            node_stmt = node_stmt.join(Student, StudentWorkflow.student_id == Student.id)
            node_stmt = _apply_report_student_scope(node_stmt, scope)
        node_stmt = node_stmt.group_by(StudentWorkflowNode.status)
        if term_range:
            node_stmt = node_stmt.where(
                StudentWorkflowNode.created_at >= term_range[0],
                StudentWorkflowNode.created_at < term_range[1],
            )
        node_rows = (await db.execute(node_stmt)).all()
        node_map = dict(node_rows)
        workflows.append(
            WorkflowSummary(
                template_code=t.code,
                template_name=t.name,
                kind=t.kind,
                total_students=total_students_workflow,
                nodes_pending=node_map.get(WORKFLOW_NODE_PENDING, 0),
                nodes_overdue=node_map.get(WORKFLOW_NODE_OVERDUE, 0),
                nodes_done=node_map.get(WORKFLOW_NODE_DONE, 0),
            )
        )

    # --- 顶部指标 ---
    student_count_stmt = select(func.count()).select_from(Student).where(Student.deleted_at.is_(None))
    if scope is not None:
        student_count_stmt = _apply_report_student_scope(student_count_stmt, scope)
    total_students_metric = (await db.execute(student_count_stmt)).scalar_one()
    
    total_requests_all = sum(s.total for s in requests_summary)
    pending_approvals = sum(s.submitted + s.in_review for s in requests_summary)
    metrics = [
        KVMetric(key="students", label="在籍学生", value=total_students_metric),
        KVMetric(key="requests", label="申请总量", value=total_requests_all),
        KVMetric(key="pending_approvals", label="待审批", value=pending_approvals),
        KVMetric(key="notices", label="通知条数", value=total_notices),
        KVMetric(key="deliveries", label="投递条数", value=total_deliveries),
    ]

    return OverviewResult(
        term_code=normalized_term_code,
        metrics=metrics,
        requests=requests_summary,
        notices=notices_summary,
        workflows=workflows,
        generated_at=datetime.now(UTC),
    )
