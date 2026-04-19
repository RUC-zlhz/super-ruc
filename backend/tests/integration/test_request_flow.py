"""common-request 闭环 — FR-006 / FR-007 / FR-008 + v1.5 offline-handled。

覆盖：
- draft → submit → claim → approve
- reject → resubmit → approve（revision 自增）
- submit → withdraw
- v1.5：submit → admin 标记 offline → OFFLINE_HANDLED（contact_info 落在 decision_comment）
- C-03：无 token 401；学生不可审批 → 403
- FR-006：attachment_required 类型无附件不能提交

辅导员（COUNSELOR）承担审批；`_approver_has_role` 按 request_type.approver_roles 过滤，
而种子中 LEAVE_PERSONAL / CERTIFICATE_IN_SCHOOL / REGISTRATION_EVENT 都含 COUNSELOR。
"""
from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student
from app.workflow import pdf_generator


async def _login_as_student(
    client: AsyncClient, db: AsyncSession, *, student_no: str, wx_code: str
) -> str:
    """创建学生 + 走 mock wx-login，返回 access_token。"""
    db.add(
        Student(
            student_no=student_no,
            full_name=f"req-{student_no}",
            grade_code="2022",
            major_code="CS",
            class_code="CS2201",
        )
    )
    await db.commit()
    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={"code": wx_code, "student_no": student_no},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


async def test_request_happy_path_draft_submit_claim_approve(
    client: AsyncClient,
    db: AsyncSession,
    counselor_headers: dict[str, str],
) -> None:
    token = await _login_as_student(
        client, db, student_no="R100001", wx_code="wx_r100001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    # 1. 创建草稿（LEAVE_PERSONAL 不要求附件）
    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "LEAVE_PERSONAL",
            "title": "本周四请病假一天",
            "form_data": {
                "reason": "发烧就诊",
                "start_date": "2026-04-23",
                "end_date": "2026-04-23",
                "leave_type": "病假",
            },
            "summary": "因病请假",
        },
    )
    assert create.status_code == 200, create.text
    detail = create.json()["data"]
    assert detail["status"] == "DRAFT"
    assert detail["revision"] == 1
    request_id = detail["id"]

    # 2. PATCH 草稿
    patch = await client.patch(
        f"/api/v1/requests/{request_id}",
        headers=stu_headers,
        json={"title": "周四病假 1 天（已就诊）"},
    )
    assert patch.status_code == 200
    assert patch.json()["data"]["title"] == "周四病假 1 天（已就诊）"

    # 3. 提交
    submit = await client.post(
        f"/api/v1/requests/{request_id}/submit", headers=stu_headers
    )
    assert submit.status_code == 200, submit.text
    assert submit.json()["data"]["status"] == "SUBMITTED"

    # 4. 辅导员认领 → IN_REVIEW
    claim = await client.post(
        f"/api/v1/admin/requests/{request_id}/claim",
        headers=counselor_headers,
    )
    assert claim.status_code == 200, claim.text
    assert claim.json()["data"]["status"] == "IN_REVIEW"

    # 5. 审批通过
    approve = await client.post(
        f"/api/v1/admin/requests/{request_id}/approve",
        headers=counselor_headers,
        json={"comment": "已核实，批准"},
    )
    assert approve.status_code == 200, approve.text
    approved = approve.json()["data"]
    assert approved["status"] == "APPROVED"
    assert approved["decision_comment"] == "已核实，批准"
    actions = {r["action"] for r in approved["approval_records"]}
    assert {"SUBMIT", "CLAIM", "APPROVE"}.issubset(actions)


async def test_request_reject_then_resubmit_bumps_revision(
    client: AsyncClient,
    db: AsyncSession,
    counselor_headers: dict[str, str],
) -> None:
    token = await _login_as_student(
        client, db, student_no="R200001", wx_code="wx_r200001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "CERTIFICATE_IN_SCHOOL",
            "title": "在读证明 - 留学申请",
            "form_data": {"purpose": "申请海外交换"},
        },
    )
    request_id = create.json()["data"]["id"]
    await client.post(f"/api/v1/requests/{request_id}/submit", headers=stu_headers)

    # 辅导员驳回
    reject = await client.post(
        f"/api/v1/admin/requests/{request_id}/reject",
        headers=counselor_headers,
        json={"comment": "用途描述不够具体，请补充接收单位"},
    )
    assert reject.status_code == 200, reject.text
    rejected = reject.json()["data"]
    assert rejected["status"] == "REJECTED"
    assert rejected["revision"] == 1

    # 驳回态可改内容（REJECTED 在 editable 集合里）
    patch = await client.patch(
        f"/api/v1/requests/{request_id}",
        headers=stu_headers,
        json={"form_data": {"purpose": "申请 MIT 交换项目，接收方为 MIT CSAIL"}},
    )
    assert patch.status_code == 200

    # 重提 → revision+1
    resubmit = await client.post(
        f"/api/v1/requests/{request_id}/submit", headers=stu_headers
    )
    assert resubmit.status_code == 200
    body = resubmit.json()["data"]
    assert body["status"] == "SUBMITTED"
    assert body["revision"] == 2

    approve = await client.post(
        f"/api/v1/admin/requests/{request_id}/approve",
        headers=counselor_headers,
        json={"comment": "补充充分"},
    )
    assert approve.status_code == 200
    assert approve.json()["data"]["status"] == "APPROVED"


async def test_request_withdraw_after_submit(
    client: AsyncClient, db: AsyncSession
) -> None:
    token = await _login_as_student(
        client, db, student_no="R300001", wx_code="wx_r300001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "REGISTRATION_EVENT",
            "title": "院级团建报名",
            "form_data": {"event_name": "春游"},
        },
    )
    request_id = create.json()["data"]["id"]
    await client.post(f"/api/v1/requests/{request_id}/submit", headers=stu_headers)

    withdraw = await client.post(
        f"/api/v1/requests/{request_id}/withdraw",
        headers=stu_headers,
        json={"comment": "临时有课，不能参加"},
    )
    assert withdraw.status_code == 200, withdraw.text
    withdrawn = withdraw.json()["data"]
    assert withdrawn["status"] == "WITHDRAWN"
    assert withdrawn["withdrawn_at"] is not None
    actions = {r["action"] for r in withdrawn["approval_records"]}
    assert {"SUBMIT", "WITHDRAW"}.issubset(actions)


async def test_request_mark_offline_v15(
    client: AsyncClient,
    db: AsyncSession,
    counselor_headers: dict[str, str],
) -> None:
    """v1.5 涉密/敏感事项 → 审批老师标记转线下办理，终止线上流转。"""
    token = await _login_as_student(
        client, db, student_no="R400001", wx_code="wx_r400001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "CERTIFICATE_IN_SCHOOL",
            "title": "涉密事项证明",
            "form_data": {"purpose": "涉及非公开研究内容"},
        },
    )
    request_id = create.json()["data"]["id"]
    await client.post(f"/api/v1/requests/{request_id}/submit", headers=stu_headers)

    offline = await client.post(
        f"/api/v1/admin/requests/{request_id}/offline",
        headers=counselor_headers,
        json={
            "contact_info": "王老师 010-12345678",
            "note": "材料涉保密实验室，线下当面核验",
        },
    )
    assert offline.status_code == 200, offline.text
    body = offline.json()["data"]
    assert body["status"] == "OFFLINE_HANDLED"
    # 联系方式被写入 decision_comment 便于学生端展示
    assert "王老师" in body["decision_comment"]
    assert "[转线下]" in body["decision_comment"]
    actions = [r["action"] for r in body["approval_records"]]
    assert "OFFLINE_HANDLE" in actions

    # 终态不可再次审批
    retry = await client.post(
        f"/api/v1/admin/requests/{request_id}/approve",
        headers=counselor_headers,
        json={"comment": "..."},
    )
    assert retry.status_code == 400


async def test_request_submit_requires_attachment_when_declared(
    client: AsyncClient, db: AsyncSession
) -> None:
    """STAMP_OFFICIAL 在种子里 attachment_required=True。"""
    token = await _login_as_student(
        client, db, student_no="R500001", wx_code="wx_r500001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "STAMP_OFFICIAL",
            "title": "实习合同盖章",
            "form_data": {
                "purpose": "实习合同学院盖章",
                "file_name": "实习合同.pdf",
            },
        },
    )
    assert create.status_code == 200
    request_id = create.json()["data"]["id"]

    # 没传附件直接提交 → 失败
    submit = await client.post(
        f"/api/v1/requests/{request_id}/submit", headers=stu_headers
    )
    assert submit.status_code == 400, submit.text


async def test_request_detail_contract_uses_canonical_attachment_and_approval_fields(
    client: AsyncClient,
    db: AsyncSession,
    counselor_headers: dict[str, str],
) -> None:
    token = await _login_as_student(
        client, db, student_no="R510001", wx_code="wx_r510001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "STAMP_OFFICIAL",
            "title": "三方协议盖章",
            "form_data": {
                "purpose": "就业协议学院盖章",
                "company_name": "OpenAI",
            },
            "summary": "S1 contract regression",
        },
    )
    assert create.status_code == 200, create.text
    request_id = create.json()["data"]["id"]

    upload = await client.post(
        f"/api/v1/requests/{request_id}/attachments",
        headers=stu_headers,
        files={"file": ("agreement.pdf", b"%PDF-1.4 test", "application/pdf")},
    )
    assert upload.status_code == 200, upload.text
    attachment = upload.json()["data"]
    assert attachment["filename"] == "agreement.pdf"
    assert attachment["mime_type"] == "application/pdf"
    assert "file_name" not in attachment

    submit = await client.post(
        f"/api/v1/requests/{request_id}/submit", headers=stu_headers
    )
    assert submit.status_code == 200, submit.text

    offline = await client.post(
        f"/api/v1/admin/requests/{request_id}/offline",
        headers=counselor_headers,
        json={
            "contact_info": "李老师 010-88886666",
            "note": "合同原件需线下核验",
        },
    )
    assert offline.status_code == 200, offline.text
    offline_data = offline.json()["data"]
    assert offline_data["status"] == "OFFLINE_HANDLED"
    assert any(r["action"] == "OFFLINE_HANDLE" for r in offline_data["approval_records"])

    detail = await client.get(f"/api/v1/requests/{request_id}", headers=stu_headers)
    assert detail.status_code == 200, detail.text
    detail_data = detail.json()["data"]
    assert detail_data["attachments"][0]["filename"] == "agreement.pdf"
    assert "file_name" not in detail_data["attachments"][0]
    assert any("operator_id" in row for row in detail_data["approval_records"])
    assert all("operator_user_id" not in row for row in detail_data["approval_records"])
    assert any("occurred_at" in row for row in detail_data["approval_records"])
    assert all("operated_at" not in row for row in detail_data["approval_records"])
    assert any(row["action"] == "OFFLINE_HANDLE" for row in detail_data["approval_records"])


async def test_proof_preview_returns_pdf_stream(
    client: AsyncClient,
    db: AsyncSession,
    counselor_headers: dict[str, str],
    monkeypatch,
) -> None:
    token = await _login_as_student(
        client, db, student_no="R520001", wx_code="wx_r520001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "CERTIFICATE_IN_SCHOOL",
            "title": "在读证明预览",
            "form_data": {"purpose": "交换申请"},
            "summary": "用于 S1 proof-preview contract",
        },
    )
    assert create.status_code == 200, create.text
    request_id = create.json()["data"]["id"]

    submit = await client.post(
        f"/api/v1/requests/{request_id}/submit", headers=stu_headers
    )
    assert submit.status_code == 200, submit.text

    approve = await client.post(
        f"/api/v1/admin/requests/{request_id}/approve",
        headers=counselor_headers,
        json={"comment": "通过，用于生成 PDF"},
    )
    assert approve.status_code == 200, approve.text

    monkeypatch.setattr(pdf_generator, "_html_to_pdf_bytes", lambda _html: b"%PDF-1.4 mock")

    resp = await client.get(
        f"/api/v1/workflow/proof-preview/{request_id}",
        headers=stu_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/pdf")
    assert "inline;" in resp.headers["content-disposition"]
    assert resp.content.startswith(b"%PDF-1.4")


async def test_proof_preview_rejects_other_student(
    client: AsyncClient,
    db: AsyncSession,
    counselor_headers: dict[str, str],
    monkeypatch,
) -> None:
    owner_token = await _login_as_student(
        client, db, student_no="R520101", wx_code="wx_r520101"
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_token = await _login_as_student(
        client, db, student_no="R520102", wx_code="wx_r520102"
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}

    create = await client.post(
        "/api/v1/requests",
        headers=owner_headers,
        json={
            "type_code": "CERTIFICATE_IN_SCHOOL",
            "title": "在读证明权限测试",
            "form_data": {"purpose": "签证"},
        },
    )
    assert create.status_code == 200, create.text
    request_id = create.json()["data"]["id"]

    submit = await client.post(
        f"/api/v1/requests/{request_id}/submit", headers=owner_headers
    )
    assert submit.status_code == 200, submit.text

    approve = await client.post(
        f"/api/v1/admin/requests/{request_id}/approve",
        headers=counselor_headers,
        json={"comment": "通过"},
    )
    assert approve.status_code == 200, approve.text

    monkeypatch.setattr(pdf_generator, "_html_to_pdf_bytes", lambda _html: b"%PDF-1.4 mock")

    resp = await client.get(
        f"/api/v1/workflow/proof-preview/{request_id}",
        headers=other_headers,
    )
    assert resp.status_code == 403, resp.text


async def test_request_endpoints_reject_anonymous_and_student_role(
    client: AsyncClient, db: AsyncSession
) -> None:
    """C-03 后端鉴权：无 token 401，学生无管理员权限 403。"""
    resp = await client.get("/api/v1/admin/requests")
    assert resp.status_code == 401

    token = await _login_as_student(
        client, db, student_no="R600001", wx_code="wx_r600001"
    )
    resp = await client.get(
        "/api/v1/admin/requests",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
