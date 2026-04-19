"""report contract smoke — S1 canonical route/schema guardrails."""
from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student
from app.exchange.models import CurriculumModule, CurriculumPlan, StudentCourseRecord


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
        json={"code": wx_code, "student_no": student_no},
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
    await db.commit()

    academic_gap = await client.get("/api/v1/report/academic-gap", headers=stu_headers)
    assert academic_gap.status_code == 200, academic_gap.text
    data = academic_gap.json()["data"]
    assert data["plan_name"] == "2022 级计算机培养方案"
    assert data["total_credits_required"] == 6
    assert data["total_credits_earned"] == 3
    assert "gap_credits" not in data
    assert "generated_at" in data
    assert "disclaimer" in data
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

    admin_gap = await admin_client.get(f"/api/v1/admin/report/academic-gap/{student_id}")
    assert admin_gap.status_code == 200, admin_gap.text
    admin_gap_data = admin_gap.json()["data"]
    assert admin_gap_data["student_no"] == "A100001"
    assert admin_gap_data["total_credits_required"] == 6
    assert admin_gap_data["modules"][0]["module_code"] == "CORE"


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
    high_items = high_only.json()["data"]["items"]
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
