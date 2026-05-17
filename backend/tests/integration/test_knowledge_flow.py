"""knowledge 闭环 happy-path：source → entry → publish → search → detail。

覆盖 FR-001 / FR-002 / FR-003：知识条目治理、受控问答降级（AI_QA_ENABLED=false
时必须走关键词匹配，不调用 Claude API），以及发布/弃用状态机与修订记录。
"""
from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.auth.models import User, UserRole
from app.core.security import create_token


async def test_list_categories_anonymous(client: AsyncClient) -> None:
    """分类字典属公开数据，无需鉴权。"""
    resp = await client.get("/api/v1/knowledge/categories")
    assert resp.status_code == 200
    codes = {c["code"] for c in resp.json()["data"]}
    assert {"PARTY", "SCHOLARSHIP", "LEAVE"}.issubset(codes)


async def test_admin_flow_create_publish_search(admin_client: AsyncClient) -> None:
    # 1. 创建来源
    src_resp = await admin_client.post(
        "/api/v1/admin/knowledge/sources",
        json={
            "source_name": "《学生手册 2024 版》第 3 章",
            "source_url": "https://example.edu/handbook-2024-ch3",
            "issuing_org": "学生工作部",
            "version_label": "2024v1",
        },
    )
    assert src_resp.status_code == 200, src_resp.text
    source_id = src_resp.json()["data"]["id"]

    # 2. 创建条目（草稿）
    entry_resp = await admin_client.post(
        "/api/v1/admin/knowledge/entries",
        json={
            "slug": "sick-leave-procedure",
            "title": "病假申请流程",
            "summary": "因病请假 3 日及以内的申请流程与所需材料。",
            "category_code": "LEAVE",
            "applicable_condition": "学生本人因病需请假 1-3 日",
            "required_materials": "医院门诊收据或病历复印件",
            "process_steps": "1. 小程序提交 → 2. 辅导员审批 → 3. 系统归档",
            "body_md": "### 操作流程\n详见步骤。",
            "source_id": source_id,
            "version_label": "2024v1",
            "tags": ["请假", "病假"],
        },
    )
    assert entry_resp.status_code == 200, entry_resp.text
    entry_detail = entry_resp.json()["data"]
    entry_id = entry_detail["id"]
    assert entry_detail["status"] == "DRAFT"
    assert "请假" in entry_detail["tags"]

    admin_detail_resp = await admin_client.get(f"/api/v1/admin/knowledge/entries/{entry_id}")
    assert admin_detail_resp.status_code == 200, admin_detail_resp.text
    admin_detail = admin_detail_resp.json()["data"]
    assert admin_detail["status"] == "DRAFT"
    assert admin_detail["body_md"] == "### 操作流程\n详见步骤。"

    # 3. 学生端此时搜不到（只检索 PUBLISHED）
    search_draft = await admin_client.get("/api/v1/knowledge/search?q=病假")
    assert search_draft.status_code == 200
    assert search_draft.json()["data"]["meta"]["total"] == 0

    # 4. 发布
    pub_resp = await admin_client.post(
        f"/api/v1/admin/knowledge/entries/{entry_id}/publish",
        json={"note": "首次发布"},
    )
    assert pub_resp.status_code == 200, pub_resp.text
    assert pub_resp.json()["data"]["status"] == "PUBLISHED"

    # 5. 学生端搜索命中
    search_pub = await admin_client.get("/api/v1/knowledge/search?q=病假")
    assert search_pub.status_code == 200
    body = search_pub.json()
    assert body["data"]["meta"]["total"] == 1
    hit = body["data"]["items"][0]
    assert hit["slug"] == "sick-leave-procedure"
    assert hit["status"] == "PUBLISHED"
    assert hit["applicable_condition"] == "学生本人因病需请假 1-3 日"
    assert hit["required_materials"] == "医院门诊收据或病历复印件"
    assert hit["process_steps"].startswith("1. 小程序提交")

    # 6. 详情返回来源（FR-002 来源治理）
    detail_resp = await admin_client.get(f"/api/v1/knowledge/{entry_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["source"] is not None
    assert detail["source"]["source_name"].startswith("《学生手册")


async def test_admin_endpoint_rejects_unauthenticated(client: AsyncClient) -> None:
    """C-03：没 token 直接 401，不能依赖前端隐藏。"""
    resp = await client.post(
        "/api/v1/admin/knowledge/sources",
        json={"source_name": "x"},
    )
    assert resp.status_code == 401


async def test_admin_endpoint_rejects_student_role(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    """普通学生不能维护知识库 → 403。"""
    from app.auth.models import Student

    db.add(Student(student_no="2022110199", full_name="测试学生Z"))
    await db.commit()
    login = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": "wx_code_knowledge_student",
            "student_no": "2022110199",
            "full_name": "测试学生Z",
        },
    )
    student_token = login.json()["data"]["access_token"]
    resp = await client.post(
        "/api/v1/admin/knowledge/sources",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"source_name": "x"},
    )
    assert resp.status_code == 403


async def test_collaborator_role_can_manage_knowledge_sources(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    user = User(work_no="KNCADRE01", display_name="Knowledge Cadre", is_active=True)
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_code="PARTY_BRANCH_SECRETARY"))
    await db.commit()
    token = create_token(str(user.id), "access", extra_claims={"roles": ["PARTY_BRANCH_SECRETARY"]})

    resp = await client.post(
        "/api/v1/admin/knowledge/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source_name": "党支部工作手册",
            "source_url": "https://example.edu/party-handbook",
            "issuing_org": "信息学院党支部",
            "version_label": "2026-v1",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["source_name"] == "党支部工作手册"


async def test_official_source_requires_url_and_writes_audit(
    admin_client: AsyncClient,
    db: AsyncSession,
) -> None:
    rejected = await admin_client.post(
        "/api/v1/admin/knowledge/sources",
        json={
            "source_name": "无链接官方来源",
            "is_official": True,
        },
    )
    assert rejected.status_code == 422, rejected.text

    draft_source = await admin_client.post(
        "/api/v1/admin/knowledge/sources",
        json={
            "source_name": "待核验来源",
            "is_official": False,
        },
    )
    assert draft_source.status_code == 200, draft_source.text
    draft_mark_official = await admin_client.patch(
        f"/api/v1/admin/knowledge/sources/{draft_source.json()['data']['id']}",
        json={"is_official": True},
    )
    assert draft_mark_official.status_code == 422, draft_mark_official.text

    created = await admin_client.post(
        "/api/v1/admin/knowledge/sources",
        json={
            "source_name": "学院官网来源",
            "source_url": "https://info.ruc.edu.cn/service",
            "is_official": True,
        },
    )
    assert created.status_code == 200, created.text
    source_id = created.json()["data"]["id"]

    create_log = (
        await db.execute(
            select(AuditLog).where(
                AuditLog.action == "CREATE_KNOWLEDGE_SOURCE",
                AuditLog.entity_id == source_id,
            )
        )
    ).scalar_one_or_none()
    assert create_log is not None
    assert create_log.result_code == "SUCCESS"

    blocked_update = await admin_client.patch(
        f"/api/v1/admin/knowledge/sources/{source_id}",
        json={"source_url": None},
    )
    assert blocked_update.status_code == 422, blocked_update.text

    updated = await admin_client.patch(
        f"/api/v1/admin/knowledge/sources/{source_id}",
        json={"source_url": "https://info.ruc.edu.cn/service/v2"},
    )
    assert updated.status_code == 200, updated.text

    update_log = (
        await db.execute(
            select(AuditLog).where(
                AuditLog.action == "UPDATE_KNOWLEDGE_SOURCE",
                AuditLog.entity_id == source_id,
            )
        )
    ).scalar_one_or_none()
    assert update_log is not None
    assert update_log.result_code == "SUCCESS"


async def test_ai_match_fallback_to_keyword(admin_client: AsyncClient) -> None:
    """AI_QA_ENABLED=false 时走关键词匹配，engine 字段 == 'keyword'。"""
    # 先发布一条条目
    src = await admin_client.post(
        "/api/v1/admin/knowledge/sources",
        json={"source_name": "test-src"},
    )
    entry_resp = await admin_client.post(
        "/api/v1/admin/knowledge/entries",
        json={
            "slug": "scholarship-info",
            "title": "国家奖学金申请",
            "summary": "国奖每年 9 月启动申请",
            "category_code": "SCHOLARSHIP",
            "source_id": src.json()["data"]["id"],
            "tags": ["奖学金"],
        },
    )
    entry_id = entry_resp.json()["data"]["id"]
    await admin_client.post(
        f"/api/v1/admin/knowledge/entries/{entry_id}/publish", json={}
    )

    match_resp = await admin_client.post(
        "/api/v1/knowledge/ai-match",
        json={"query": "国家奖学金怎么申请", "top_k": 3},
    )
    assert match_resp.status_code == 200, match_resp.text
    data = match_resp.json()["data"]
    assert data["engine"] == "keyword"
    assert "免责" in data["disclaimer"] or "人工" in data["disclaimer"]
