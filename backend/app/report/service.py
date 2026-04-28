"""report 服务层 — FR-014 学业缺口 / FR-016 运营看板。

FR-014 原则（C-05 弱结论）：
- 输出"未满足模块"清单，不输出"可以毕业"。
- 如果培养方案缺失或成绩数据为空 → data_warnings 明确提示。
- 使用 CourseEquivalence 做等价折算（ratio × 实际学分）。

FR-016：
- 按状态/类型聚合 requests / notices / workflows。不暴露个人敏感字段。
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student
from app.core.exceptions import NotFoundError
from app.core.sql import order_by_nulls_last_desc
from app.exchange.models import (
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
    WorkflowSummary,
)
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


# ============================================================
# FR-014 学业缺口
# ============================================================
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
        return AcademicGapResult(
            student_no=student.student_no,
            student_name=student.full_name,
            grade_code=student.grade_code,
            major_code=student.major_code,
            data_warnings=data_warnings,
            generated_at=datetime.now(UTC),
        )

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
    for r in records:
        passed_course_codes.add(r.course_code)
        earned[r.course_code] = earned.get(r.course_code, 0) + float(r.credits or 0)
        for target, ratio in equiv_map.get(r.course_code, []):
            earned[target] = earned.get(target, 0) + float(r.credits or 0) * ratio

    module_gaps: list[AcademicModuleGap] = []
    total_earned = 0.0
    for m in modules:
        allowed_codes: set[str] = set()
        if m.courses:
            for c in m.courses:
                code = c.get("code") if isinstance(c, dict) else None
                if code:
                    allowed_codes.add(str(code))
        module_earned = 0.0
        passed: list[str] = []
        if allowed_codes:
            for code in allowed_codes:
                if code in earned:
                    module_earned += earned[code]
                    if code in passed_course_codes:
                        passed.append(code)
        else:
            # 无白名单：按 module_type 作为粗口径（通识/实践允许任何通过课程）
            # 这里仅按全部记录累加作为参考，并给出 warning
            if not allowed_codes:
                module_earned = 0.0
                data_warnings.append(
                    f"模块 {m.module_code} 未配置课程白名单，缺口计算仅供参考。"
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

    # 建议课程：从当前有效开课中选取模块下尚缺学分的课程
    suggested: list[dict[str, Any]] = []
    offered = (await db.execute(
        select(CourseOffering).where(CourseOffering.is_active.is_(True))
    )).scalars().all()
    offer_map = {o.course_code: o for o in offered}
    for gap in module_gaps:
        if gap.credits_gap <= 0:
            continue
        for m in modules:
            if m.module_code != gap.module_code or not m.courses:
                continue
            for c in m.courses:
                code = c.get("code") if isinstance(c, dict) else None
                if not code or code in gap.passed_courses:
                    continue
                o = offer_map.get(str(code))
                if o is None:
                    continue
                suggested.append({
                    "module_code": gap.module_code,
                    "course_code": o.course_code,
                    "course_name": o.course_name,
                    "credits": float(o.credits or 0),
                    "term_code": o.term_code,
                    "course_type": o.course_type,
                })

    return AcademicGapResult(
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
async def build_overview(db: AsyncSession) -> OverviewResult:
    # --- requests 按类型 × 状态聚合 ---
    stmt = (
        select(
            Request.type_code,
            Request.status,
            func.count().label("cnt"),
        )
        .group_by(Request.type_code, Request.status)
    )
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
    total_notices = (await db.execute(
        select(func.count()).select_from(Notice)
    )).scalar_one()
    published_notices = (await db.execute(
        select(func.count()).select_from(Notice).where(Notice.status == "PUBLISHED")
    )).scalar_one()
    total_batches = (await db.execute(
        select(func.count()).select_from(NoticeDeliveryBatch)
    )).scalar_one()
    delivery_rows = (await db.execute(
        select(NoticeDelivery.status, func.count()).group_by(NoticeDelivery.status)
    )).all()
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
        total_students = (await db.execute(
            select(func.count()).select_from(StudentWorkflow).where(
                StudentWorkflow.template_id == t.id
            )
        )).scalar_one()
        node_rows = (await db.execute(
            select(StudentWorkflowNode.status, func.count())
            .join(StudentWorkflow, StudentWorkflow.id == StudentWorkflowNode.workflow_id)
            .where(StudentWorkflow.template_id == t.id)
            .group_by(StudentWorkflowNode.status)
        )).all()
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
        metrics=metrics,
        requests=requests_summary,
        notices=notices_summary,
        workflows=workflows,
        generated_at=datetime.now(UTC),
    )
