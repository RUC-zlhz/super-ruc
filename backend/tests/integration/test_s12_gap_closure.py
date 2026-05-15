"""S12 需求缺口闭环集成测试。"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student, User, UserRole
from app.core.config import settings
from app.core.security import create_token, encrypt_field
from app.exchange import repository as exchange_repo
from app.exchange.models import (
    BATCH_STATUS_COMMITTED,
    BATCH_STATUS_VALIDATED,
    IMPORT_TYPE_TRANSCRIPT_PDF_REVIEW,
    CurriculumModule,
    CurriculumPlan,
    StudentCourseRecord,
)
from app.knowledge.models import TemplateAsset
from app.notice import service as notice_service
from app.notice.models import DELIVERY_STATUS_SENT, NOTICE_STATUS_DRAFT, Notice, NoticeDelivery
from app.workflow.models import (
    Request,
    RequestType,
    StudentWorkflow,
    StudentWorkflowNode,
    WorkflowNode,
    WorkflowTemplate,
)


async def _student_headers(
    db: AsyncSession,
    *,
    student: Student,
    work_no: str,
    phone: str | None = None,
) -> tuple[dict[str, str], User]:
    user = User(
        work_no=work_no,
        display_name=student.full_name,
        student_id=student.id,
        phone_enc=encrypt_field(phone) if phone else None,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_code="STUDENT"))
    await db.commit()
    token = create_token(str(user.id), "access", extra_claims={"roles": ["STUDENT"], "sid": student.id})
    return {"Authorization": f"Bearer {token}"}, user


async def test_default_imports_students_curriculum_and_gap_suggestions(
    admin_client: AsyncClient,
    db: AsyncSession,
) -> None:
    student_import = await admin_client.post("/api/v1/admin/default-imports/students")
    assert student_import.status_code == 200, student_import.text
    student_result = student_import.json()["data"]
    assert student_result["import_type"] == "DEFAULT_STUDENTS"
    assert student_result["created_count"] >= 1

    imported_student = (
        await db.execute(select(Student).where(Student.student_no == "2024201540"))
    ).scalar_one()
    assert imported_student.full_name == "张念昊"
    assert imported_student.gender == "男"
    assert imported_student.expected_graduation_year == 2028
    assert imported_student.grade_code is None
    assert imported_student.major_code is None
    assert imported_student.class_code is None

    non_default = CurriculumPlan(
        grade_code="2024",
        major_code="信息安全",
        plan_name="教师维护的信息安全培养方案",
        version_label="teacher-v1",
        is_active=True,
    )
    db.add(non_default)
    await db.commit()

    curriculum_import = await admin_client.post("/api/v1/admin/default-imports/curriculum")
    assert curriculum_import.status_code == 200, curriculum_import.text
    curriculum_result = curriculum_import.json()["data"]
    assert curriculum_result["import_type"] == "DEFAULT_CURRICULUM"
    assert curriculum_result["total_rows"] == 6
    assert curriculum_result["created_count"] == 6

    default_plans = (
        await db.execute(
            select(CurriculumPlan).where(CurriculumPlan.version_label == "2024-default")
        )
    ).scalars().all()
    assert {plan.major_code for plan in default_plans} >= {
        "计算机科学与技术",
        "信息管理与信息系统",
        "软件工程",
        "信息安全",
        "数据科学与大数据技术",
        "数据科学与大数据技术（理学）",
    }
    refreshed_non_default = (
        await db.execute(
            select(CurriculumPlan).where(CurriculumPlan.version_label == "teacher-v1")
        )
    ).scalar_one()
    assert refreshed_non_default.plan_name == "教师维护的信息安全培养方案"

    info_security_plan = (
        await db.execute(
            select(CurriculumPlan).where(
                CurriculumPlan.grade_code == "2024",
                CurriculumPlan.major_code == "信息安全",
                CurriculumPlan.version_label == "2024-default",
            )
        )
    ).scalar_one()
    modules = (
        await db.execute(select(CurriculumModule).where(CurriculumModule.plan_id == info_security_plan.id))
    ).scalars().all()
    assert modules
    all_course_codes = {
        course["code"]
        for module in modules
        for course in (module.courses or [])
        if isinstance(course, dict) and course.get("code")
    }
    assert "BISYMS0012" in all_course_codes
    assert "BCSAMSS0001S" not in all_course_codes

    gap_student = Student(
        student_no="S12-GAP-001",
        full_name="S12 缺口学生",
        grade_code="2024",
        major_code="信息安全",
        class_code="IS2401",
    )
    db.add(gap_student)
    await db.commit()
    await db.refresh(gap_student)

    gap = await admin_client.get(f"/api/v1/admin/report/academic-gap/{gap_student.id}")
    assert gap.status_code == 200, gap.text
    gap_data = gap.json()["data"]
    suggested_codes = {item["course_code"] for item in gap_data["suggested_courses"]}
    assert "BISYMS0012" in suggested_codes
    assert any("开课数据" in warning for warning in gap_data["data_warnings"])
    assert any(
        item["capacity_status"] == "数据未配置" and item["prerequisite_status"] == "数据未配置"
        for item in gap_data["suggested_courses"]
    )


async def test_transcript_pdf_review_commit_writes_formal_records(
    admin_client: AsyncClient,
    db: AsyncSession,
) -> None:
    student = Student(student_no="S12-PDF-001", full_name="PDF 核验学生", grade_code="2024", major_code="CS")
    db.add(student)
    await db.flush()
    batch = await exchange_repo.create_batch(
        db,
        batch_no="IM-TPDF-S12-001",
        import_type=IMPORT_TYPE_TRANSCRIPT_PDF_REVIEW,
        filename="transcript.pdf",
        file_size=256,
        mime_type="application/pdf",
        operator_id=None,
        operator_role="STUDENT",
    )
    await exchange_repo.finalize_batch(
        db,
        batch,
        status=BATCH_STATUS_VALIDATED,
        total_rows=1,
        ok_rows=0,
        warn_rows=1,
        fatal_rows=0,
        summary={"student_id": student.id, "formal_records_written": 0, "review_required": True},
    )
    await db.commit()

    detail = await admin_client.get(f"/api/v1/admin/exchange/imports/{batch.id}")
    assert detail.status_code == 200, detail.text
    detail_data = detail.json()["data"]
    assert detail_data["batch"]["summary"]["student_id"] == student.id
    assert detail_data["batch"]["summary"]["review_required"] is True

    commit = await admin_client.post(
        f"/api/v1/admin/report/transcript-pdf-reviews/{batch.id}/commit",
        json={
            "records": [
                {
                    "line_no": 1,
                    "course_code": "CS101",
                    "course_name": "程序设计",
                    "credits": 3,
                    "term_code": "2025-FALL",
                    "score": 88,
                    "pass_flag": True,
                }
            ],
            "note": "人工核验通过",
        },
    )
    assert commit.status_code == 200, commit.text
    data = commit.json()["data"]
    assert data["status"] == BATCH_STATUS_COMMITTED
    assert data["formal_records_written"] == 1

    committed_detail = await admin_client.get(f"/api/v1/admin/exchange/imports/{batch.id}")
    assert committed_detail.status_code == 200, committed_detail.text
    committed_summary = committed_detail.json()["data"]["batch"]["summary"]
    assert committed_summary["formal_records_written"] == 1
    assert committed_summary["review_note"] == "人工核验通过"
    assert committed_summary["reviewed_at"]

    record = (
        await db.execute(
            select(StudentCourseRecord).where(
                StudentCourseRecord.student_id == student.id,
                StudentCourseRecord.course_code == "CS101",
            )
        )
    ).scalar_one()
    assert record.term_code == "2025-FALL"
    assert record.pass_flag is True
    assert record.imported_batch_id == batch.id


async def test_knowledge_templates_permission_and_official_source_priority(
    client: AsyncClient,
    admin_client: AsyncClient,
    db: AsyncSession,
) -> None:
    official_source = await admin_client.post(
        "/api/v1/admin/knowledge/sources",
        json={
            "source_name": "学院官网办事指南",
            "source_url": "https://info.ruc.edu.cn/service/template",
            "version_label": "2026",
            "is_official": True,
        },
    )
    assert official_source.status_code == 200, official_source.text
    assert official_source.json()["data"]["is_official"] is True
    unofficial_source = await admin_client.post(
        "/api/v1/admin/knowledge/sources",
        json={
            "source_name": "内部草稿来源",
            "source_url": "https://draft.example.edu/template",
            "version_label": "draft",
            "is_official": False,
        },
    )
    assert unofficial_source.status_code == 200, unofficial_source.text
    assert unofficial_source.json()["data"]["is_official"] is False

    linked_template = await admin_client.post(
        "/api/v1/admin/knowledge/templates",
        data={
            "template_name": "成绩证明模板",
            "template_type": "DOCX",
            "category_code": "CERTIFICATE",
            "applicable_scenario": "成绩证明申请",
            "version_label": "2026",
        },
        files={
            "file": (
                "grade-proof.docx",
                b"template-bytes",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert linked_template.status_code == 200, linked_template.text
    linked_template_id = linked_template.json()["data"]["id"]
    unlinked_template = await admin_client.post(
        "/api/v1/admin/knowledge/templates",
        data={"template_name": "未发布模板", "template_type": "DOCX"},
        files={"file": ("draft.docx", b"draft-bytes", "application/octet-stream")},
    )
    assert unlinked_template.status_code == 200, unlinked_template.text
    unlinked_template_id = unlinked_template.json()["data"]["id"]

    official_entry = await admin_client.post(
        "/api/v1/admin/knowledge/entries",
        json={
            "slug": "s12-official-template",
            "title": "成绩证明模板下载",
            "summary": "成绩证明模板下载",
            "category_code": "CERTIFICATE",
            "body_md": "按学院官网模板办理。",
            "source_id": official_source.json()["data"]["id"],
            "template_ids": [linked_template_id],
        },
    )
    assert official_entry.status_code == 200, official_entry.text
    await admin_client.post(
        f"/api/v1/admin/knowledge/entries/{official_entry.json()['data']['id']}/publish",
        json={},
    )
    unofficial_entry = await admin_client.post(
        "/api/v1/admin/knowledge/entries",
        json={
            "slug": "s12-unofficial-template",
            "title": "成绩证明模板下载",
            "summary": "成绩证明模板下载",
            "category_code": "CERTIFICATE",
            "body_md": "内部草稿。",
            "source_id": unofficial_source.json()["data"]["id"],
        },
    )
    assert unofficial_entry.status_code == 200, unofficial_entry.text
    await admin_client.post(
        f"/api/v1/admin/knowledge/entries/{unofficial_entry.json()['data']['id']}/publish",
        json={},
    )

    student = Student(student_no="S12-KNOW-001", full_name="模板学生")
    db.add(student)
    await db.commit()
    await db.refresh(student)
    student_headers, _ = await _student_headers(db, student=student, work_no="S12-KNOW-U")

    search = await client.get(
        "/api/v1/knowledge/search",
        headers=student_headers,
        params={"q": "成绩证明模板下载"},
    )
    assert search.status_code == 200, search.text
    first_hit = search.json()["data"]["items"][0]
    assert first_hit["slug"] == "s12-official-template"
    assert first_hit["source_name"] == "学院官网办事指南"
    assert first_hit["source_url"] == "https://info.ruc.edu.cn/service/template"
    assert first_hit["source_is_official"] is True

    ai_match = await client.post(
        "/api/v1/knowledge/ai-match",
        headers=student_headers,
        json={"query": "成绩证明模板下载", "top_k": 2},
    )
    assert ai_match.status_code == 200, ai_match.text
    first_candidate = ai_match.json()["data"]["candidates"][0]
    assert first_candidate["slug"] == "s12-official-template"
    assert first_candidate["source_is_official"] is True

    templates = await client.get("/api/v1/knowledge/templates", headers=student_headers)
    assert templates.status_code == 200, templates.text
    template_ids = {item["id"] for item in templates.json()["data"]["items"]}
    assert linked_template_id in template_ids
    assert unlinked_template_id not in template_ids

    linked_download = await client.get(
        f"/api/v1/knowledge/templates/{linked_template_id}/download",
        headers=student_headers,
    )
    assert linked_download.status_code == 200, linked_download.text
    unlinked_download = await client.get(
        f"/api/v1/knowledge/templates/{unlinked_template_id}/download",
        headers=student_headers,
    )
    assert unlinked_download.status_code == 404
    admin_unlinked_download = await admin_client.get(
        f"/api/v1/admin/knowledge/templates/{unlinked_template_id}/download"
    )
    assert admin_unlinked_download.status_code == 200, admin_unlinked_download.text

    await admin_client.delete(f"/api/v1/admin/knowledge/templates/{linked_template_id}")
    inactive_download = await admin_client.get(
        f"/api/v1/admin/knowledge/templates/{linked_template_id}/download"
    )
    assert inactive_download.status_code == 404

    linked_template_row = await db.get(TemplateAsset, linked_template_id)
    assert linked_template_row is not None
    assert linked_template_row.status == "DEPRECATED"


async def test_progress_center_aggregates_requests_and_workflows(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    student = Student(student_no="S12-PROG-001", full_name="进度学生")
    db.add(student)
    await db.commit()
    await db.refresh(student)
    headers, user = await _student_headers(db, student=student, work_no="S12-PROG-U")

    request_type = RequestType(code="S12_REQ", name="S12 事务", category="OTHER")
    db.add(request_type)
    await db.flush()
    request = Request(
        request_no="REQ-S12-PROG-001",
        type_id=request_type.id,
        type_code=request_type.code,
        applicant_user_id=user.id,
        applicant_student_id=student.id,
        title="成绩证明申请",
        form_data={},
        status="SUBMITTED",
        decision_comment="辅导员审核",
    )
    template = WorkflowTemplate(code="S12_WF", name="S12 党团流程", kind="PARTY", is_active=True)
    db.add_all([request, template])
    await db.flush()
    node = WorkflowNode(template_id=template.id, code="APPLY", name="提交申请书", sort_order=1)
    db.add(node)
    await db.flush()
    workflow = StudentWorkflow(
        student_id=student.id,
        template_id=template.id,
        status="ACTIVE",
        current_node_id=node.id,
    )
    db.add(workflow)
    await db.flush()
    db.add(
        StudentWorkflowNode(
            workflow_id=workflow.id,
            node_id=node.id,
            status="PENDING",
            due_date=(datetime.now(UTC) + timedelta(days=7)).date(),
        )
    )
    await db.commit()

    resp = await client.get("/api/v1/progress/my", headers=headers)
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]["items"]
    by_type = {item["source_type"]: item for item in items}
    assert by_type["REQUEST"]["title"] == "成绩证明申请"
    assert by_type["REQUEST"]["detail_url"] == f"/pages/request/detail?id={request.id}"
    assert by_type["WORKFLOW"]["current_step"] == "提交申请书"
    assert by_type["WORKFLOW"]["detail_url"] == f"/pages/workflow/detail?id={workflow.id}"


async def test_notice_ingest_sources_and_sms_retry_receipt(
    client: AsyncClient,
    admin_client: AsyncClient,
    db: AsyncSession,
    monkeypatch,
) -> None:
    class FakeResponse:
        content = (
            b"<rss><channel><item><title>S12 RSS Notice</title>"
            b"<link>https://info.ruc.edu.cn/rss/s12</link>"
            b"<description>S12 RSS body</description></item></channel></rss>"
        )

        def raise_for_status(self) -> None:
            return None

    class FakeAsyncClient:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        async def __aenter__(self) -> FakeAsyncClient:
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        async def get(self, _url: str) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(notice_service.httpx, "AsyncClient", FakeAsyncClient)

    source = await admin_client.post(
        "/api/v1/admin/notices/sources",
        json={
            "name": "学院公开 RSS",
            "source_type": "RSS",
            "source_url": "https://info.ruc.edu.cn/rss.xml",
            "category": "ACADEMIC",
        },
    )
    assert source.status_code == 200, source.text
    source_id = source.json()["data"]["id"]

    run = await admin_client.post(f"/api/v1/admin/notices/sources/{source_id}/run")
    assert run.status_code == 200, run.text
    run_data = run.json()["data"]
    assert run_data["fetched_count"] == 1
    assert run_data["created_count"] == 1
    draft_notice = (
        await db.execute(select(Notice).where(Notice.source_url == "https://info.ruc.edu.cn/rss/s12"))
    ).scalar_one()
    assert draft_notice.status == NOTICE_STATUS_DRAFT

    rerun = await admin_client.post(f"/api/v1/admin/notices/sources/{source_id}/run")
    assert rerun.status_code == 200, rerun.text
    assert rerun.json()["data"]["skipped_count"] == 1
    runs = await admin_client.get("/api/v1/admin/notices/ingest-runs", params={"source_id": source_id})
    assert runs.status_code == 200, runs.text
    assert runs.json()["data"]["meta"]["total"] == 2

    sms_student = Student(
        student_no="S12-SMS-001",
        full_name="短信学生",
        grade_code="2024",
        major_code="CS",
        phone_enc=encrypt_field("13800138000"),
    )
    db.add(sms_student)
    await db.commit()
    await db.refresh(sms_student)
    await _student_headers(
        db,
        student=sms_student,
        work_no="S12-SMS-U",
        phone="13800138000",
    )

    monkeypatch.setattr(settings, "SMS_ENABLED", False)
    notice = await admin_client.post(
        "/api/v1/admin/notices",
        json={
            "title": "短信通知治理",
            "body_md": "短信通知治理",
            "summary": "短信通知治理",
            "target_rule": {"grade_codes": ["2024"], "major_codes": ["CS"]},
            "channels": ["SMS"],
        },
    )
    assert notice.status_code == 200, notice.text
    notice_id = notice.json()["data"]["id"]
    await admin_client.post(f"/api/v1/admin/notices/{notice_id}/publish")
    dispatch = await admin_client.post(f"/api/v1/admin/notices/{notice_id}/dispatch", json={})
    assert dispatch.status_code == 200, dispatch.text
    batch_id = dispatch.json()["data"]["id"]
    deliveries = await admin_client.get(f"/api/v1/admin/notices/batches/{batch_id}/deliveries")
    delivery = deliveries.json()["data"]["items"][0]
    assert delivery["channel"] == "SMS"
    assert delivery["status"] == "SKIPPED"
    assert delivery["error_code"] == "SMS_DISABLED"

    monkeypatch.setattr(settings, "SMS_ENABLED", True)
    retry = await admin_client.post(f"/api/v1/admin/notices/deliveries/{delivery['id']}/retry")
    assert retry.status_code == 200, retry.text
    assert retry.json()["data"]["status"] == DELIVERY_STATUS_SENT
    assert retry.json()["data"]["target_handle"].startswith("138")

    receipt = await admin_client.post(
        f"/api/v1/admin/notices/deliveries/{delivery['id']}/receipt/mock",
        json={"receipt_status": "DELIVERED"},
    )
    assert receipt.status_code == 200, receipt.text
    assert receipt.json()["data"]["receipt_status"] == "DELIVERED"
    refreshed_delivery = await db.get(NoticeDelivery, delivery["id"])
    assert refreshed_delivery is not None
    assert refreshed_delivery.status == DELIVERY_STATUS_SENT
