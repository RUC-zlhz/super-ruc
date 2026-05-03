"""notice 闭环 — FR-010 目标人群 + FR-011 发送批次与送达记录。

覆盖：
- admin create → target-preview（按 grade/major/political_status/role_codes 过滤）
- publish → dispatch（IN_APP + SMS，IN_APP=SENT / SMS=SKIPPED）
- 学生 GET /notices/inbox 看到自己那条；mark-read 后 read_at 落库
- DRAFT 通知不能直接 dispatch；ARCHIVED 通知不能修改
- 管理员 GET /{notice}/batches 与 /batches/{id}/deliveries 返回分页
- C-03：匿名访问 401，普通学生访问 /admin/notices 403
"""
from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student, User, UserRole
from app.core.security import encrypt_field


async def _login_as_student(
    client: AsyncClient, db: AsyncSession, *,
    student_no: str, wx_code: str,
    grade_code: str = "2022", major_code: str = "CS", class_code: str = "CS2201",
    political_status: str | None = None,
    email: str | None = None,
) -> tuple[str, int]:
    stu = Student(
        student_no=student_no, full_name=f"n-{student_no}",
        grade_code=grade_code, major_code=major_code, class_code=class_code,
        political_status=political_status,
        email=email,
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


async def _seed_broadcast_students(db: AsyncSession) -> dict[str, int]:
    """写一批覆盖多 grade/major/political_status/毕业状态的学生，用于 target-preview。"""
    students = [
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
        Student(student_no="N10005", full_name="已毕业党员",
                grade_code="2020", major_code="CS", class_code="CS2001",
                political_status="中共党员", graduation_flag=True, status="GRADUATED"),
    ]
    db.add_all(students)
    await db.flush()
    student_ids = {row.student_no: row.id for row in students}
    await db.commit()
    return student_ids


async def _bind_student_roles(
    db: AsyncSession,
    *,
    student_id: int,
    work_no: str,
    role_codes: list[str],
) -> None:
    user = User(
        work_no=work_no,
        display_name=f"notice-{work_no}",
        student_id=student_id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    effective_role_codes: list[str] = []
    for role_code in ["STUDENT", *role_codes]:
        if role_code in effective_role_codes:
            continue
        effective_role_codes.append(role_code)
        db.add(UserRole(user_id=user.id, role_code=role_code))
    await db.commit()


async def test_target_preview_filters_by_grade_major_and_political_status(
    db: AsyncSession, admin_client: AsyncClient,
) -> None:
    student_ids = await _seed_broadcast_students(db)
    await _bind_student_roles(
        db, student_id=student_ids["N10001"], work_no="NROLE10001", role_codes=["PARTY_BACKBONE"]
    )
    await _bind_student_roles(
        db, student_id=student_ids["N10003"], work_no="NROLE10003", role_codes=["PARTY_BACKBONE"]
    )
    await _bind_student_roles(
        db, student_id=student_ids["N10005"], work_no="NROLE10005", role_codes=["PARTY_BACKBONE"]
    )

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

    # role_codes 也参与命中，默认仍排除已毕业学生
    resp = await admin_client.post(
        "/api/v1/admin/notices/target-preview",
        json={"target_rule": {"role_codes": ["PARTY_BACKBONE"]}},
    )
    assert resp.status_code == 200, resp.text
    r = resp.json()["data"]
    assert r["target_count"] == 2
    assert set(r["sample_student_nos"]) == {"N10001", "N10003"}

    # 显式关闭排除毕业生后，已毕业学生也会命中
    resp = await admin_client.post(
        "/api/v1/admin/notices/target-preview",
        json={
            "target_rule": {
                "role_codes": ["PARTY_BACKBONE"],
                "exclude_graduated": False,
            }
        },
    )
    assert resp.status_code == 200, resp.text
    r = resp.json()["data"]
    assert r["target_count"] == 3
    assert set(r["sample_student_nos"]) == {"N10001", "N10003", "N10005"}

    # 空规则 = 全部在读
    resp = await admin_client.post(
        "/api/v1/admin/notices/target-preview", json={"target_rule": None},
    )
    assert resp.json()["data"]["target_count"] == 4


async def test_notice_publish_dispatch_and_student_inbox(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient,
) -> None:
    # 1. 先建一个目标学生（2022 CS 党员）
    token, student_id = await _login_as_student(
        client, db, student_no="N20001", wx_code="wx_n20001",
        political_status="中共党员",
    )
    stu_headers = {"Authorization": f"Bearer {token}"}
    other_token, _ = await _login_as_student(
        client,
        db,
        student_no="N20002",
        wx_code="wx_n20002",
        political_status="群众",
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}

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
    assert "delivery_id" in item
    assert "read_at" in item
    assert "is_read" not in item
    assert item["read_at"] is None
    delivery_id = item["delivery_id"]

    # 7. 详情走 canonical notice_id，返回 NoticeOut 而不是学生端旧别名
    detail = await client.get(f"/api/v1/notices/{notice_id}", headers=stu_headers)
    assert detail.status_code == 200, detail.text
    detail_data = detail.json()["data"]
    assert detail_data["id"] == notice_id
    assert detail_data["body_md"] == "## 议程\n1. 学习材料\n2. 组织生活"
    assert "body" not in detail_data
    assert set(detail_data["tags"]) == {"党员", "例会"}

    admin_detail = await admin_client.get(f"/api/v1/notices/{notice_id}")
    assert admin_detail.status_code == 200, admin_detail.text
    admin_detail_data = admin_detail.json()["data"]
    assert admin_detail_data["source_type"] == "MANUAL"
    assert admin_detail_data["channels"] == "IN_APP,SMS"

    other_detail = await client.get(
        f"/api/v1/notices/{notice_id}",
        headers=other_headers,
    )
    assert other_detail.status_code == 404

    other_mark = await client.post(
        f"/api/v1/notices/read/{delivery_id}",
        headers=other_headers,
    )
    assert other_mark.status_code == 404

    # 8. mark-read → 再查 unread_only=true 应为空
    mark = await client.post(
        f"/api/v1/notices/read/{delivery_id}", headers=stu_headers,
    )
    assert mark.status_code == 200

    unread = await client.get(
        "/api/v1/notices/inbox", params={"unread_only": True}, headers=stu_headers,
    )
    assert unread.json()["data"]["meta"]["total"] == 0

    # 9. admin 查批次 + 投递明细
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
    in_app_row = next(d for d in dlist if d["channel"] == "IN_APP")
    assert in_app_row["target_handle"] is None
    assert sms_row["error_code"] == "SMS_DISABLED"
    assert "target_handle" in sms_row


async def test_notice_email_dispatch_records_delivery(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient, monkeypatch,
) -> None:
    token, student_id = await _login_as_student(
        client, db, student_no="N20021", wx_code="wx_n20021",
        political_status="中共党员",
        email="n20021@example.com",
    )

    create = await admin_client.post(
        "/api/v1/admin/notices",
        json={
            "title": "邮件通知测试",
            "body_md": "正文",
            "summary": "邮件通知摘要",
            "category": "PARTY",
            "target_rule": {
                "grade_codes": ["2022"],
                "major_codes": ["CS"],
                "political_status": ["中共党员"],
            },
            "channels": ["EMAIL"],
        },
    )
    assert create.status_code == 200, create.text
    notice_id = create.json()["data"]["id"]

    await admin_client.post(f"/api/v1/admin/notices/{notice_id}/publish")

    from app.notice import service as notice_service

    def fake_send_email(to_addr: str, subject: str, body: str):
        return True, None

    monkeypatch.setattr(notice_service, "_send_email", fake_send_email)

    dispatch = await admin_client.post(
        f"/api/v1/admin/notices/{notice_id}/dispatch",
        json={},
    )
    assert dispatch.status_code == 200, dispatch.text
    batch = dispatch.json()["data"]
    assert batch["status"] == "COMPLETED"
    assert batch["success_count"] == 1
    assert batch["failed_count"] == 0

    deliveries = await admin_client.get(
        f"/api/v1/admin/notices/batches/{batch['id']}/deliveries",
    )
    assert deliveries.status_code == 200, deliveries.text
    rows = deliveries.json()["data"]["items"]
    assert len(rows) == 1
    row = rows[0]
    assert row["channel"] == "EMAIL"
    assert row["status"] == "SENT"
    assert row["target_handle"] is not None


async def test_notice_sms_enabled_uses_phone_and_masks_delivery_handle(
    client: AsyncClient,
    db: AsyncSession,
    admin_client: AsyncClient,
    monkeypatch,
) -> None:
    token, student_id = await _login_as_student(
        client,
        db,
        student_no="N20031",
        wx_code="wx_n20031",
        political_status="中共党员",
    )
    user = (
        await db.execute(select(User).where(User.student_id == student_id))
    ).scalar_one()
    user.phone_enc = encrypt_field("13800138000")
    await db.commit()

    create = await admin_client.post(
        "/api/v1/admin/notices",
        json={
            "title": "短信通知测试",
            "body_md": "正文",
            "summary": "短信摘要",
            "category": "PARTY",
            "target_rule": {"political_status": ["中共党员"]},
            "channels": ["SMS"],
        },
    )
    assert create.status_code == 200, create.text
    notice_id = create.json()["data"]["id"]
    await admin_client.post(f"/api/v1/admin/notices/{notice_id}/publish")

    from app.notice import service as notice_service

    sent_to: list[str] = []

    def fake_send_sms(to_number: str, body: str):
        sent_to.append(to_number)
        return True, None

    monkeypatch.setattr(notice_service.settings, "SMS_ENABLED", True)
    monkeypatch.setattr(notice_service, "_send_sms", fake_send_sms)

    dispatch = await admin_client.post(f"/api/v1/admin/notices/{notice_id}/dispatch", json={})
    assert dispatch.status_code == 200, dispatch.text
    assert sent_to == ["13800138000"]

    deliveries = await admin_client.get(
        f"/api/v1/admin/notices/batches/{dispatch.json()['data']['id']}/deliveries",
    )
    row = deliveries.json()["data"]["items"][0]
    assert row["status"] == "SENT"
    assert row["target_handle"] == "138****8000"


async def test_notice_sms_enabled_without_phone_is_not_sent(
    client: AsyncClient,
    db: AsyncSession,
    admin_client: AsyncClient,
    monkeypatch,
) -> None:
    await _login_as_student(
        client,
        db,
        student_no="N20032",
        wx_code="wx_n20032",
        political_status="中共党员",
    )
    create = await admin_client.post(
        "/api/v1/admin/notices",
        json={
            "title": "无手机号短信通知测试",
            "body_md": "正文",
            "summary": "短信摘要",
            "category": "PARTY",
            "target_rule": {"political_status": ["中共党员"]},
            "channels": ["SMS"],
        },
    )
    notice_id = create.json()["data"]["id"]
    await admin_client.post(f"/api/v1/admin/notices/{notice_id}/publish")

    from app.notice import service as notice_service

    def should_not_send(_to_number: str, _body: str):
        raise AssertionError("SMS gateway should not be called without phone")

    monkeypatch.setattr(notice_service.settings, "SMS_ENABLED", True)
    monkeypatch.setattr(notice_service, "_send_sms", should_not_send)

    dispatch = await admin_client.post(f"/api/v1/admin/notices/{notice_id}/dispatch", json={})
    assert dispatch.status_code == 200, dispatch.text
    batch = dispatch.json()["data"]
    assert batch["success_count"] == 0
    assert batch["failed_count"] == 0
    deliveries = await admin_client.get(
        f"/api/v1/admin/notices/batches/{batch['id']}/deliveries",
    )
    row = deliveries.json()["data"]["items"][0]
    assert row["status"] == "SKIPPED"
    assert row["error_code"] == "NO_PHONE"


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
