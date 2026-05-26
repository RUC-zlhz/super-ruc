"""党团流程闭环 — FR-004 学生侧本人进度 + FR-005 模板/节点/提醒管理。

覆盖：
- admin upsert template (3 nodes) → start for a student → 第一节点 PENDING
- GET /workflow/my：学生看到自己的流程与当前节点
- admin complete_node → 下一节点 triggered；全部完成后 workflow=COMPLETED
- admin mark_node_status=DEFERRED
- admin generate_reminders：模拟 overdue 场景，节点自动转 OVERDUE
- C-03：匿名 /workflow/my 401；学生调 /admin/workflow/templates 403
"""
from __future__ import annotations

from datetime import date, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.models import AuditLog
from app.auth.models import Student, User, UserRole
from app.core.security import create_token
from app.workflow.models import (
    StudentWorkflowNode,
    WorkflowReminder,
    WorkflowTemplate,
)


async def _login_as_student(
    client: AsyncClient, db: AsyncSession, *,
    student_no: str, wx_code: str,
) -> tuple[str, int]:
    stu = Student(
        student_no=student_no, full_name=f"w-{student_no}",
        grade_code="2022", major_code="CS", class_code="CS2201",
        political_status="入党申请人",
    )
    db.add(stu)
    await db.commit()
    await db.refresh(stu)
    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": wx_code,
            "student_no": student_no,
            "full_name": f"w-{student_no}",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"], stu.id


async def _create_student(
    db: AsyncSession,
    *,
    student_no: str,
    class_code: str,
    major_code: str = "CS",
    grade_code: str = "2022",
) -> int:
    stu = Student(
        student_no=student_no,
        full_name=f"w-{student_no}",
        grade_code=grade_code,
        major_code=major_code,
        class_code=class_code,
        political_status="入党申请人",
    )
    db.add(stu)
    await db.commit()
    await db.refresh(stu)
    return stu.id


async def _create_role_token(
    db: AsyncSession,
    *,
    work_no: str,
    role_code: str,
    scope_code: str | None = None,
) -> str:
    user = User(work_no=work_no, display_name=work_no, is_active=True)
    db.add(user)
    await db.flush()
    if scope_code is not None:
        db.add(UserRole(user_id=user.id, role_code=role_code, scope_code=scope_code))
    await db.commit()
    return create_token(str(user.id), "access", extra_claims={"roles": [role_code]})


def _party_template_payload() -> dict:
    return {
        "code": "PARTY_DEV_MAIN",
        "name": "党员发展主流程",
        "kind": "PARTY",
        "description": "入党申请 → 积极分子 → 发展对象",
        "version_label": "2026-v1",
        "nodes": [
            {
                "code": "APPLY",
                "name": "递交入党申请书",
                "sort_order": 1,
                "stage_group": "INITIAL",
                "required_task": "提交书面申请",
                "trigger_rule": "ON_APPLY",
                "due_rule_days": 30,
                "reminder_lead_days": 5,
                "reminder_enabled": True,
                "reminder_channel": "IN_APP",
                "repeat_interval_days": 3,
                "max_reminders": 3,
            },
            {
                "code": "ACTIVIST",
                "name": "确定为积极分子",
                "sort_order": 2,
                "stage_group": "ACTIVIST",
                "required_task": "支部大会讨论",
                "trigger_rule": "PREV_DONE",
                "due_rule_days": 60,
                "reminder_lead_days": 7,
                "reminder_enabled": True,
                "reminder_channel": "IN_APP",
                "repeat_interval_days": 7,
                "max_reminders": 2,
            },
            {
                "code": "TARGET",
                "name": "确定为发展对象",
                "sort_order": 3,
                "stage_group": "TARGET",
                "required_task": "政审 + 推优",
                "trigger_rule": "PREV_DONE",
                "reminder_enabled": False,
                "reminder_channel": "IN_APP",
                "is_terminal": True,
            },
        ],
    }


async def test_default_official_workflow_templates_are_seeded(
    db: AsyncSession,
) -> None:
    party = (
        await db.execute(
            select(WorkflowTemplate)
            .options(selectinload(WorkflowTemplate.nodes))
            .where(WorkflowTemplate.code == "PARTY_DEVELOPMENT_OFFICIAL_V2")
        )
    ).scalar_one()
    party_nodes = sorted(party.nodes, key=lambda node: node.sort_order)
    assert party.is_active is True
    assert party.name == "发展党员工作程序（官方29步）"
    assert len(party_nodes) == 29
    assert party_nodes[0].name == "教育引导"
    assert party_nodes[-1].name == "存档"
    assert party_nodes[-1].is_terminal is True
    assert {node.stage_group for node in party_nodes} == {
        "ACTIVIST_CONFIRMATION",
        "DEVELOPMENT_TARGET",
        "PROBATION_ACCEPTANCE",
        "PROBATION_EDUCATION_FULL_MEMBER",
    }

    youth = (
        await db.execute(
            select(WorkflowTemplate)
            .options(selectinload(WorkflowTemplate.nodes))
            .where(WorkflowTemplate.code == "YOUTH_LEAGUE_DEVELOPMENT_OFFICIAL_V2")
        )
    ).scalar_one()
    youth_nodes = sorted(youth.nodes, key=lambda node: node.sort_order)
    youth_node_names = [node.name for node in youth_nodes]
    assert youth.is_active is True
    assert youth.name == "发展团员工作流程（官方15步）"
    assert len(youth_nodes) == 15
    assert youth_nodes[0].name == "提交入团申请书"
    assert youth_nodes[-1].name == "档案管理"
    assert youth_nodes[-1].is_terminal is True
    assert "推优入党" not in youth_node_names
    assert "毕业团员转出" not in youth_node_names
    assert {node.stage_group for node in youth_nodes} == {
        "APPLY",
        "ACTIVIST_CONFIRMATION",
        "ACTIVIST_EDUCATION",
        "DEVELOPMENT_TARGET",
        "NEW_MEMBER_ACCEPTANCE",
    }

    membership = (
        await db.execute(
            select(WorkflowTemplate)
            .options(selectinload(WorkflowTemplate.nodes))
            .where(WorkflowTemplate.code == "YOUTH_LEAGUE_MEMBERSHIP_MANAGEMENT_V1")
        )
    ).scalar_one()
    membership_nodes = sorted(membership.nodes, key=lambda node: node.sort_order)
    assert membership.is_active is True
    assert [node.name for node in membership_nodes] == ["推优入党", "毕业团员转出"]

    legacy_rows = (
        await db.execute(
            select(WorkflowTemplate).where(
                WorkflowTemplate.code.in_(["PARTY_DEVELOPMENT_V1", "YOUTH_LEAGUE_V1"])
            )
        )
    ).scalars().all()
    legacy_by_code = {row.code: row for row in legacy_rows}
    assert legacy_by_code["PARTY_DEVELOPMENT_V1"].is_active is False
    assert legacy_by_code["YOUTH_LEAGUE_V1"].is_active is False


async def test_official_party_template_can_start_and_advance(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient,
) -> None:
    token, student_id = await _login_as_student(
        client, db, student_no="W00029", wx_code="wx_w00029",
    )

    start = await admin_client.post(
        "/api/v1/admin/workflow/students",
        json={
            "student_id": student_id,
            "template_code": "PARTY_DEVELOPMENT_OFFICIAL_V2",
            "note": "官方模板回归",
        },
    )
    assert start.status_code == 200, start.text
    workflow = start.json()["data"]
    assert workflow["current_node_name"] == "教育引导"
    assert len(workflow["nodes"]) == 29
    node_states = {node["node_code"]: node for node in workflow["nodes"]}
    first_state = node_states["PARTY_01_EDUCATION_GUIDANCE"]
    second_state = node_states["PARTY_02_RECEIVE_APPLICATION_TALK"]
    assert first_state["triggered_at"] is not None
    assert second_state["triggered_at"] is None

    complete = await admin_client.post(
        f"/api/v1/admin/workflow/node-states/{first_state['id']}/complete",
        json={"evidence": "已完成教育引导"},
    )
    assert complete.status_code == 200, complete.text
    advanced = complete.json()["data"]
    assert advanced["current_node_name"] == "接收入党申请书并派人谈话"
    advanced_nodes = {node["node_code"]: node for node in advanced["nodes"]}
    assert advanced_nodes["PARTY_01_EDUCATION_GUIDANCE"]["status"] == "DONE"
    assert advanced_nodes["PARTY_02_RECEIVE_APPLICATION_TALK"]["triggered_at"] is not None

    mine = await client.get(
        "/api/v1/workflow/my",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert mine.status_code == 200, mine.text
    assert mine.json()["data"][0]["template_code"] == "PARTY_DEVELOPMENT_OFFICIAL_V2"


async def test_party_template_upsert_start_complete_workflow(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient,
) -> None:
    token, student_id = await _login_as_student(
        client, db, student_no="W10001", wx_code="wx_w10001",
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    # 1. 上传党员发展模板
    upsert = await admin_client.post(
        "/api/v1/admin/workflow/templates", json=_party_template_payload(),
    )
    assert upsert.status_code == 200, upsert.text
    tpl = upsert.json()["data"]
    assert tpl["code"] == "PARTY_DEV_MAIN"
    assert len(tpl["nodes"]) == 3
    assert [n["code"] for n in tpl["nodes"]] == ["APPLY", "ACTIVIST", "TARGET"]
    assert tpl["nodes"][0]["repeat_interval_days"] == 3
    assert tpl["nodes"][0]["max_reminders"] == 3
    assert tpl["nodes"][2]["reminder_enabled"] is False

    # 2. 管理员可先搜索学生，再为学生启动流程
    search = await admin_client.get(
        "/api/v1/admin/workflow/students/search",
        params={"q": "W10001"},
    )
    assert search.status_code == 200, search.text
    search_items = search.json()["data"]["items"]
    assert len(search_items) == 1
    assert search_items[0]["student_no"] == "W10001"

    start = await admin_client.post(
        "/api/v1/admin/workflow/students",
        json={
            "student_id": student_id,
            "template_code": "PARTY_DEV_MAIN",
            "note": "支书初核",
        },
    )
    assert start.status_code == 200, start.text
    sw = start.json()["data"]
    assert sw["status"] == "ACTIVE"
    assert sw["current_node_name"] == "递交入党申请书"
    assert sw["next_action_hint"] == "提交书面申请"
    node_states = {n["node_code"]: n for n in sw["nodes"]}
    assert node_states["APPLY"]["status"] == "PENDING"
    assert node_states["APPLY"]["triggered_at"] is not None
    assert node_states["APPLY"]["due_date"] is not None
    assert node_states["ACTIVIST"]["status"] == "PENDING"
    assert node_states["ACTIVIST"]["triggered_at"] is None

    # 重复启动 → ConflictError
    dup = await admin_client.post(
        "/api/v1/admin/workflow/students",
        json={"student_id": student_id, "template_code": "PARTY_DEV_MAIN"},
    )
    assert dup.status_code == 409

    # 3. 学生 GET /workflow/my
    mine = await client.get("/api/v1/workflow/my", headers=stu_headers)
    assert mine.status_code == 200, mine.text
    my_list = mine.json()["data"]
    assert len(my_list) == 1
    assert my_list[0]["template_code"] == "PARTY_DEV_MAIN"
    assert my_list[0]["current_node_name"] == "递交入党申请书"

    listed = await admin_client.get(
        "/api/v1/admin/workflow/students",
        params={"student_no": "W10001", "template_code": "PARTY_DEV_MAIN"},
    )
    assert listed.status_code == 200, listed.text
    assert listed.json()["data"]["meta"]["total"] == 1
    assert listed.json()["data"]["items"][0]["student_no"] == "W10001"

    # 4. 完成第 1 节点 → 第 2 节点触发
    state_apply = node_states["APPLY"]["id"]
    complete1 = await admin_client.post(
        f"/api/v1/admin/workflow/node-states/{state_apply}/complete",
        json={"evidence": "纸质申请书扫描件 URL", "note": "已收到"},
    )
    assert complete1.status_code == 200, complete1.text
    sw2 = complete1.json()["data"]
    assert sw2["current_node_name"] == "确定为积极分子"
    ns2 = {n["node_code"]: n for n in sw2["nodes"]}
    assert ns2["APPLY"]["status"] == "DONE"
    assert ns2["APPLY"]["completed_at"] is not None
    assert ns2["ACTIVIST"]["status"] == "PENDING"
    assert ns2["ACTIVIST"]["triggered_at"] is not None

    # 5. DEFERRED 标记第 2 节点
    state_activist = ns2["ACTIVIST"]["id"]
    defer = await admin_client.post(
        f"/api/v1/admin/workflow/node-states/{state_activist}/status",
        json={"status": "DEFERRED", "note": "支部大会推迟到下月"},
    )
    assert defer.status_code == 200
    deferred_nodes = {n["node_code"]: n for n in defer.json()["data"]["nodes"]}
    assert deferred_nodes["ACTIVIST"]["status"] == "DEFERRED"

    # 6. 继续完成 2 和 3 → 流程 COMPLETED
    c2 = await admin_client.post(
        f"/api/v1/admin/workflow/node-states/{state_activist}/complete",
        json={"evidence": "支部大会决议"},
    )
    assert c2.status_code == 200
    state_target = next(
        n["id"] for n in c2.json()["data"]["nodes"] if n["node_code"] == "TARGET"
    )
    c3 = await admin_client.post(
        f"/api/v1/admin/workflow/node-states/{state_target}/complete",
        json={"evidence": "政审材料齐备"},
    )
    assert c3.status_code == 200
    final = c3.json()["data"]
    assert final["status"] == "COMPLETED"
    assert final["completed_at"] is not None
    assert final["current_node_id"] is None


async def test_workflow_reminders_overdue_path(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient,
) -> None:
    """覆盖 FR-005：对已触发但过期的节点生成提醒 + 节点自动转 OVERDUE。"""
    _tok, student_id = await _login_as_student(
        client, db, student_no="W20001", wx_code="wx_w20001",
    )

    await admin_client.post(
        "/api/v1/admin/workflow/templates", json=_party_template_payload(),
    )
    start = await admin_client.post(
        "/api/v1/admin/workflow/students",
        json={"student_id": student_id, "template_code": "PARTY_DEV_MAIN"},
    )
    assert start.status_code == 200

    # 直接改 DB：把第一节点 due_date 拨到昨天，模拟逾期
    yesterday = date.today() - timedelta(days=1)
    states = (
        await db.execute(
            select(StudentWorkflowNode).where(
                StudentWorkflowNode.workflow_id == start.json()["data"]["id"]
            )
        )
    ).scalars().all()
    apply_state = next(s for s in states if s.triggered_at is not None)
    apply_state.due_date = yesterday
    await db.commit()

    # 生成提醒
    gen = await admin_client.post(
        "/api/v1/admin/workflow/reminders/generate",
        json={"channel": "IN_APP"},
    )
    assert gen.status_code == 200, gen.text
    run = gen.json()["data"]
    assert run["created_count"] >= 1
    assert run["sent_count"] >= 1
    assert run["status"] == "COMPLETED"

    # 节点状态已自动转 OVERDUE
    await db.refresh(apply_state)
    assert apply_state.status == "OVERDUE"

    # Reminder 记录已入库
    reminders = (
        await db.execute(
            select(WorkflowReminder).where(
                WorkflowReminder.workflow_node_state_id == apply_state.id
            )
        )
    ).scalars().all()
    assert len(reminders) >= 1
    r = reminders[0]
    assert r.channel == "IN_APP"
    assert r.status == "SENT"
    assert r.sent_at is not None

    runs = await admin_client.get("/api/v1/admin/workflow/reminder-runs")
    assert runs.status_code == 200, runs.text
    assert runs.json()["data"]["items"][0]["id"] == run["id"]

    reminder_list = await admin_client.get(
        "/api/v1/admin/workflow/reminders",
        params={"template_code": "PARTY_DEV_MAIN", "student_no": "W20001"},
    )
    assert reminder_list.status_code == 200, reminder_list.text
    reminder_item = reminder_list.json()["data"]["items"][0]
    assert reminder_item["student_no"] == "W20001"
    assert reminder_item["template_code"] == "PARTY_DEV_MAIN"
    assert reminder_item["status"] == "SENT"


async def test_complete_node_cancels_unsent_workflow_reminders(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient,
) -> None:
    _tok, student_id = await _login_as_student(
        client, db, student_no="W30001", wx_code="wx_w30001",
    )
    await admin_client.post(
        "/api/v1/admin/workflow/templates", json=_party_template_payload(),
    )
    start = await admin_client.post(
        "/api/v1/admin/workflow/students",
        json={"student_id": student_id, "template_code": "PARTY_DEV_MAIN"},
    )
    assert start.status_code == 200
    apply_state = next(
        node for node in start.json()["data"]["nodes"] if node["node_code"] == "APPLY"
    )

    reminder = WorkflowReminder(
        workflow_node_state_id=apply_state["id"],
        student_id=student_id,
        reminder_date=date.today(),
        channel="IN_APP",
        status="PENDING",
        message="待发送提醒",
    )
    db.add(reminder)
    await db.commit()

    complete = await admin_client.post(
        f"/api/v1/admin/workflow/node-states/{apply_state['id']}/complete",
        json={"evidence": "已提交材料"},
    )
    assert complete.status_code == 200, complete.text

    await db.refresh(reminder)
    assert reminder.status == "CANCELLED"
    assert reminder.cancel_reason == "节点已完成，自动关闭未发送提醒"


async def test_scoped_launcher_can_start_only_students_in_scope(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient,
) -> None:
    in_scope_student_id = await _create_student(
        db,
        student_no="W41001",
        class_code="CS2201",
    )
    out_scope_student_id = await _create_student(
        db,
        student_no="W41002",
        class_code="CS2202",
    )
    token = await _create_role_token(
        db,
        work_no="WFCOUNSELOR01",
        role_code="COUNSELOR",
        scope_code="CLASS:CS2201",
    )
    headers = {"Authorization": f"Bearer {token}"}

    upsert = await admin_client.post(
        "/api/v1/admin/workflow/templates",
        json=_party_template_payload(),
    )
    assert upsert.status_code == 200, upsert.text

    ok_start = await client.post(
        "/api/v1/admin/workflow/students",
        headers=headers,
        json={"student_id": in_scope_student_id, "template_code": "PARTY_DEV_MAIN"},
    )
    assert ok_start.status_code == 200, ok_start.text

    denied = await client.post(
        "/api/v1/admin/workflow/students",
        headers=headers,
        json={"student_id": out_scope_student_id, "template_code": "PARTY_DEV_MAIN"},
    )
    assert denied.status_code == 403, denied.text
    assert "无权为该学生发起流程" in denied.text

    denied_log = (
        await db.execute(
            select(AuditLog)
            .where(
                AuditLog.event_type == "WORKFLOW",
                AuditLog.entity_code == "STUDENT_WORKFLOW",
                AuditLog.action == "START",
                AuditLog.entity_id == out_scope_student_id,
            )
            .order_by(AuditLog.id.desc())
        )
    ).scalar_one()
    assert denied_log.result_code == "DENIED"
    assert denied_log.detail["target"]["student_id"] == out_scope_student_id
    assert denied_log.detail["target"]["template_code"] == "PARTY_DEV_MAIN"
    assert denied_log.detail["reason"] == "OUT_OF_SCOPE"


async def test_scoped_launcher_without_scope_cannot_start_student_workflow(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient,
) -> None:
    student_id = await _create_student(
        db,
        student_no="W42001",
        class_code="CS2201",
    )
    token = await _create_role_token(
        db,
        work_no="WFCOUNSELOR02",
        role_code="COUNSELOR",
    )

    upsert = await admin_client.post(
        "/api/v1/admin/workflow/templates",
        json=_party_template_payload(),
    )
    assert upsert.status_code == 200, upsert.text

    denied = await client.post(
        "/api/v1/admin/workflow/students",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": student_id, "template_code": "PARTY_DEV_MAIN"},
    )
    assert denied.status_code == 403, denied.text

    denied_log = (
        await db.execute(
            select(AuditLog)
            .where(
                AuditLog.event_type == "WORKFLOW",
                AuditLog.entity_code == "STUDENT_WORKFLOW",
                AuditLog.action == "START",
                AuditLog.entity_id == student_id,
            )
            .order_by(AuditLog.id.desc())
        )
    ).scalar_one()
    assert denied_log.result_code == "DENIED"
    assert denied_log.detail["reason"] == "EMPTY_SCOPE"


async def test_super_admin_can_start_student_workflow_outside_scoped_boundaries(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient,
) -> None:
    student_id = await _create_student(
        db,
        student_no="W43001",
        class_code="CS9999",
    )
    token = await _create_role_token(
        db,
        work_no="WFSUPER01",
        role_code="SUPER_ADMIN",
    )

    upsert = await admin_client.post(
        "/api/v1/admin/workflow/templates",
        json=_party_template_payload(),
    )
    assert upsert.status_code == 200, upsert.text

    start = await client.post(
        "/api/v1/admin/workflow/students",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": student_id, "template_code": "PARTY_DEV_MAIN"},
    )
    assert start.status_code == 200, start.text

    detail = await client.get(
        f"/api/v1/workflow/{start.json()['data']['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail.status_code == 200, detail.text


async def test_workflow_detail_requires_student_self_or_authorized_scope(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient,
) -> None:
    token_a, student_a_id = await _login_as_student(
        client, db, student_no="W44001", wx_code="wx_w44001",
    )
    token_b, _student_b_id = await _login_as_student(
        client, db, student_no="W44002", wx_code="wx_w44002",
    )
    guest_user = User(work_no="WFGUEST01", display_name="Workflow Guest", is_active=True)
    db.add(guest_user)
    await db.commit()
    guest_token = create_token(str(guest_user.id), "access", extra_claims={"roles": []})

    upsert = await admin_client.post(
        "/api/v1/admin/workflow/templates",
        json=_party_template_payload(),
    )
    assert upsert.status_code == 200, upsert.text
    start = await admin_client.post(
        "/api/v1/admin/workflow/students",
        json={"student_id": student_a_id, "template_code": "PARTY_DEV_MAIN"},
    )
    assert start.status_code == 200, start.text
    workflow_id = start.json()["data"]["id"]

    own = await client.get(
        f"/api/v1/workflow/{workflow_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert own.status_code == 200, own.text

    other = await client.get(
        f"/api/v1/workflow/{workflow_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert other.status_code == 403, other.text

    guest = await client.get(
        f"/api/v1/workflow/{workflow_id}",
        headers={"Authorization": f"Bearer {guest_token}"},
    )
    assert guest.status_code == 403, guest.text


async def test_scoped_workflow_admin_lists_and_reminders_are_scope_filtered(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient,
) -> None:
    in_scope_student_id = await _create_student(
        db,
        student_no="W45001",
        class_code="CS2201",
    )
    out_scope_student_id = await _create_student(
        db,
        student_no="W45002",
        class_code="CS2202",
    )
    token = await _create_role_token(
        db,
        work_no="WFCOUNSELOR03",
        role_code="COUNSELOR",
        scope_code="CLASS:CS2201",
    )
    headers = {"Authorization": f"Bearer {token}"}

    upsert = await admin_client.post(
        "/api/v1/admin/workflow/templates",
        json=_party_template_payload(),
    )
    assert upsert.status_code == 200, upsert.text
    in_start = await admin_client.post(
        "/api/v1/admin/workflow/students",
        json={"student_id": in_scope_student_id, "template_code": "PARTY_DEV_MAIN"},
    )
    assert in_start.status_code == 200, in_start.text
    out_start = await admin_client.post(
        "/api/v1/admin/workflow/students",
        json={"student_id": out_scope_student_id, "template_code": "PARTY_DEV_MAIN"},
    )
    assert out_start.status_code == 200, out_start.text

    in_state = next(
        node for node in in_start.json()["data"]["nodes"] if node["node_code"] == "APPLY"
    )
    out_state = next(
        node for node in out_start.json()["data"]["nodes"] if node["node_code"] == "APPLY"
    )
    db.add(
        WorkflowReminder(
            workflow_node_state_id=in_state["id"],
            student_id=in_scope_student_id,
            reminder_date=date.today(),
            channel="IN_APP",
            status="SENT",
            message="scope in",
        )
    )
    db.add(
        WorkflowReminder(
            workflow_node_state_id=out_state["id"],
            student_id=out_scope_student_id,
            reminder_date=date.today(),
            channel="IN_APP",
            status="SENT",
            message="scope out",
        )
    )
    await db.commit()

    workflows = await client.get(
        "/api/v1/admin/workflow/students",
        headers=headers,
    )
    assert workflows.status_code == 200, workflows.text
    workflow_items = workflows.json()["data"]["items"]
    assert workflows.json()["data"]["meta"]["total"] == 1
    assert [item["student_no"] for item in workflow_items] == ["W45001"]

    reminders = await client.get(
        "/api/v1/admin/workflow/reminders",
        headers=headers,
    )
    assert reminders.status_code == 200, reminders.text
    reminder_items = reminders.json()["data"]["items"]
    assert reminders.json()["data"]["meta"]["total"] == 1
    assert [item["student_no"] for item in reminder_items] == ["W45001"]


async def test_scoped_workflow_node_operations_reject_out_of_scope_and_audit(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient,
) -> None:
    out_scope_student_id = await _create_student(
        db,
        student_no="W46001",
        class_code="CS2202",
    )
    token = await _create_role_token(
        db,
        work_no="WFCOUNSELOR04",
        role_code="COUNSELOR",
        scope_code="CLASS:CS2201",
    )
    headers = {"Authorization": f"Bearer {token}"}

    upsert = await admin_client.post(
        "/api/v1/admin/workflow/templates",
        json=_party_template_payload(),
    )
    assert upsert.status_code == 200, upsert.text
    start = await admin_client.post(
        "/api/v1/admin/workflow/students",
        json={"student_id": out_scope_student_id, "template_code": "PARTY_DEV_MAIN"},
    )
    assert start.status_code == 200, start.text
    apply_state = next(
        node for node in start.json()["data"]["nodes"] if node["node_code"] == "APPLY"
    )

    denied_complete = await client.post(
        f"/api/v1/admin/workflow/node-states/{apply_state['id']}/complete",
        headers=headers,
        json={"evidence": "越权材料"},
    )
    assert denied_complete.status_code == 403, denied_complete.text
    assert "无权操作该流程节点" in denied_complete.text

    denied_status = await client.post(
        f"/api/v1/admin/workflow/node-states/{apply_state['id']}/status",
        headers=headers,
        json={"status": "DEFERRED", "note": "越权延期"},
    )
    assert denied_status.status_code == 403, denied_status.text

    logs = (
        await db.execute(
            select(AuditLog)
            .where(
                AuditLog.event_type == "WORKFLOW",
                AuditLog.entity_code == "STUDENT_WORKFLOW_NODE",
                AuditLog.entity_id == apply_state["id"],
            )
            .order_by(AuditLog.id)
        )
    ).scalars().all()
    denied_actions = {log.action for log in logs if log.result_code == "DENIED"}
    assert {"COMPLETE_DENIED", "MARK_STATUS_DENIED"} <= denied_actions


async def test_workflow_endpoints_reject_anonymous_and_student(
    client: AsyncClient, db: AsyncSession,
) -> None:
    resp = await client.get("/api/v1/workflow/my")
    assert resp.status_code == 401

    token, _ = await _login_as_student(
        client, db, student_no="W90001", wx_code="wx_w90001",
    )
    # 学生不得调用模板管理
    forbidden = await client.post(
        "/api/v1/admin/workflow/templates",
        headers={"Authorization": f"Bearer {token}"},
        json=_party_template_payload(),
    )
    assert forbidden.status_code == 403


async def test_collaborator_role_can_access_workflow_admin_tools(
    client: AsyncClient,
    db: AsyncSession,
    admin_client: AsyncClient,
) -> None:
    student_id = await _create_student(
        db,
        student_no="W47001",
        class_code="CS2201",
    )
    await admin_client.post(
        "/api/v1/admin/workflow/templates",
        json=_party_template_payload(),
    )
    started = await admin_client.post(
        "/api/v1/admin/workflow/students",
        json={"student_id": student_id, "template_code": "PARTY_DEV_MAIN"},
    )
    assert started.status_code == 200, started.text
    apply_state = next(
        node for node in started.json()["data"]["nodes"] if node["node_code"] == "APPLY"
    )

    user = User(work_no="WFCADRE01", display_name="Workflow Cadre", is_active=True)
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_code="PARTY_BRANCH_SECRETARY"))
    await db.commit()
    token = create_token(str(user.id), "access", extra_claims={"roles": ["PARTY_BRANCH_SECRETARY"]})

    resp = await client.get(
        "/api/v1/admin/workflow/templates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text

    search = await client.get(
        "/api/v1/admin/workflow/students/search",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert search.status_code == 403, search.text

    workflows = await client.get(
        "/api/v1/admin/workflow/students",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert workflows.status_code == 200, workflows.text
    assert workflows.json()["data"]["meta"]["total"] == 0

    node_status = await client.post(
        f"/api/v1/admin/workflow/node-states/{apply_state['id']}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "DEFERRED", "note": "无范围协同角色不可操作"},
    )
    assert node_status.status_code == 403, node_status.text

    start = await client.post(
        "/api/v1/admin/workflow/students",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": 1, "template_code": "PARTY_DEV_MAIN"},
    )
    assert start.status_code == 403, start.text
