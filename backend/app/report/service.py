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
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import build_audit_detail, log_action
from app.auth.models import Student
from app.core.config import settings
from app.core.exceptions import BizError, NotFoundError
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

# ============================================================
# FR-014 学业缺口
# ============================================================
_TRANSCRIPT_PDF_MAX_BYTES = 10 * 1024 * 1024
_TERM_CODE_PATTERN = re.compile(r"(\d{4})-(SPRING|SUMMER|FALL|WINTER)")


def _generate_transcript_pdf_batch_no() -> str:
    return (
        f"IM-TPDF-{datetime.now(UTC).strftime('%y%m%d%H%M%S')}-"
        f"{uuid.uuid4().hex[:6].upper()}"
    )


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


def _iter_module_courses(raw: Any) -> list[dict[str, Any]]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


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
    student = (
        await db.execute(select(Student).where(Student.id == student_id))
    ).scalar_one_or_none()
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
    warnings = analysis.data_warnings

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
        parsed_courses=[
            TranscriptPdfCandidateCourse(**candidate) for candidate in candidate_rows
        ],
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
    db: AsyncSession, student_id: int
) -> AcademicGapResult:
    student = (await db.execute(
        select(Student).where(Student.id == student_id)
    )).scalar_one_or_none()
    if student is None:
        raise NotFoundError("学生不存在")

    data_warnings: list[str] = []

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
            data_warnings=data_warnings,
            generated_at=datetime.now(UTC),
        )
        result.credits_gap = _compute_gap_value(result)
        result.risk_level = _derive_risk_level(result)
        result.conclusion_text = _build_academic_gap_conclusion(result)
        return result

    modules = (await db.execute(
        select(CurriculumModule)
        .where(CurriculumModule.plan_id == plan.id)
        .order_by(CurriculumModule.sort_order.asc())
    )).scalars().all()

    records = (await db.execute(
        select(StudentCourseRecord).where(
            StudentCourseRecord.student_id == student_id,
            StudentCourseRecord.pass_flag.is_(True),
        )
    )).scalars().all()

    if not records:
        data_warnings.append("暂无已通过的课程记录；所有模块标记为缺口以供人工核验。")

    equivs = (await db.execute(
        select(CourseEquivalence).where(
            CourseEquivalence.is_active.is_(True),
            ((CourseEquivalence.grade_code == student.grade_code)
             | (CourseEquivalence.grade_code.is_(None))),
            ((CourseEquivalence.major_code == student.major_code)
             | (CourseEquivalence.major_code.is_(None))),
        )
    )).scalars().all()
    equiv_map: dict[str, list[tuple[str, float]]] = {}
    for e in equivs:
        equiv_map.setdefault(e.source_course_code, []).append(
            (e.target_course_code, float(e.ratio or 1.0))
        )

    # 展开一条成绩到它可以覆盖的 course_code 集合（原始 + 所有等价目标）
    # 同时记录该课程的"有效学分"
    earned: dict[str, float] = {}
    passed_course_codes: set[str] = set()
    total_passed_credits = 0.0
    for r in records:
        passed_course_codes.add(r.course_code)
        total_passed_credits += float(r.credits or 0)
        earned[r.course_code] = earned.get(r.course_code, 0) + float(r.credits or 0)
        for target, ratio in equiv_map.get(r.course_code, []):
            earned[target] = earned.get(target, 0) + float(r.credits or 0) * ratio

    module_gaps: list[AcademicModuleGap] = []
    total_earned = 0.0
    whitelist_earned_total = 0.0
    flexible_credit_balance = total_passed_credits
    for m in modules:
        allowed_codes: set[str] = set()
        for c in _iter_module_courses(m.courses):
            code = c.get("code")
            if code:
                allowed_codes.add(str(code))
        module_earned = 0.0
        passed: list[str] = []
        if allowed_codes:
            for code in allowed_codes:
                if code in earned:
                    module_earned += earned[code]
                    whitelist_earned_total += earned[code]
                    if code in passed_course_codes:
                        passed.append(code)
            flexible_credit_balance = max(total_passed_credits - whitelist_earned_total, 0.0)
        else:
            required = float(m.credits_required or 0)
            module_earned = min(required, flexible_credit_balance)
            flexible_credit_balance = max(flexible_credit_balance - module_earned, 0.0)
            data_warnings.append(
                f"模块 {m.module_code} 未配置课程白名单，已按未归属已修学分粗略抵扣。"
            )

        module_earned = round(module_earned, 2)
        required = float(m.credits_required or 0)
        gap = max(required - module_earned, 0.0)
        total_earned += module_earned
        module_gaps.append(AcademicModuleGap(
            module_code=m.module_code,
            module_name=m.module_name,
            module_type=m.module_type,
            credits_required=required,
            credits_earned=module_earned,
            credits_gap=round(gap, 2),
            passed_courses=passed,
            note=m.note,
        ))

    # 建议课程：缺口模块中的未修课程均返回；缺少开课/容量/课表/先修/偏好数据时显式提示。
    ranked_suggestions: list[tuple[int, float, int, int, str, dict[str, Any]]] = []
    offered = (await db.execute(
        select(CourseOffering).where(CourseOffering.is_active.is_(True))
    )).scalars().all()
    offer_map = {o.course_code: o for o in offered}
    if not offered:
        data_warnings.append("当前未配置有效开课数据，课程推荐仅按培养方案白名单列出候选。")
    module_map = {module.module_code: module for module in modules}
    module_gap_map = {gap.module_code: gap.credits_gap for gap in module_gaps}
    module_priority_map = {
        "REQUIRED": 0,
        "PRACTICE": 1,
        "GENERAL": 2,
        "ELECTIVE": 3,
    }
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
            rank_score = 0
            if offering is not None:
                rank_score += 50
                term_value = offering.term_code
                course_name = offering.course_name
                credits = float(offering.credits or course.get("credits") or 0)
                course_type = offering.course_type or module.module_type
                capacity = offering.capacity
                capacity_status = "已配置" if capacity is not None else "数据未配置"
                if capacity is not None:
                    rank_score += 10
                schedule_status = "已配置" if term_value else "数据未配置"
            else:
                term_value = course.get("opening_term")
                course_name = str(course.get("name") or code)
                credits = float(course.get("credits") or 0)
                course_type = module.module_type
                capacity = None
                capacity_status = "数据未配置"
                schedule_status = "实际开课数据未配置"
                course_warnings.append("实际开课数据未配置")
            if not term_value:
                course_warnings.append("开课学期数据未配置")
            if capacity is None:
                course_warnings.append("容量数据未配置")
            course_warnings.extend(["先修要求数据未配置", "时间冲突数据未配置", "学生偏好数据未配置"])
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
                        "schedule_status": schedule_status,
                        "prerequisite_status": "数据未配置",
                        "conflict_status": "数据未配置",
                        "preference_status": "数据未配置",
                        "rank_score": rank_score,
                        "data_status": "PARTIAL" if course_warnings else "COMPLETE",
                        "data_warnings": course_warnings,
                        "reason": f"模块 {gap.module_name} 尚有 {format(gap.credits_gap, '.1f')} 学分差额",
                    },
                )
            )
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
    page: int,
    page_size: int,
) -> tuple[list[AcademicGapAggregateItem], int]:
    stmt = select(Student).where(Student.deleted_at.is_(None))
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
    students = (await db.execute(stmt.order_by(Student.student_no.asc(), Student.id.asc()))).scalars().all()

    desired_risk = risk_level.upper() if risk_level else None
    rank_map = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    items: list[tuple[int, float, AcademicGapAggregateItem]] = []
    for student in students:
        result = await compute_academic_gap(db, student.id)
        current_risk = _derive_risk_level(result)
        if desired_risk and current_risk != desired_risk:
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
        gap_sort = gap if gap is not None else float("inf")
        items.append((rank_map.get(current_risk, 99), gap_sort, item))

    items.sort(key=lambda row: (row[0], -row[1], row[2].student_no, row[2].student_id))
    flattened = [item for _, _, item in items]
    total = len(flattened)
    start = max(page - 1, 0) * page_size
    end = start + page_size
    return flattened[start:end], total


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
    end_year = year + 1 if season == "FALL" else year
    return (
        datetime(year, start_month, start_day, tzinfo=UTC),
        datetime(end_year, end_month, end_day, tzinfo=UTC),
    )


async def build_overview(db: AsyncSession, *, term_code: str | None = None) -> OverviewResult:
    normalized_term_code = _normalize_term_code(term_code)
    term_range = _term_code_date_range(normalized_term_code)
    # --- requests 按类型 × 状态聚合 ---
    stmt = (
        select(
            Request.type_code,
            Request.status,
            func.count().label("cnt"),
        )
        .group_by(Request.type_code, Request.status)
    )
    if term_range:
        stmt = stmt.where(Request.created_at >= term_range[0], Request.created_at < term_range[1])
    grouped = (await db.execute(stmt)).all()

    types = (await db.execute(select(RequestType))).scalars().all()
    type_map = {t.code: t for t in types}

    summary_map: dict[str, RequestSummary] = {}
    for type_code, status, cnt in grouped:
        s = summary_map.setdefault(type_code, RequestSummary(
            type_code=type_code,
            type_name=(type_map.get(type_code).name if type_code in type_map else type_code),
        ))
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
    notice_count_stmt = select(func.count()).select_from(Notice)
    published_notice_stmt = notice_count_stmt.where(Notice.status == "PUBLISHED")
    batch_count_stmt = select(func.count()).select_from(NoticeDeliveryBatch)
    delivery_stmt = select(NoticeDelivery.status, func.count()).group_by(NoticeDelivery.status)
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
        sent=sent, failed=failed, skipped=skipped, read=read,
    )

    # --- workflows ---
    templates = (await db.execute(select(WorkflowTemplate))).scalars().all()
    workflows: list[WorkflowSummary] = []
    for t in templates:
        workflow_count_stmt = select(func.count()).select_from(StudentWorkflow).where(
            StudentWorkflow.template_id == t.id
        )
        if term_range:
            workflow_count_stmt = workflow_count_stmt.where(
                StudentWorkflow.started_at >= term_range[0],
                StudentWorkflow.started_at < term_range[1],
            )
        total_students = (await db.execute(workflow_count_stmt)).scalar_one()
        node_stmt = (
            select(StudentWorkflowNode.status, func.count())
            .join(StudentWorkflow, StudentWorkflow.id == StudentWorkflowNode.workflow_id)
            .where(StudentWorkflow.template_id == t.id)
            .group_by(StudentWorkflowNode.status)
        )
        if term_range:
            node_stmt = node_stmt.where(
                StudentWorkflowNode.created_at >= term_range[0],
                StudentWorkflowNode.created_at < term_range[1],
            )
        node_rows = (await db.execute(node_stmt)).all()
        node_map = dict(node_rows)
        workflows.append(WorkflowSummary(
            template_code=t.code,
            template_name=t.name,
            kind=t.kind,
            total_students=total_students,
            nodes_pending=node_map.get(WORKFLOW_NODE_PENDING, 0),
            nodes_overdue=node_map.get(WORKFLOW_NODE_OVERDUE, 0),
            nodes_done=node_map.get(WORKFLOW_NODE_DONE, 0),
        ))

    # --- 顶部指标 ---
    total_students = (await db.execute(
        select(func.count()).select_from(Student).where(Student.deleted_at.is_(None))
    )).scalar_one()
    total_requests_all = sum(s.total for s in requests_summary)
    pending_approvals = sum(
        s.submitted + s.in_review for s in requests_summary
    )
    metrics = [
        KVMetric(key="students", label="在籍学生", value=total_students),
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
