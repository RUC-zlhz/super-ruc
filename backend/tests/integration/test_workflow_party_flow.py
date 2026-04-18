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

from app.auth.models import Student
from app.workflow.models import (
    StudentWorkflowNode,
    WorkflowReminder,
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
        json={"code": wx_code, "student_no": student_no},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"], stu.id


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
                "due_rule_days": 30,
                "reminder_lead_days": 5,
            },
            {
                "code": "ACTIVIST",
                "name": "确定为积极分子",
                "sort_order": 2,
                "stage_group": "ACTIVIST",
                "required_task": "支部大会讨论",
                "due_rule_days": 60,
                "reminder_lead_days": 7,
            },
            {
                "code": "TARGET",
                "name": "确定为发展对象",
                "sort_order": 3,
                "stage_group": "TARGET",
                "required_task": "政审 + 推优",
                "is_terminal": True,
            },
        ],
    }


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

    # 2. 管理员为学生启动流程
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
    workflow_id = sw["id"]

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
    assert gen.json()["data"]["created"] >= 1

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
    assert r.status == "PENDING"
    assert str(yesterday) in (r.message or "")


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
