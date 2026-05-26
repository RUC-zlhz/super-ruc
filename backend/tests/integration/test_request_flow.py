"""common-request 闭环 — FR-006 / FR-007 / FR-008 + v1.5 offline-handled。

覆盖：
- draft → submit → claim → approve
- reject → resubmit → approve（revision 自增）
- submit → withdraw
- v1.5：submit → admin 标记 offline → OFFLINE_HANDLED（contact_info 落在 decision_comment）
- FR-008：APPROVED / OFFLINE_HANDLED 等终态由审批角色受控 REOPEN 后重批
- C-03：无 token 401；学生不可审批 → 403
- FR-006：attachment_required 类型无附件不能提交

辅导员（COUNSELOR）承担审批；`_approver_has_role` 按 request_type.approver_roles 过滤，
而种子中 LEAVE_PERSONAL / CERTIFICATE_IN_SCHOOL / REGISTRATION_EVENT 都含 COUNSELOR。
"""
from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.auth.models import Student, User, UserRole
from app.core import storage
from app.core.security import create_token
from app.workflow import pdf_generator
from app.workflow.models import ProofTemplate, RequestType


async def _login_as_student(
    client: AsyncClient,
    db: AsyncSession,
    *,
    student_no: str,
    wx_code: str,
    class_code: str = "CS2201",
) -> str:
    """创建学生 + 走 mock wx-login，返回 access_token。"""
    db.add(
        Student(
            student_no=student_no,
            full_name=f"req-{student_no}",
            grade_code="2022",
            major_code="CS",
            class_code=class_code,
        )
    )
    await db.commit()
    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": wx_code,
            "student_no": student_no,
            "full_name": f"req-{student_no}",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


async def _latest_audit(
    db: AsyncSession,
    *,
    action: str,
    entity_id: int,
) -> AuditLog | None:
    stmt = (
        select(AuditLog)
        .where(AuditLog.action == action, AuditLog.entity_id == entity_id)
        .order_by(AuditLog.id.desc())
    )
    return (await db.execute(stmt)).scalars().first()


async def _headers_for_role(
    db: AsyncSession,
    *,
    role_code: str,
    work_no: str,
    scope_code: str | None = None,
) -> dict[str, str]:
    user = User(work_no=work_no, display_name=f"req-{role_code}", is_active=True)
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_code=role_code, scope_code=scope_code))
    await db.commit()
    token = create_token(str(user.id), "access", extra_claims={"roles": [role_code]})
    return {"Authorization": f"Bearer {token}"}


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

    inbox = await client.get("/api/v1/notices/inbox", headers=stu_headers)
    assert inbox.status_code == 200, inbox.text
    assert any(
        "申请已转线下办理" in item["title"]
        and item["delivery_id"] is not None
        for item in inbox.json()["data"]["items"]
    )

    # 终态不可再次审批
    retry = await client.post(
        f"/api/v1/admin/requests/{request_id}/approve",
        headers=counselor_headers,
        json={"comment": "..."},
    )
    assert retry.status_code == 400


async def test_request_reopen_approved_terminal_to_in_review_records_history_and_audit(
    client: AsyncClient,
    db: AsyncSession,
    counselor_headers: dict[str, str],
) -> None:
    token = await _login_as_student(
        client, db, student_no="R410001", wx_code="wx_r410001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "LEAVE_PERSONAL",
            "title": "重批测试请假",
            "form_data": {
                "reason": "会议冲突",
                "start_date": "2026-04-24",
                "end_date": "2026-04-24",
                "leave_type": "事假",
            },
        },
    )
    assert create.status_code == 200, create.text
    request_id = create.json()["data"]["id"]
    await client.post(f"/api/v1/requests/{request_id}/submit", headers=stu_headers)

    approve = await client.post(
        f"/api/v1/admin/requests/{request_id}/approve",
        headers=counselor_headers,
        json={"comment": "初次通过"},
    )
    assert approve.status_code == 200, approve.text
    assert approve.json()["data"]["status"] == "APPROVED"

    reopen = await client.post(
        f"/api/v1/admin/requests/{request_id}/reopen",
        headers=counselor_headers,
        json={"comment": "发现需补充核验，重开审批"},
    )
    assert reopen.status_code == 200, reopen.text
    reopened = reopen.json()["data"]
    assert reopened["status"] == "IN_REVIEW"
    assert reopened["decided_at"] is None
    assert reopened["decided_by"] is None
    assert reopened["decision_comment"] is None

    reopen_records = [r for r in reopened["approval_records"] if r["action"] == "REOPEN"]
    assert len(reopen_records) == 1
    assert reopen_records[0]["status_before"] == "APPROVED"
    assert reopen_records[0]["status_after"] == "IN_REVIEW"
    assert reopen_records[0]["comment"] == "发现需补充核验，重开审批"

    reopen_log = await _latest_audit(db, action="REOPEN", entity_id=request_id)
    assert reopen_log is not None
    assert reopen_log.result_code == "SUCCESS"

    reapprove = await client.post(
        f"/api/v1/admin/requests/{request_id}/approve",
        headers=counselor_headers,
        json={"comment": "复核后通过"},
    )
    assert reapprove.status_code == 200, reapprove.text
    assert reapprove.json()["data"]["status"] == "APPROVED"


async def test_request_reopen_offline_handled_terminal_can_return_to_submitted(
    client: AsyncClient,
    db: AsyncSession,
    counselor_headers: dict[str, str],
) -> None:
    token = await _login_as_student(
        client, db, student_no="R420001", wx_code="wx_r420001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "CERTIFICATE_IN_SCHOOL",
            "title": "转线下后恢复线上",
            "form_data": {"purpose": "学院证明补充材料"},
        },
    )
    assert create.status_code == 200, create.text
    request_id = create.json()["data"]["id"]
    await client.post(f"/api/v1/requests/{request_id}/submit", headers=stu_headers)

    offline = await client.post(
        f"/api/v1/admin/requests/{request_id}/offline",
        headers=counselor_headers,
        json={"contact_info": "王老师 010-12345678", "note": "需线下核验"},
    )
    assert offline.status_code == 200, offline.text
    assert offline.json()["data"]["status"] == "OFFLINE_HANDLED"

    reopen = await client.post(
        f"/api/v1/admin/requests/{request_id}/reopen",
        headers=counselor_headers,
        json={
            "comment": "材料已转为可线上核验，恢复待受理",
            "target_status": "SUBMITTED",
        },
    )
    assert reopen.status_code == 200, reopen.text
    reopened = reopen.json()["data"]
    assert reopened["status"] == "SUBMITTED"
    assert reopened["decision_comment"] is None
    assert any(
        r["action"] == "REOPEN"
        and r["status_before"] == "OFFLINE_HANDLED"
        and r["status_after"] == "SUBMITTED"
        for r in reopened["approval_records"]
    )


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
    monkeypatch,
) -> None:
    token = await _login_as_student(
        client, db, student_no="R510001", wx_code="wx_r510001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    def _unexpected_minio_client():
        raise AssertionError("test env should use local object storage fallback")

    monkeypatch.setattr(storage, "get_minio_client", _unexpected_minio_client)

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

    preview_log = await _latest_audit(
        db,
        action="PROOF_PREVIEW",
        entity_id=request_id,
    )
    assert preview_log is not None
    assert preview_log.result_code == "SUCCESS"


async def test_proof_preview_uses_active_template_engine(
    client: AsyncClient,
    db: AsyncSession,
    counselor_headers: dict[str, str],
    monkeypatch,
) -> None:
    admin_headers = await _headers_for_role(
        db,
        role_code="SUPER_ADMIN",
        work_no="REQPROOFTPL01",
    )
    upsert = await client.post(
        "/api/v1/admin/proof-templates",
        headers=admin_headers,
        json={
            "code": "CERTIFICATE_IN_SCHOOL_TEST",
            "name": "测试在读证明模板",
            "request_type_code": "CERTIFICATE_IN_SCHOOL",
            "version_label": "test-v1",
            "html_template": (
                "<html><body>"
                "ENGINE {{student.full_name}} {{student.student_no}} "
                "{{form.purpose}} {{request.request_no}}"
                "</body></html>"
            ),
            "is_active": True,
            "is_default": True,
        },
    )
    assert upsert.status_code == 200, upsert.text

    token = await _login_as_student(
        client, db, student_no="R520201", wx_code="wx_r520201"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "CERTIFICATE_IN_SCHOOL",
            "title": "模板引擎证明",
            "form_data": {"purpose": "<交换申请>"},
        },
    )
    assert create.status_code == 200, create.text
    request_id = create.json()["data"]["id"]
    await client.post(f"/api/v1/requests/{request_id}/submit", headers=stu_headers)
    approve = await client.post(
        f"/api/v1/admin/requests/{request_id}/approve",
        headers=counselor_headers,
        json={"comment": "模板引擎通过"},
    )
    assert approve.status_code == 200, approve.text

    captured: dict[str, str] = {}

    def _capture_pdf(html: str) -> bytes:
        captured["html"] = html
        return b"%PDF-1.4 template"

    monkeypatch.setattr(pdf_generator, "_html_to_pdf_bytes", _capture_pdf)
    resp = await client.get(
        f"/api/v1/workflow/proof-preview/{request_id}",
        headers=stu_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.content.startswith(b"%PDF-1.4")
    assert "ENGINE req-R520201 R520201" in captured["html"]
    assert "&lt;交换申请&gt;" in captured["html"]
    assert "<交换申请>" not in captured["html"]


async def test_admin_proof_template_rejects_unknown_placeholder(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    admin_headers = await _headers_for_role(
        db,
        role_code="SUPER_ADMIN",
        work_no="REQPROOFTPL02",
    )
    resp = await client.post(
        "/api/v1/admin/proof-templates",
        headers=admin_headers,
        json={
            "code": "CERTIFICATE_BAD_PLACEHOLDER",
            "name": "错误模板",
            "request_type_code": "CERTIFICATE_IN_SCHOOL",
            "version_label": "bad-v1",
            "html_template": "<html>{{student.id_card_enc}}</html>",
        },
    )
    assert resp.status_code == 400, resp.text
    assert "未授权占位符" in resp.text


async def test_proof_preview_requires_active_template(
    client: AsyncClient,
    db: AsyncSession,
    counselor_headers: dict[str, str],
    monkeypatch,
) -> None:
    db.add(
        RequestType(
            code="CERTIFICATE_NO_TEMPLATE",
            name="无模板证明",
            category="CERTIFICATE",
            description="用于模板缺失回归",
            form_schema={
                "type": "object",
                "required": ["purpose"],
                "properties": {"purpose": {"type": "string", "title": "用途"}},
            },
            attachment_required=False,
            allow_withdraw=True,
            withdraw_hours_limit=72,
            approver_roles="COUNSELOR",
            is_active=True,
        )
    )
    await db.commit()

    token = await _login_as_student(
        client, db, student_no="R520301", wx_code="wx_r520301"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "CERTIFICATE_NO_TEMPLATE",
            "title": "无模板证明",
            "form_data": {"purpose": "测试"},
        },
    )
    assert create.status_code == 200, create.text
    request_id = create.json()["data"]["id"]
    await client.post(f"/api/v1/requests/{request_id}/submit", headers=stu_headers)
    approve = await client.post(
        f"/api/v1/admin/requests/{request_id}/approve",
        headers=counselor_headers,
        json={"comment": "通过"},
    )
    assert approve.status_code == 200, approve.text

    monkeypatch.setattr(pdf_generator, "_html_to_pdf_bytes", lambda _html: b"unexpected")
    resp = await client.get(
        f"/api/v1/workflow/proof-preview/{request_id}",
        headers=stu_headers,
    )
    assert resp.status_code == 400, resp.text
    assert "未配置有效电子证明模板" in resp.text


async def test_admin_can_list_preview_and_deactivate_proof_template(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    admin_headers = await _headers_for_role(
        db,
        role_code="SUPER_ADMIN",
        work_no="REQPROOFTPL03",
    )
    payload = {
        "code": "CERTIFICATE_PREVIEW_TEST",
        "name": "预览测试模板",
        "request_type_code": "CERTIFICATE_IN_SCHOOL",
        "version_label": "preview-v1",
        "html_template": "<html>{{student.full_name}} {{form.purpose}}</html>",
        "field_schema": {"note": "test"},
        "is_active": True,
        "is_default": False,
    }
    upsert = await client.post(
        "/api/v1/admin/proof-templates",
        headers=admin_headers,
        json=payload,
    )
    assert upsert.status_code == 200, upsert.text

    listing = await client.get(
        "/api/v1/admin/proof-templates?request_type_code=CERTIFICATE_IN_SCHOOL",
        headers=admin_headers,
    )
    assert listing.status_code == 200, listing.text
    assert any(
        item["code"] == "CERTIFICATE_PREVIEW_TEST"
        for item in listing.json()["data"]
    )

    preview = await client.post(
        "/api/v1/admin/proof-templates/preview",
        headers=admin_headers,
        json={"html_template": payload["html_template"]},
    )
    assert preview.status_code == 200, preview.text
    assert "张三" in preview.json()["data"]["html"]
    assert "form.purpose" in preview.json()["data"]["placeholders"]

    deactivated = await client.delete(
        "/api/v1/admin/proof-templates/CERTIFICATE_PREVIEW_TEST",
        headers=admin_headers,
    )
    assert deactivated.status_code == 200, deactivated.text
    assert deactivated.json()["data"]["is_active"] is False
    row = (
        await db.execute(
            select(ProofTemplate).where(
                ProofTemplate.code == "CERTIFICATE_PREVIEW_TEST"
            )
        )
    ).scalar_one()
    assert row.is_active is False


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

    denied_log = await _latest_audit(
        db,
        action="READ_DETAIL_DENIED",
        entity_id=request_id,
    )
    assert denied_log is not None
    assert denied_log.result_code == "DENIED"


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


async def test_student_request_create_requires_bound_student_identity(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    headers = await _headers_for_role(
        db,
        role_code="COUNSELOR",
        work_no="REQ-NO-STUDENT",
    )

    resp = await client.post(
        "/api/v1/requests",
        headers=headers,
        json={
            "type_code": "LEAVE_PERSONAL",
            "title": "教师账号不应创建学生侧申请",
            "form_data": {"reason": "权限边界测试"},
        },
    )

    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == 40305


async def test_collaborator_role_can_view_request_workbench_and_detail(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    token = await _login_as_student(
        client, db, student_no="R700001", wx_code="wx_r700001"
    )
    other_token = await _login_as_student(
        client,
        db,
        student_no="R700002",
        wx_code="wx_r700002",
        class_code="CS2202",
    )
    stu_headers = {"Authorization": f"Bearer {token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    async def create_leave_request(headers: dict[str, str], title: str) -> int:
        create = await client.post(
            "/api/v1/requests",
            headers=headers,
            json={
                "type_code": "LEAVE_PERSONAL",
                "title": title,
                "form_data": {
                    "reason": "活动请假",
                    "start_date": "2026-05-18",
                    "end_date": "2026-05-18",
                },
                "summary": "用于权限回归",
            },
        )
        assert create.status_code == 200, create.text
        request_id = create.json()["data"]["id"]
        submit = await client.post(
            f"/api/v1/requests/{request_id}/submit",
            headers=headers,
        )
        assert submit.status_code == 200, submit.text
        return request_id

    request_id = await create_leave_request(stu_headers, "班团骨干查看的请假单")
    other_request_id = await create_leave_request(other_headers, "跨班不可见请假单")

    cadre_headers = await _headers_for_role(
        db,
        role_code="YOUTH_LEAGUE_SECRETARY",
        work_no="REQCADRE01",
        scope_code="CS2201",
    )
    workbench = await client.get("/api/v1/admin/requests", headers=cadre_headers)
    assert workbench.status_code == 200, workbench.text
    items = workbench.json()["data"]["items"]
    assert {item["id"] for item in items} == {request_id}

    detail = await client.get(
        f"/api/v1/requests/{request_id}",
        headers=cadre_headers,
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"]["id"] == request_id

    forbidden_detail = await client.get(
        f"/api/v1/requests/{other_request_id}",
        headers=cadre_headers,
    )
    assert forbidden_detail.status_code == 403, forbidden_detail.text


async def test_collaborator_without_scope_cannot_see_request_workbench(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    token = await _login_as_student(
        client, db, student_no="R710001", wx_code="wx_r710001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "LEAVE_PERSONAL",
            "title": "班团骨干查看的请假单",
            "form_data": {
                "reason": "活动请假",
                "start_date": "2026-05-18",
                "end_date": "2026-05-18",
            },
            "summary": "用于权限回归",
        },
    )
    assert create.status_code == 200, create.text
    request_id = create.json()["data"]["id"]
    submit = await client.post(
        f"/api/v1/requests/{request_id}/submit",
        headers=stu_headers,
    )
    assert submit.status_code == 200, submit.text

    cadre_headers = await _headers_for_role(
        db,
        role_code="YOUTH_LEAGUE_SECRETARY",
        work_no="REQCADRE02",
    )
    workbench = await client.get("/api/v1/admin/requests", headers=cadre_headers)
    assert workbench.status_code == 200, workbench.text
    assert workbench.json()["data"]["items"] == []

    detail = await client.get(
        f"/api/v1/requests/{request_id}",
        headers=cadre_headers,
    )
    assert detail.status_code == 403, detail.text


async def test_collaborator_admin_action_requires_scope_even_for_own_request(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    token = await _login_as_student(
        client, db, student_no="R720001", wx_code="wx_r720001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}
    create = await client.post(
        "/api/v1/requests",
        headers=stu_headers,
        json={
            "type_code": "LEAVE_PERSONAL",
            "title": "本人申请不应绕过协同 scope",
            "form_data": {
                "reason": "活动请假",
                "start_date": "2026-05-18",
                "end_date": "2026-05-18",
            },
            "summary": "用于权限回归",
        },
    )
    assert create.status_code == 200, create.text
    request_id = create.json()["data"]["id"]
    submit = await client.post(
        f"/api/v1/requests/{request_id}/submit",
        headers=stu_headers,
    )
    assert submit.status_code == 200, submit.text

    student = (
        await db.execute(select(Student).where(Student.student_no == "R720001"))
    ).scalar_one()
    user = (await db.execute(select(User).where(User.student_id == student.id))).scalar_one()
    db.add(UserRole(user_id=user.id, role_code="YOUTH_LEAGUE_SECRETARY"))
    request_type = (
        await db.execute(select(RequestType).where(RequestType.code == "LEAVE_PERSONAL"))
    ).scalar_one()
    request_type.approver_roles = "YOUTH_LEAGUE_SECRETARY"
    await db.commit()
    cadre_headers = {
        "Authorization": "Bearer "
        + create_token(
            str(user.id),
            "access",
            extra_claims={
                "roles": ["YOUTH_LEAGUE_SECRETARY"],
                "sid": student.id,
                "ver": user.token_version,
            },
        )
    }

    detail = await client.get(
        f"/api/v1/requests/{request_id}",
        headers=cadre_headers,
    )
    assert detail.status_code == 200, detail.text

    claim = await client.post(
        f"/api/v1/admin/requests/{request_id}/claim",
        headers=cadre_headers,
    )
    assert claim.status_code == 403, claim.text
