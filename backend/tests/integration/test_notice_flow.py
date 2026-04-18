"""notice 闭环 — FR-010 目标人群 + FR-011 发送批次与送达记录。

覆盖：
- admin create → target-preview（按 grade/major/political_status 过滤）
- publish → dispatch（IN_APP + SMS，IN_APP=SENT / SMS=SKIPPED）
- 学生 GET /notices/inbox 看到自己那条；mark-read 后 read_at 落库
- DRAFT 通知不能直接 dispatch；ARCHIVED 通知不能修改
- 管理员 GET /{notice}/batches 与 /batches/{id}/deliveries 返回分页
- C-03：匿名访问 401，普通学生访问 /admin/notices 403
"""
from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student


async def _login_as_student(
    client: AsyncClient, db: AsyncSession, *,
    student_no: str, wx_code: str,
    grade_code: str = "2022", major_code: str = "CS", class_code: str = "CS2201",
    political_status: str | None = None,
) -> tuple[str, int]:
    stu = Student(
        student_no=student_no, full_name=f"n-{student_no}",
        grade_code=grade_code, major_code=major_code, class_code=class_code,
        political_status=political_status,
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


async def _seed_broadcast_students(db: AsyncSession) -> None:
    """写一批覆盖多 grade/major/political_status 的学生，用于 target-preview。"""
    db.add_all([
        Student(student_no="N10001", full_name="大四党员",
                grade_code="2021", major_code="CS", class_code="CS2101",
                political_status="中共党员"),
        Student(student_no="N10002", full_name="大四群众",
                grade_code="2021", major_code="CS", class_code="CS2101",
                political_status="群众"),
        Student(student_no="N10003", full_name="大三党员",
                grade_code="2022", major_code="CS", class_code="CS2201",
                political_status="中共党员"),
        Student(student_no="N10004", full_name="大三软工",
                grade_code="2022", major_code="SE", class_code="SE2201",
                political_status="共青团员"),
    ])
    await db.commit()


async def test_target_preview_filters_by_grade_major_and_political_status(
    db: AsyncSession, admin_client: AsyncClient,
) -> None:
    await _seed_broadcast_students(db)

    # 仅 2021 级 CS
    resp = await admin_client.post(
        "/api/v1/admin/notices/target-preview",
        json={
            "target_rule": {
                "grade_codes": ["2021"],
                "major_codes": ["CS"],
            }
        },
    )
    assert resp.status_code == 200, resp.text
    r = resp.json()["data"]
    assert r["target_count"] == 2
    assert set(r["sample_student_nos"]) == {"N10001", "N10002"}

    # 仅中共党员
    resp = await admin_client.post(
        "/api/v1/admin/notices/target-preview",
        json={"target_rule": {"political_status": ["中共党员"]}},
    )
    r = resp.json()["data"]
    assert r["target_count"] == 2
    assert set(r["sample_student_nos"]) == {"N10001", "N10003"}

    # 空规则 = 全部在读
    resp = await admin_client.post(
        "/api/v1/admin/notices/target-preview", json={"target_rule": None},
    )
    assert resp.json()["data"]["target_count"] >= 4


async def test_notice_publish_dispatch_and_student_inbox(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient,
) -> None:
    # 1. 先建一个目标学生（2022 CS 党员）
    token, student_id = await _login_as_student(
        client, db, student_no="N20001", wx_code="wx_n20001",
        political_status="中共党员",
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    # 2. 管理员创建通知
    create = await admin_client.post(
        "/api/v1/admin/notices",
        json={
            "title": "4 月党支部例会",
            "body_md": "## 议程\n1. 学习材料\n2. 组织生活",
            "summary": "4 月党员例会通知",
            "category": "PARTY",
            "tags": ["党员", "例会"],
            "target_rule": {
                "grade_codes": ["2022"],
                "major_codes": ["CS"],
                "political_status": ["中共党员"],
            },
            "target_summary": "2022 级 CS 党员",
            "channels": ["IN_APP", "SMS"],
        },
    )
    assert create.status_code == 200, create.text
    notice = create.json()["data"]
    assert notice["status"] == "DRAFT"
    assert set(notice["tags"]) == {"党员", "例会"}
    notice_id = notice["id"]

    # 3. DRAFT 不能 dispatch
    early_dispatch = await admin_client.post(
        f"/api/v1/admin/notices/{notice_id}/dispatch", json={},
    )
    assert early_dispatch.status_code == 400
    assert early_dispatch.json()["code"] == 40032

    # 4. 发布
    publish = await admin_client.post(
        f"/api/v1/admin/notices/{notice_id}/publish",
    )
    assert publish.status_code == 200, publish.text
    assert publish.json()["data"]["status"] == "PUBLISHED"
    assert publish.json()["data"]["published_at"] is not None

    # 5. 发送（IN_APP 成功 / SMS 因 SMS_ENABLED=False 跳过）
    dispatch = await admin_client.post(
        f"/api/v1/admin/notices/{notice_id}/dispatch", json={},
    )
    assert dispatch.status_code == 200, dispatch.text
    batch = dispatch.json()["data"]
    assert batch["target_count"] == 1
    # 1 IN_APP SENT + 1 SMS SKIPPED；failed=0 → COMPLETED
    assert batch["success_count"] == 1
    assert batch["failed_count"] == 0
    assert batch["status"] == "COMPLETED"
    batch_id = batch["id"]
    assert batch["batch_no"].startswith("NB-")

    # 6. 学生收件箱看到这条
    inbox = await client.get("/api/v1/notices/inbox", headers=stu_headers)
    assert inbox.status_code == 200
    items = inbox.json()["data"]["items"]
    assert len(items) == 1
    item = items[0]
    assert item["id"] == notice_id
    assert item["read_at"] is None
    delivery_id = item["delivery_id"]

    # 7. mark-read → 再查 unread_only=true 应为空
    mark = await client.post(
        f"/api/v1/notices/read/{delivery_id}", headers=stu_headers,
    )
    assert mark.status_code == 200

    unread = await client.get(
        "/api/v1/notices/inbox", params={"unread_only": True}, headers=stu_headers,
    )
    assert unread.json()["data"]["meta"]["total"] == 0

    # 8. admin 查批次 + 投递明细
    batches = await admin_client.get(
        f"/api/v1/admin/notices/{notice_id}/batches"
    )
    assert batches.status_code == 200
    assert any(b["id"] == batch_id for b in batches.json()["data"])

    deliveries = await admin_client.get(
        f"/api/v1/admin/notices/batches/{batch_id}/deliveries",
    )
    assert deliveries.status_code == 200
    dlist = deliveries.json()["data"]["items"]
    assert len(dlist) == 2
    by_ch = {d["channel"]: d["status"] for d in dlist}
    assert by_ch["IN_APP"] == "READ"  # mark_read 把 IN_APP 的 status 置为 READ
    assert by_ch["SMS"] == "SKIPPED"
    sms_row = next(d for d in dlist if d["channel"] == "SMS")
    assert sms_row["error_code"] == "SMS_DISABLED"


async def test_archived_notice_cannot_be_edited(
    admin_client: AsyncClient,
) -> None:
    create = await admin_client.post(
        "/api/v1/admin/notices",
        json={
            "title": "存档测试",
            "body_md": "x",
            "channels": ["IN_APP"],
        },
    )
    notice_id = create.json()["data"]["id"]
    arch = await admin_client.post(
        f"/api/v1/admin/notices/{notice_id}/archive"
    )
    assert arch.status_code == 200
    assert arch.json()["data"]["status"] == "ARCHIVED"

    patch = await admin_client.patch(
        f"/api/v1/admin/notices/{notice_id}",
        json={"title": "改动", "body_md": "x", "channels": ["IN_APP"]},
    )
    assert patch.status_code == 400
    assert patch.json()["code"] == 40030


async def test_notice_endpoints_reject_anonymous_and_student(
    client: AsyncClient, db: AsyncSession,
) -> None:
    resp = await client.get("/api/v1/admin/notices")
    assert resp.status_code == 401

    token, _ = await _login_as_student(
        client, db, student_no="N90001", wx_code="wx_n90001"
    )
    resp2 = await client.get(
        "/api/v1/admin/notices",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 403
