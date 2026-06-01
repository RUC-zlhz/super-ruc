from __future__ import annotations

from pathlib import Path

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def test_student_template_list_and_download_after_publish(
    admin_client: AsyncClient,
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    from app.auth.models import Student

    db.add(Student(student_no="2022110201", full_name="模板测试学生"))
    await db.commit()
    login = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": "wx_code_knowledge_template_student",
            "student_no": "2022110201",
            "full_name": "模板测试学生",
        },
    )
    assert login.status_code == 200, login.text
    student_token = login.json()["data"]["access_token"]

    src_resp = await admin_client.post(
        "/api/v1/admin/knowledge/sources",
        json={"source_name": "template-list-src"},
    )
    assert src_resp.status_code == 200, src_resp.text
    source_id = src_resp.json()["data"]["id"]

    upload_resp = await admin_client.post(
        "/api/v1/admin/knowledge/templates",
        files={
            "file": (
                "leave-template.docx",
                b"template-bytes",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={
            "template_name": "请假模板示例",
            "template_type": "DOCX",
            "category_code": "LEAVE",
            "applicable_scenario": "学生请假",
            "version_label": "示例模板",
        },
    )
    assert upload_resp.status_code == 200, upload_resp.text
    template_id = upload_resp.json()["data"]["id"]

    entry_resp = await admin_client.post(
        "/api/v1/admin/knowledge/entries",
        json={
            "slug": "leave-template-example",
            "title": "请假模板示例下载",
            "summary": "用于测试学生端模板下载。",
            "category_code": "LEAVE",
            "source_id": source_id,
            "process_steps": "1. 下载模板；2. 填写信息；3. 提交审核。",
            "body_md": "模板下载示例",
            "template_ids": [template_id],
            "tags": ["请假模板", "模板下载"],
        },
    )
    assert entry_resp.status_code == 200, entry_resp.text
    entry_id = entry_resp.json()["data"]["id"]

    publish_resp = await admin_client.post(
        f"/api/v1/admin/knowledge/entries/{entry_id}/publish",
        json={},
    )
    assert publish_resp.status_code == 200, publish_resp.text

    template_list = await client.get(
        "/api/v1/knowledge/templates",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert template_list.status_code == 200, template_list.text
    items = template_list.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["template_name"] == "请假模板示例"

    detail_resp = await client.get(f"/api/v1/knowledge/{entry_id}")
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()["data"]
    assert detail["templates"][0]["template_id"] == template_id

    download_resp = await client.get(
        f"/api/v1/knowledge/templates/{template_id}/download",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert download_resp.status_code == 200, download_resp.text
    download_url = download_resp.json()["data"]["download_url"]
    assert download_url.startswith("file://")
    local_path = Path(download_url.removeprefix("file:///"))
    assert local_path.exists()

    file_resp = await client.get(
        f"/api/v1/knowledge/templates/{template_id}/file",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert file_resp.status_code == 200, file_resp.text
    assert file_resp.content == b"template-bytes"
    assert file_resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert "filename*=" in file_resp.headers["content-disposition"]
