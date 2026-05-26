"""report contract smoke — S1 canonical route/schema guardrails."""
from __future__ import annotations

from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student, User, UserRole
from app.core.security import create_token
from app.exchange.models import (
    IMPORT_TYPE_TRANSCRIPT_PDF_REVIEW,
    CourseEquivalence,
    CourseOffering,
    CurriculumModule,
    CurriculumPlan,
    ImportBatch,
    StudentCourseRecord,
)
from app.report import service as report_service
from app.report.transcript_pdf import TranscriptPdfAnalysis, TranscriptPdfCandidate
from app.workflow.models import Request, RequestType


async def _headers_for_role(
    db: AsyncSession,
    *,
    role_code: str,
    work_no: str,
    scope_code: str | None = None,
) -> dict[str, str]:
    user = User(work_no=work_no, display_name=f"report-{role_code}", is_active=True)
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_code=role_code, scope_code=scope_code))
    await db.commit()
    token = create_token(str(user.id), "access", extra_claims={"roles": [role_code]})
    return {"Authorization": f"Bearer {token}"}


async def _login_as_student(
    client: AsyncClient, db: AsyncSession, *, student_no: str, wx_code: str
) -> tuple[str, int]:
    stu = Student(
        student_no=student_no,
        full_name=f"report-{student_no}",
        grade_code="2022",
        major_code="CS",
        class_code="CS2201",
    )
    db.add(stu)
    await db.commit()
    await db.refresh(stu)
    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": wx_code,
            "student_no": student_no,
            "full_name": f"report-{student_no}",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"], stu.id


async def test_report_routes_use_canonical_contract(
    client: AsyncClient,
    db: AsyncSession,
    admin_client: AsyncClient,
) -> None:
    token, student_id = await _login_as_student(
        client, db, student_no="A100001", wx_code="wx_a100001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    plan = CurriculumPlan(
        grade_code="2022",
        major_code="CS",
        plan_name="2022 级计算机培养方案",
        version_label="2022-v1",
        total_credits_required=6,
        is_active=True,
    )
    db.add(plan)
    await db.flush()
    db.add_all(
        [
            CurriculumModule(
                plan_id=plan.id,
                module_code="CORE",
                module_name="核心课程",
                module_type="REQUIRED",
                credits_required=3,
                courses=[{"code": "CS101", "name": "程序设计", "credits": 3}],
                sort_order=1,
            ),
            CurriculumModule(
                plan_id=plan.id,
                module_code="PRACTICE",
                module_name="实践环节",
                module_type="PRACTICE",
                credits_required=3,
                courses=[{"code": "CS199", "name": "课程实践", "credits": 3}],
                sort_order=2,
            ),
        ]
    )
    db.add(
        StudentCourseRecord(
            student_id=student_id,
            term_code="2025-FALL",
            course_code="CS101",
            course_name="程序设计",
            credits=3,
            course_type="REQUIRED",
            pass_flag=True,
        )
    )
    db.add(
        CourseOffering(
            term_code="2025-FALL",
            course_code="CS199",
            course_name="课程实践",
            credits=3,
            course_type="PRACTICE",
            major_codes="CS",
            grade_codes="2022",
            is_active=True,
        )
    )
    await db.commit()

    academic_gap = await client.get(
        "/api/v1/report/academic-gap",
        headers=stu_headers,
        params={"term_code": "2025-FALL"},
    )
    assert academic_gap.status_code == 200, academic_gap.text
    data = academic_gap.json()["data"]
    assert data["plan_name"] == "2022 级计算机培养方案"
    assert data["total_credits_required"] == 6
    assert data["total_credits_earned"] == 3
    assert "gap_credits" not in data
    assert "generated_at" in data
    assert "disclaimer" in data
    assert data["recommendation_term_code"] == "2025-FALL"
    assert data["suggested_courses"]
    assert data["suggested_courses"][0]["course_code"] == "CS199"
    assert data["suggested_courses"][0]["recommendation_basis"] == "CURRENT_TERM_OFFERING"
    assert data["suggested_courses"][0]["is_current_term_offering"] is True
    assert "graduation" not in str(data["suggested_courses"][0]).lower()
    assert len(data["modules"]) == 2
    first_module = data["modules"][0]
    assert {"credits_required", "credits_earned", "credits_gap"} <= set(first_module)
    assert "min_credits" not in first_module
    assert "earned_credits" not in first_module
    assert "gap" not in first_module

    overview = await admin_client.get("/api/v1/admin/report/overview")
    assert overview.status_code == 200, overview.text
    overview_data = overview.json()["data"]
    assert set(overview_data) >= {"metrics", "requests", "notices", "workflows", "generated_at", "disclaimer"}
    assert "pending_requests" not in overview_data
    assert isinstance(overview_data["metrics"], list)
    assert isinstance(overview_data["requests"], list)
    assert isinstance(overview_data["workflows"], list)
    assert overview_data["notices"] is not None
    if overview_data["metrics"]:
        metric = overview_data["metrics"][0]
        assert {"key", "label", "value"} <= set(metric)

    request_type = RequestType(
        code="TERM_OVERVIEW",
        name="学期看板测试",
        category="OTHER",
        approver_roles="COUNSELOR",
    )
    db.add(request_type)
    await db.flush()
    applicant_user = (
        await db.execute(select(User).where(User.student_id == student_id))
    ).scalar_one()
    db.add(
        Request(
            request_no="REQ-TERM-2501",
            type_id=request_type.id,
            type_code=request_type.code,
            applicant_user_id=applicant_user.id,
            applicant_student_id=student_id,
            title="秋季事务",
            form_data={},
            status="SUBMITTED",
            created_at=datetime(2025, 10, 1, tzinfo=UTC),
        )
    )
    db.add(
        Request(
            request_no="REQ-TERM-2601",
            type_id=request_type.id,
            type_code=request_type.code,
            applicant_user_id=applicant_user.id,
            applicant_student_id=student_id,
            title="春季事务",
            form_data={},
            status="SUBMITTED",
            created_at=datetime(2026, 3, 1, tzinfo=UTC),
        )
    )
    await db.commit()

    fall_overview = await admin_client.get(
        "/api/v1/admin/report/overview",
        params={"term_code": "2025-FALL"},
    )
    assert fall_overview.status_code == 200, fall_overview.text
    fall_data = fall_overview.json()["data"]
    assert fall_data["term_code"] == "2025-FALL"
    term_summary = next(
        item for item in fall_data["requests"] if item["type_code"] == "TERM_OVERVIEW"
    )
    assert term_summary["total"] == 1

    invalid_term = await admin_client.get(
        "/api/v1/admin/report/overview",
        params={"term_code": "2025-AUTUMN"},
    )
    assert invalid_term.status_code == 422, invalid_term.text
    invalid_payload = invalid_term.json()
    assert invalid_payload["code"] == 42210
    assert "term_code" in invalid_payload["message"]

    admin_gap = await admin_client.get(
        f"/api/v1/admin/report/academic-gap/{student_id}",
        params={"term_code": "2025-FALL"},
    )
    assert admin_gap.status_code == 200, admin_gap.text
    admin_gap_data = admin_gap.json()["data"]
    assert admin_gap_data["student_no"] == "A100001"
    assert admin_gap_data["total_credits_required"] == 6
    assert admin_gap_data["modules"][0]["module_code"] == "CORE"


async def test_student_transcript_pdf_upload_creates_review_record_without_formal_grades(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    token, student_id = await _login_as_student(
        client, db, student_no="A100002", wx_code="wx_a100002"
    )
    headers = {"Authorization": f"Bearer {token}"}

    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    upload = await client.post(
        "/api/v1/report/transcript-pdf",
        headers=headers,
        files={"file": ("transcript.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 200, upload.text
    data = upload.json()["data"]
    assert data["status"] == "PENDING_REVIEW"
    assert data["review_required"] is True
    assert data["formal_records_written"] == 0
    assert data["data_warnings"]
    assert any("不会写入正式成绩" in warning for warning in data["data_warnings"])

    batch = await db.get(ImportBatch, data["upload_id"])
    assert batch is not None
    assert batch.import_type == IMPORT_TYPE_TRANSCRIPT_PDF_REVIEW
    assert batch.summary["review_required"] is True
    assert batch.summary["formal_records_written"] == 0
    assert batch.object_key

    records = (
        await db.execute(
            select(StudentCourseRecord).where(
                StudentCourseRecord.student_id == student_id
            )
        )
    ).scalars().all()
    assert records == []


async def test_student_transcript_pdf_upload_returns_course_recommendations(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch,
) -> None:
    token, student_id = await _login_as_student(
        client, db, student_no="A100004", wx_code="wx_a100004"
    )
    headers = {"Authorization": f"Bearer {token}"}

    plan = CurriculumPlan(
        grade_code="2022",
        major_code="CS",
        plan_name="2022 推荐匹配方案",
        version_label="teacher-v1",
        total_credits_required=3,
        is_active=True,
    )
    db.add(plan)
    await db.flush()
    db.add(
        CurriculumModule(
            plan_id=plan.id,
            module_code="CORE",
            module_name="专业核心课",
            module_type="REQUIRED",
            credits_required=3,
            courses=[{"code": "CS200", "name": "离散数学", "credits": 3}],
            sort_order=1,
        )
    )
    await db.commit()

    def _fake_analyze_transcript_pdf(*_args, **_kwargs) -> TranscriptPdfAnalysis:
        return TranscriptPdfAnalysis(
            extracted_text="离散数学 学分 3 成绩 92",
            data_warnings=[],
            candidate_courses=[
                TranscriptPdfCandidate(
                    line_no=1,
                    raw_text="离散数学 学分 3 成绩 92",
                    course_code=None,
                    course_name="离散数学",
                    credits=3,
                    term_code="2025-FALL",
                    score=92,
                    pass_flag=True,
                    confidence="HIGH",
                )
            ],
        )

    monkeypatch.setattr(report_service, "analyze_transcript_pdf", _fake_analyze_transcript_pdf)

    upload = await client.post(
        "/api/v1/report/transcript-pdf",
        headers=headers,
        files={"file": ("transcript.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
    )
    assert upload.status_code == 200, upload.text
    data = upload.json()["data"]
    assert data["parsed_courses_count"] == 1
    recommendations = data["parsed_courses"][0]["course_recommendations"]
    assert recommendations
    assert recommendations[0]["course_code"] == "CS200"
    assert recommendations[0]["course_name"] == "离散数学"
    assert "课程名称精确匹配" in recommendations[0]["match_reason"]

    batch = await db.get(ImportBatch, data["upload_id"])
    assert batch is not None
    assert batch.summary["candidate_courses"][0]["course_recommendations"][0]["course_code"] == "CS200"


async def test_student_transcript_pdf_upload_maps_object_storage_failure_to_biz_error(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch,
) -> None:
    token, student_id = await _login_as_student(
        client, db, student_no="A100003", wx_code="wx_a100003"
    )
    headers = {"Authorization": f"Bearer {token}"}

    def _broken_put_object(**_kwargs):
        raise RuntimeError("object storage unavailable")

    monkeypatch.setattr(report_service, "put_object", _broken_put_object)

    upload = await client.post(
        "/api/v1/report/transcript-pdf",
        headers=headers,
        files={"file": ("transcript.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
    )
    assert upload.status_code == 500, upload.text
    payload = upload.json()
    assert payload["code"] == 50072
    assert "成绩单 PDF 上传失败" in payload["message"]

    batch_rows = (
        await db.execute(
            select(ImportBatch).where(
                ImportBatch.import_type == IMPORT_TYPE_TRANSCRIPT_PDF_REVIEW
            )
        )
    ).scalars().all()
    assert batch_rows == []
    records = (
        await db.execute(
            select(StudentCourseRecord).where(
                StudentCourseRecord.student_id == student_id
            )
        )
    ).scalars().all()
    assert records == []


async def test_admin_academic_gap_aggregate_query_uses_items_meta_and_filters(
    db: AsyncSession,
    admin_client: AsyncClient,
) -> None:
    high_risk = Student(
        student_no="A200001",
        full_name="high-gap",
        grade_code="2022",
        major_code="CS",
        class_code="CS2201",
    )
    low_risk = Student(
        student_no="A200002",
        full_name="low-gap",
        grade_code="2022",
        major_code="CS",
        class_code="CS2201",
    )
    missing_plan = Student(
        student_no="A200003",
        full_name="missing-plan",
        grade_code="2022",
        major_code="MATH",
        class_code="MA2201",
    )
    db.add_all([high_risk, low_risk, missing_plan])
    await db.flush()

    plan = CurriculumPlan(
        grade_code="2022",
        major_code="CS",
        plan_name="2022 级计算机培养方案",
        version_label="2022-v2",
        total_credits_required=6,
        is_active=True,
    )
    db.add(plan)
    await db.flush()
    db.add_all(
        [
            CurriculumModule(
                plan_id=plan.id,
                module_code="CORE",
                module_name="核心课程",
                module_type="REQUIRED",
                credits_required=6,
                courses=[{"code": "CS201", "name": "算法设计", "credits": 6}],
                sort_order=1,
            ),
            StudentCourseRecord(
                student_id=low_risk.id,
                term_code="2025-FALL",
                course_code="CS201",
                course_name="算法设计",
                credits=6,
                course_type="REQUIRED",
                pass_flag=True,
            ),
        ]
    )
    await db.commit()

    listing = await admin_client.get(
        "/api/v1/admin/report/academic-gap",
        params={"grade_code": "2022", "page": 1, "page_size": 10},
    )
    assert listing.status_code == 200, listing.text
    payload = listing.json()["data"]
    assert set(payload) == {"items", "meta"}
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["size"] == 10
    assert payload["meta"]["total"] == 3
    items = payload["items"]
    assert {
        "student_id",
        "student_no",
        "student_name",
        "grade_code",
        "major_code",
        "total_credits_required",
        "total_credits_earned",
        "credits_gap",
        "data_warnings",
        "generated_at",
    } <= set(items[0])
    high_gap_item = next(item for item in items if item["student_no"] == "A200001")
    assert "modules" not in high_gap_item
    assert high_gap_item["credits_gap"] == 6
    missing_plan_item = next(item for item in items if item["student_no"] == "A200003")
    assert missing_plan_item["total_credits_required"] is None
    assert missing_plan_item["data_warnings"]

    high_only = await admin_client.get(
        "/api/v1/admin/report/academic-gap",
        params={"risk_level": "HIGH", "page": 1, "page_size": 10},
    )
    assert high_only.status_code == 200, high_only.text
    high_payload = high_only.json()["data"]
    assert high_payload["meta"]["total"] == 2
    high_items = high_payload["items"]
    assert {item["student_no"] for item in high_items} == {"A200001", "A200003"}

    keyword = await admin_client.get(
        "/api/v1/admin/report/academic-gap",
        params={"keyword": "low-gap", "page": 1, "page_size": 10},
    )
    assert keyword.status_code == 200, keyword.text
    keyword_items = keyword.json()["data"]["items"]
    assert len(keyword_items) == 1
    assert keyword_items[0]["student_no"] == "A200002"

    detail = await admin_client.get(
        f"/api/v1/admin/report/academic-gap/{high_risk.id}"
    )
    assert detail.status_code == 200, detail.text
    detail_data = detail.json()["data"]
    assert detail_data["student_no"] == "A200001"
    assert "disclaimer" in detail_data


async def test_admin_academic_gap_respects_teacher_scope(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    in_scope = Student(
        student_no="A210001",
        full_name="scope-in",
        grade_code="2022",
        major_code="CS",
        class_code="CS2201",
    )
    out_scope = Student(
        student_no="A210002",
        full_name="scope-out",
        grade_code="2022",
        major_code="CS",
        class_code="CS2202",
    )
    db.add_all([in_scope, out_scope])
    await db.commit()
    await db.refresh(in_scope)
    await db.refresh(out_scope)

    headers = await _headers_for_role(
        db,
        role_code="COUNSELOR",
        work_no="REPORT-SCOPE-COUNSELOR",
        scope_code="CLASS:CS2201",
    )

    listing = await client.get(
        "/api/v1/admin/report/academic-gap",
        headers=headers,
        params={"grade_code": "2022", "page": 1, "page_size": 10},
    )
    assert listing.status_code == 200, listing.text
    payload = listing.json()["data"]
    assert payload["meta"]["total"] == 1
    assert [item["student_no"] for item in payload["items"]] == ["A210001"]

    allowed_detail = await client.get(
        f"/api/v1/admin/report/academic-gap/{in_scope.id}",
        headers=headers,
    )
    assert allowed_detail.status_code == 200, allowed_detail.text

    denied_detail = await client.get(
        f"/api/v1/admin/report/academic-gap/{out_scope.id}",
        headers=headers,
    )
    assert denied_detail.status_code == 403, denied_detail.text


async def test_academic_gap_recommendations_only_use_requested_term(
    db: AsyncSession,
) -> None:
    student = Student(
        student_no="A220001",
        full_name="term-gap",
        grade_code="2022",
        major_code="CS",
        class_code="CS2201",
    )
    db.add(student)
    await db.flush()
    plan = CurriculumPlan(
        grade_code="2022",
        major_code="CS",
        plan_name="2022 学期过滤方案",
        version_label="2022-term-filter",
        total_credits_required=3,
        is_active=True,
    )
    db.add(plan)
    await db.flush()
    db.add_all(
        [
            CurriculumModule(
                plan_id=plan.id,
                module_code="CORE",
                module_name="核心课程",
                module_type="REQUIRED",
                credits_required=3,
                courses=[{"code": "CS-TERM", "name": "学期过滤课程", "credits": 3}],
                sort_order=1,
            ),
            CourseOffering(
                term_code="2025-SPRING",
                course_code="CS-TERM",
                course_name="本学期开课",
                credits=3,
                course_type="REQUIRED",
                is_active=True,
            ),
            CourseOffering(
                term_code="2025-FALL",
                course_code="CS-TERM",
                course_name="其他学期开课",
                credits=3,
                course_type="REQUIRED",
                is_active=True,
            ),
        ]
    )
    await db.commit()

    current = await report_service.compute_academic_gap(
        db,
        student.id,
        term_code="2025-SPRING",
    )
    assert current.recommendation_term_code == "2025-SPRING"
    assert [item["course_name"] for item in current.suggested_courses] == ["本学期开课"]
    assert current.suggested_courses[0]["recommendation_basis"] == "CURRENT_TERM_OFFERING"
    assert current.suggested_courses[0]["is_current_term_offering"] is True

    other = await report_service.compute_academic_gap(
        db,
        student.id,
        term_code="2025-SUMMER",
    )
    assert other.recommendation_term_code == "2025-SUMMER"
    assert [item["course_name"] for item in other.suggested_courses] == ["学期过滤课程"]
    assert other.suggested_courses[0]["term_code"] is None
    assert other.suggested_courses[0]["recommendation_basis"] == "CURRICULUM_CANDIDATE"
    assert other.suggested_courses[0]["is_current_term_offering"] is False
    assert all(item["course_name"] != "其他学期开课" for item in other.suggested_courses)
    assert any("培养方案候选课程" in warning for warning in other.data_warnings)


async def test_academic_gap_equivalent_course_consumes_credit_once(
    db: AsyncSession,
) -> None:
    student = Student(
        student_no="A200004",
        full_name="equiv-gap",
        grade_code="2022",
        major_code="CS",
        class_code="CS2201",
    )
    db.add(student)
    await db.flush()

    plan = CurriculumPlan(
        grade_code="2022",
        major_code="CS",
        plan_name="2022 等价课程测试方案",
        version_label="2022-equiv",
        total_credits_required=6,
        is_active=True,
    )
    db.add(plan)
    await db.flush()
    db.add_all(
        [
            CurriculumModule(
                plan_id=plan.id,
                module_code="MODULE_B",
                module_name="模块 B",
                module_type="REQUIRED",
                credits_required=3,
                courses=[{"code": "CS-B", "name": "等价目标 B", "credits": 3}],
                sort_order=1,
            ),
            CurriculumModule(
                plan_id=plan.id,
                module_code="MODULE_C",
                module_name="模块 C",
                module_type="REQUIRED",
                credits_required=3,
                courses=[{"code": "CS-C", "name": "等价目标 C", "credits": 3}],
                sort_order=2,
            ),
            CourseEquivalence(
                grade_code="2022",
                major_code="CS",
                source_course_code="CS-A",
                source_course_name="源课程 A",
                target_course_code="CS-B",
                target_course_name="等价目标 B",
                ratio=1,
                is_active=True,
            ),
            CourseEquivalence(
                grade_code="2022",
                major_code="CS",
                source_course_code="CS-A",
                source_course_name="源课程 A",
                target_course_code="CS-C",
                target_course_name="等价目标 C",
                ratio=1,
                is_active=True,
            ),
            StudentCourseRecord(
                student_id=student.id,
                term_code="2025-FALL",
                course_code="CS-A",
                course_name="源课程 A",
                credits=3,
                course_type="REQUIRED",
                pass_flag=True,
            ),
        ]
    )
    await db.commit()

    result = await report_service.compute_academic_gap(db, student.id)

    assert result.total_credits_required == 6
    assert result.total_credits_earned == 3
    assert result.credits_gap == 3
    modules = {item.module_code: item for item in result.modules}
    assert modules["MODULE_B"].credits_earned == 3
    assert modules["MODULE_C"].credits_earned == 0
    assert modules["MODULE_B"].passed_courses == ["CS-A"]


async def test_admin_academic_gap_rejects_invalid_pagination(
    admin_client: AsyncClient,
) -> None:
    for params in (
        {"page": 0, "page_size": 20},
        {"page": 1, "page_size": 0},
        {"page": 1, "page_size": 101},
    ):
        response = await admin_client.get("/api/v1/admin/report/academic-gap", params=params)
        assert response.status_code == 422, response.text
        assert response.json()["code"] == 42200
