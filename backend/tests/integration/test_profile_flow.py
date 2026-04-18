"""profile 闭环 — FR-018 学生画像 + v1.5 账号生命周期。

覆盖：
- 学生本人 GET /profile/me：只返回非敏感 facts，敏感条目对学生端隐藏
- 学生 POST /profile/me/corrections → admin 审批 APPROVED + apply_to_fact → 字段落库
- 管理员 GET /admin/profile/students 搜索；POST /admin/profile/{id}/facts 录入事实
- v1.5：enrollment_status=ARCHIVED 的学生写操作被拦截（提交申请 → 40311），
  但 /profile/me 只读仍可访问
- C-03：匿名访问 401
"""
from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import ENROLLMENT_ARCHIVED, Student
from app.profile.models import ProfileFact


async def _login_as_student(
    client: AsyncClient, db: AsyncSession, *, student_no: str, wx_code: str,
) -> tuple[str, int]:
    """创建学生 + 走 mock wx-login，返回 (access_token, student_id)。"""
    stu = Student(
        student_no=student_no,
        full_name=f"p-{student_no}",
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


async def test_my_profile_hides_sensitive_facts(
    client: AsyncClient,
    db: AsyncSession,
    admin_client: AsyncClient,
) -> None:
    """FR-018 + C-04：学生端只能看到 is_sensitive=False 的事实。"""
    token, student_id = await _login_as_student(
        client, db, student_no="P100001", wx_code="wx_p100001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    # admin 录入两条事实：一条普通、一条敏感
    r1 = await admin_client.post(
        f"/api/v1/admin/profile/{student_id}/facts",
        json={
            "fact_type": "COMPETITION",
            "title": "ACM-ICPC 省赛银奖",
            "rank_label": "省级二等奖",
            "source": "TEACHER_ENTRY",
        },
    )
    assert r1.status_code == 200, r1.text

    r2 = await admin_client.post(
        f"/api/v1/admin/profile/{student_id}/facts",
        json={
            "fact_type": "CUSTOM",
            "title": "心理辅导记录",
            "description": "学期焦虑咨询两次",
            "source": "TEACHER_ENTRY",
            "is_sensitive": True,
        },
    )
    assert r2.status_code == 200, r2.text

    # 学生端视图
    mine = await client.get("/api/v1/profile/me", headers=stu_headers)
    assert mine.status_code == 200, mine.text
    data = mine.json()["data"]
    assert data["student"]["student_no"] == "P100001"
    titles = {f["title"] for f in data["facts"]}
    assert "ACM-ICPC 省赛银奖" in titles
    assert "心理辅导记录" not in titles  # 敏感条目对学生隐藏
    assert data["competition_count"] == 1

    # 管理侧视图可以看到全部
    admin_view = await admin_client.get(f"/api/v1/admin/profile/{student_id}")
    assert admin_view.status_code == 200
    admin_titles = {f["title"] for f in admin_view.json()["data"]["facts"]}
    assert {"ACM-ICPC 省赛银奖", "心理辅导记录"}.issubset(admin_titles)


async def test_correction_approve_applies_to_fact(
    client: AsyncClient,
    db: AsyncSession,
    admin_client: AsyncClient,
) -> None:
    """学生提纠错 → admin 审批 APPROVED+apply_to_fact=True → fact 字段被更新。"""
    token, student_id = await _login_as_student(
        client, db, student_no="P200001", wx_code="wx_p200001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    create_fact = await admin_client.post(
        f"/api/v1/admin/profile/{student_id}/facts",
        json={
            "fact_type": "PRACTICE",
            "title": "支教活动",
            "description": "山区小学支教一周",
            "source": "TEACHER_ENTRY",
        },
    )
    fact_id = create_fact.json()["data"]["id"]

    # 学生提交纠错：修正 description
    corr = await client.post(
        "/api/v1/profile/me/corrections",
        headers=stu_headers,
        json={
            "fact_id": fact_id,
            "field_name": "description",
            "proposed_value": "山区支教两周（原记录有误）",
            "reason": "实际参与两周，不是一周",
        },
    )
    assert corr.status_code == 200, corr.text
    cor = corr.json()["data"]
    assert cor["status"] == "PENDING"
    assert cor["current_value"] == "山区小学支教一周"
    correction_id = cor["id"]

    # admin 审批通过，应用到 fact
    decision = await admin_client.post(
        f"/api/v1/admin/profile/corrections/{correction_id}/decision",
        json={
            "decision": "APPROVED",
            "comment": "属实，核销原记录",
            "apply_to_fact": True,
        },
    )
    assert decision.status_code == 200, decision.text
    assert decision.json()["data"]["status"] == "APPROVED"

    # 直接查 DB 验证 fact.description 被更新
    fact = (
        await db.execute(select(ProfileFact).where(ProfileFact.id == fact_id))
    ).scalar_one()
    await db.refresh(fact)
    assert fact.description == "山区支教两周（原记录有误）"


async def test_admin_search_students(
    db: AsyncSession,
    admin_client: AsyncClient,
) -> None:
    """管理员按 grade/major 搜索学生列表。"""
    db.add_all([
        Student(
            student_no="P310001", full_name="张三",
            grade_code="2023", major_code="CS", class_code="CS2301",
        ),
        Student(
            student_no="P310002", full_name="李四",
            grade_code="2023", major_code="CS", class_code="CS2301",
        ),
        Student(
            student_no="P310099", full_name="王五",
            grade_code="2024", major_code="SE", class_code="SE2401",
        ),
    ])
    await db.commit()

    resp = await admin_client.get(
        "/api/v1/admin/profile/students",
        params={"grade_code": "2023", "major_code": "CS"},
    )
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]["items"]
    nos = {i["student_no"] for i in items}
    assert {"P310001", "P310002"}.issubset(nos)
    assert "P310099" not in nos

    # 关键字搜索姓名
    resp2 = await admin_client.get(
        "/api/v1/admin/profile/students", params={"q": "王五"},
    )
    items2 = resp2.json()["data"]["items"]
    assert any(i["student_no"] == "P310099" for i in items2)


async def test_archived_student_cannot_submit_request_but_can_read_profile(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    """v1.5：enrollment_status=ARCHIVED 只读降级。
    - 画像只读接口仍可调用
    - 事务申请创建（require_active_enrollment）→ 40311 / 403
    """
    token, student_id = await _login_as_student(
        client, db, student_no="P400001", wx_code="wx_p400001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    # 降级为 ARCHIVED
    stu = await db.get(Student, student_id)
    assert stu is not None
    stu.enrollment_status = ENROLLMENT_ARCHIVED
    await db.commit()

    # 只读仍可
    mine = await client.get("/api/v1/profile/me", headers=stu_headers)
    assert mine.status_code == 200, mine.text

    # 写操作拦截：创建申请 → 403 + 40311
    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "LEAVE_PERSONAL",
            "title": "毕业后补请假",
            "form_data": {"reason": "测试"},
        },
    )
    assert create.status_code == 403, create.text
    body = create.json()
    assert body["code"] == 40311


async def test_archived_student_cannot_submit_correction(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    """v1.5 生命周期漏口回归：非在读学生提交画像纠错 → 403 / 40311。"""
    token, student_id = await _login_as_student(
        client, db, student_no="P500001", wx_code="wx_p500001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    stu = await db.get(Student, student_id)
    assert stu is not None
    stu.enrollment_status = ENROLLMENT_ARCHIVED
    await db.commit()

    # 只读仍通过
    mine = await client.get("/api/v1/profile/me", headers=stu_headers)
    assert mine.status_code == 200

    # 纠错申诉写操作被拦截
    resp = await client.post(
        "/api/v1/profile/me/corrections",
        headers=stu_headers,
        json={
            "fact_id": None,
            "field_name": "description",
            "proposed_value": "归档后补申诉",
            "reason": "测试",
        },
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == 40311


async def test_profile_endpoints_reject_anonymous(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/profile/me")
    assert resp.status_code == 401
    resp2 = await client.get("/api/v1/admin/profile/students")
    assert resp2.status_code == 401
