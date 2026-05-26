"""S47 cross-role linkage smoke.

This is intentionally broader than a single module regression: one student and
several teacher roles exercise the same DB state across notification delivery,
request approval, party workflow progress, profile visibility, academic report
scope, and honor publication.
"""
from __future__ import annotations

from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student, User, UserRole
from app.core.security import create_token
from app.exchange.models import CurriculumModule, CurriculumPlan, StudentCourseRecord


async def _create_student_and_login(
    client: AsyncClient,
    db: AsyncSession,
    *,
    student_no: str,
    full_name: str,
    grade_code: str = "2026",
    major_code: str = "CS",
    class_code: str = "CS2601",
    political_status: str = "入党申请人",
) -> tuple[dict[str, str], int]:
    student = Student(
        student_no=student_no,
        full_name=full_name,
        grade_code=grade_code,
        major_code=major_code,
        class_code=class_code,
        political_status=political_status,
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)

    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": f"wx_{student_no}",
            "student_no": student_no,
            "full_name": full_name,
        },
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}, student.id


async def _create_role_headers(
    db: AsyncSession,
    *,
    work_no: str,
    display_name: str,
    roles: list[tuple[str, str | None]],
) -> dict[str, str]:
    user = User(work_no=work_no, display_name=display_name, is_active=True)
    db.add(user)
    await db.flush()
    role_codes: list[str] = []
    for role_code, scope_code in roles:
        db.add(UserRole(user_id=user.id, role_code=role_code, scope_code=scope_code))
        if role_code not in role_codes:
            role_codes.append(role_code)
    await db.commit()
    token = create_token(str(user.id), "access", extra_claims={"roles": role_codes})
    return {"Authorization": f"Bearer {token}"}


async def _seed_curriculum_gap_data(db: AsyncSession, *, student_id: int) -> None:
    plan = CurriculumPlan(
        grade_code="2026",
        major_code="CS",
        plan_name="S47 计算机培养方案",
        version_label="2026-s47",
        total_credits_required=6,
        is_active=True,
    )
    db.add(plan)
    await db.flush()
    db.add_all(
        [
            CurriculumModule(
                plan_id=plan.id,
                module_code="S47_CORE",
                module_name="S47 核心课程",
                module_type="REQUIRED",
                credits_required=6,
                courses=[
                    {"code": "S47-101", "name": "S47 程序设计", "credits": 3},
                    {"code": "S47-102", "name": "S47 数据库", "credits": 3},
                ],
                sort_order=1,
            ),
            StudentCourseRecord(
                student_id=student_id,
                term_code="2026-FALL",
                course_code="S47-101",
                course_name="S47 程序设计",
                credits=3,
                course_type="REQUIRED",
                pass_flag=True,
            ),
        ]
    )
    await db.commit()


async def test_cross_role_student_teacher_linkage_smoke(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    student_headers, student_id = await _create_student_and_login(
        client,
        db,
        student_no="S470001",
        full_name="S47 联通学生",
    )
    await _seed_curriculum_gap_data(db, student_id=student_id)

    out_of_scope = Student(
        student_no="S470099",
        full_name="S47 范围外学生",
        grade_code="2026",
        major_code="EE",
        class_code="EE2601",
    )
    db.add(out_of_scope)
    await db.commit()

    admin_headers = await _create_role_headers(
        db,
        work_no="S47ADMIN",
        display_name="S47 超管",
        roles=[("SUPER_ADMIN", None)],
    )
    counselor_headers = await _create_role_headers(
        db,
        work_no="S47COUNSELOR",
        display_name="S47 辅导员",
        roles=[("COUNSELOR", "CLASS:CS2601")],
    )
    head_teacher_headers = await _create_role_headers(
        db,
        work_no="S47HEAD",
        display_name="S47 班主任",
        roles=[("HEAD_TEACHER", "CLASS:CS2601")],
    )
    party_teacher_headers = await _create_role_headers(
        db,
        work_no="S47PARTY",
        display_name="S47 党团教师",
        roles=[("PARTY_BUILD_TEACHER", "CLASS:CS2601")],
    )

    # 1. Teacher publishes an in-app notice; the scoped student receives and reads it.
    notice = await client.post(
        "/api/v1/admin/notices",
        headers=admin_headers,
        json={
            "title": "S47 班级联通通知",
            "body_md": "请完成 S47 联通 smoke 验证。",
            "summary": "S47 smoke",
            "category": "ACADEMIC",
            "target_rule": {"class_codes": ["CS2601"]},
            "target_summary": "CS2601",
            "channels": ["IN_APP"],
        },
    )
    assert notice.status_code == 200, notice.text
    notice_id = notice.json()["data"]["id"]
    publish = await client.post(
        f"/api/v1/admin/notices/{notice_id}/publish", headers=admin_headers
    )
    assert publish.status_code == 200, publish.text
    dispatch = await client.post(
        f"/api/v1/admin/notices/{notice_id}/dispatch",
        headers=admin_headers,
        json={},
    )
    assert dispatch.status_code == 200, dispatch.text
    assert dispatch.json()["data"]["target_count"] == 1

    inbox = await client.get("/api/v1/notices/inbox", headers=student_headers)
    assert inbox.status_code == 200, inbox.text
    inbox_items = inbox.json()["data"]["items"]
    assert [item["id"] for item in inbox_items] == [notice_id]
    delivery_id = inbox_items[0]["delivery_id"]
    mark_read = await client.post(
        f"/api/v1/notices/read/{delivery_id}", headers=student_headers
    )
    assert mark_read.status_code == 200, mark_read.text

    # 2. Student submits a request; scoped counselor sees, claims, and approves it.
    request_create = await client.post(
        "/api/v1/requests",
        headers=student_headers,
        json={
            "type_code": "LEAVE_PERSONAL",
            "title": "S47 请假申请",
            "form_data": {
                "reason": "联通 smoke",
                "start_date": "2026-05-26",
                "end_date": "2026-05-26",
                "leave_type": "事假",
            },
            "summary": "S47 跨角色申请",
        },
    )
    assert request_create.status_code == 200, request_create.text
    request_id = request_create.json()["data"]["id"]
    submit = await client.post(
        f"/api/v1/requests/{request_id}/submit", headers=student_headers
    )
    assert submit.status_code == 200, submit.text

    request_list = await client.get(
        "/api/v1/admin/requests",
        headers=counselor_headers,
        params={"status": "SUBMITTED"},
    )
    assert request_list.status_code == 200, request_list.text
    assert request_id in {item["id"] for item in request_list.json()["data"]["items"]}

    claim = await client.post(
        f"/api/v1/admin/requests/{request_id}/claim", headers=counselor_headers
    )
    assert claim.status_code == 200, claim.text
    approve = await client.post(
        f"/api/v1/admin/requests/{request_id}/approve",
        headers=counselor_headers,
        json={"comment": "S47 已核验"},
    )
    assert approve.status_code == 200, approve.text
    assert approve.json()["data"]["status"] == "APPROVED"

    my_requests = await client.get(
        "/api/v1/requests/my", headers=student_headers, params={"status": "APPROVED"}
    )
    assert my_requests.status_code == 200, my_requests.text
    assert request_id in {item["id"] for item in my_requests.json()["data"]["items"]}

    # 3. Party teacher starts a party workflow; the student sees the progress.
    workflow_start = await client.post(
        "/api/v1/admin/workflow/students",
        headers=party_teacher_headers,
        json={
            "student_id": student_id,
            "template_code": "PARTY_DEVELOPMENT_OFFICIAL_V2",
            "note": "S47 党团联通",
        },
    )
    assert workflow_start.status_code == 200, workflow_start.text
    workflow = workflow_start.json()["data"]
    assert workflow["template_code"] == "PARTY_DEVELOPMENT_OFFICIAL_V2"
    assert workflow["current_node_name"] == "教育引导"

    my_workflows = await client.get("/api/v1/workflow/my", headers=student_headers)
    assert my_workflows.status_code == 200, my_workflows.text
    assert workflow["id"] in {item["id"] for item in my_workflows.json()["data"]}

    # 4. Profile/report role boundaries line up with backend expectations.
    self_profile = await client.get("/api/v1/profile/me", headers=student_headers)
    assert self_profile.status_code == 200, self_profile.text
    assert self_profile.json()["data"]["student"]["student_no"] == "S470001"

    head_profile = await client.get(
        f"/api/v1/admin/profile/{student_id}", headers=head_teacher_headers
    )
    assert head_profile.status_code == 200, head_profile.text
    assert head_profile.json()["data"]["student"]["student_no"] == "S470001"

    party_profile = await client.get(
        f"/api/v1/admin/profile/{student_id}", headers=party_teacher_headers
    )
    assert party_profile.status_code == 403, party_profile.text

    student_gap = await client.get(
        "/api/v1/report/academic-gap", headers=student_headers
    )
    assert student_gap.status_code == 200, student_gap.text
    assert student_gap.json()["data"]["student_no"] == "S470001"
    assert student_gap.json()["data"]["total_credits_required"] == 6

    counselor_gap_list = await client.get(
        "/api/v1/admin/report/academic-gap",
        headers=counselor_headers,
        params={"page": 1, "page_size": 20},
    )
    assert counselor_gap_list.status_code == 200, counselor_gap_list.text
    gap_items = counselor_gap_list.json()["data"]["items"]
    assert {item["student_no"] for item in gap_items} == {"S470001"}

    party_dashboard = await client.get(
        "/api/v1/admin/report/overview", headers=party_teacher_headers
    )
    assert party_dashboard.status_code == 200, party_dashboard.text
    assert "metrics" in party_dashboard.json()["data"]

    # 5. Teacher publishes an honor record; the student-facing endpoint can read it.
    category = await client.post(
        "/api/v1/admin/honors/categories",
        headers=party_teacher_headers,
        json={
            "code": "S47_HONOR",
            "name": "S47 荣誉",
            "description": "S47 联通荣誉",
            "sort_order": 47,
            "is_active": True,
        },
    )
    assert category.status_code == 200, category.text
    honor = await client.post(
        "/api/v1/admin/honors",
        headers=party_teacher_headers,
        json={
            "category_code": "S47_HONOR",
            "title": "S47 联通荣誉",
            "level": "SCHOOL",
            "awarded_by": "信息学院",
            "announced_at": str(date(2026, 5, 26)),
            "is_collective": False,
            "summary": "S47 荣誉公示",
            "story_md": "S47 荣誉详情",
            "cover_image_url": "https://example.edu/s47-honor.jpg",
            "media": {"photos": ["https://example.edu/s47-honor.jpg"]},
            "consent_flag": True,
            "recipients": [
                {
                    "student_id": student_id,
                    "student_no_snapshot": "S470001",
                    "display_name": "S47 联通学生",
                    "major_snapshot": "CS",
                    "grade_snapshot": "2026",
                }
            ],
        },
    )
    assert honor.status_code == 200, honor.text
    honor_id = honor.json()["data"]["id"]

    public_honors = await client.get(
        "/api/v1/honors",
        headers=student_headers,
        params={"category_code": "S47_HONOR"},
    )
    assert public_honors.status_code == 200, public_honors.text
    assert [item["id"] for item in public_honors.json()["data"]["items"]] == [honor_id]
    public_honor_detail = await client.get(
        f"/api/v1/honors/{honor_id}", headers=student_headers
    )
    assert public_honor_detail.status_code == 200, public_honor_detail.text
    assert public_honor_detail.json()["data"]["cover_image_url"] == "https://example.edu/s47-honor.jpg"
