"""honor S3 集成测试：历史口径、治理元数据、类别可维护性。"""
from __future__ import annotations

from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student, User, UserRole
from app.core.security import create_token


async def _create_student(
    db: AsyncSession,
    *,
    student_no: str,
    full_name: str,
    grade_code: str = "2022",
    major_code: str = "CS",
    class_code: str = "CS2201",
) -> Student:
    row = Student(
        student_no=student_no,
        full_name=full_name,
        grade_code=grade_code,
        major_code=major_code,
        class_code=class_code,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def _create_headers(
    db: AsyncSession,
    *,
    work_no: str,
    display_name: str,
    student_id: int | None = None,
    roles: list[tuple[str, str | None]] | None = None,
) -> dict[str, str]:
    user = User(
        work_no=work_no,
        display_name=display_name,
        student_id=student_id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    role_codes: list[str] = []
    for role_code, scope_code in roles or []:
        db.add(UserRole(user_id=user.id, role_code=role_code, scope_code=scope_code))
        if role_code not in role_codes:
            role_codes.append(role_code)
    await db.commit()
    token_claims: dict[str, object] = {"roles": role_codes}
    if student_id is not None:
        token_claims["sid"] = student_id
    token = create_token(str(user.id), "access", extra_claims=token_claims)
    return {"Authorization": f"Bearer {token}"}


async def _create_category(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    code: str,
    name: str,
    is_active: bool,
    sort_order: int,
) -> dict:
    resp = await client.post(
        "/api/v1/admin/honors/categories",
        headers=headers,
        json={
            "code": code,
            "name": name,
            "description": f"{name} 分类",
            "sort_order": sort_order,
            "is_active": is_active,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _create_record(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    category_code: str,
    title: str,
    announced_at: str,
    effective_to: str | None = None,
    consent_flag: bool = True,
    student_id: int | None = None,
    display_name: str = "Honor Student",
) -> dict:
    resp = await client.post(
        "/api/v1/admin/honors",
        headers=headers,
        json={
            "category_code": category_code,
            "title": title,
            "level": "NATIONAL",
            "awarded_by": "教育部",
            "announced_at": announced_at,
            "effective_to": effective_to,
            "summary": f"{title} summary",
            "story_md": f"## {title}",
            "consent_flag": consent_flag,
            "recipients": [
                {
                    "student_id": student_id,
                    "student_no_snapshot": None,
                    "display_name": display_name,
                    "major_snapshot": "CS",
                    "grade_snapshot": "2022",
                }
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _archive_record(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    record_id: int,
    new_status: str,
    reason: str,
) -> dict:
    resp = await client.post(
        f"/api/v1/admin/honors/{record_id}/archive",
        headers=headers,
        json={"new_status": new_status, "reason": reason},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def test_honor_admin_categories_and_governance_metadata(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    student = await _create_student(db, student_no="H300001", full_name="荣誉学生甲")
    viewer_headers = await _create_headers(
        db,
        work_no="S300001",
        display_name="Honor Viewer",
        student_id=student.id,
        roles=[("STUDENT", None)],
    )
    admin_headers = await _create_headers(
        db,
        work_no="T300001",
        display_name="Honor Admin",
        roles=[("SUPER_ADMIN", None)],
    )

    await _create_category(
        client,
        admin_headers,
        code="SCHOLARSHIP",
        name="奖学金",
        is_active=True,
        sort_order=1,
    )
    await _create_category(
        client,
        admin_headers,
        code="LEGACY",
        name="历史荣誉类",
        is_active=False,
        sort_order=2,
    )

    public_categories = await client.get("/api/v1/honors/categories", headers=viewer_headers)
    assert public_categories.status_code == 200, public_categories.text
    public_codes = {row["code"] for row in public_categories.json()["data"]}
    assert "SCHOLARSHIP" in public_codes
    assert "LEGACY" not in public_codes

    admin_categories = await client.get("/api/v1/admin/honors/categories", headers=admin_headers)
    assert admin_categories.status_code == 200, admin_categories.text
    admin_codes = {row["code"] for row in admin_categories.json()["data"]}
    assert "SCHOLARSHIP" in admin_codes
    assert "LEGACY" in admin_codes

    current = await _create_record(
        client,
        admin_headers,
        category_code="SCHOLARSHIP",
        title="国家奖学金",
        announced_at="2026-04-10",
        effective_to="2026-12-31",
        student_id=student.id,
        display_name=student.full_name,
    )
    archived = await _create_record(
        client,
        admin_headers,
        category_code="SCHOLARSHIP",
        title="先进个人",
        announced_at="2024-05-01",
        effective_to="2024-12-31",
        student_id=student.id,
        display_name=student.full_name,
    )
    archived = await _archive_record(
        client,
        admin_headers,
        record_id=archived["id"],
        new_status="ARCHIVED",
        reason="届满归档",
    )

    admin_filtered = await client.get(
        "/api/v1/admin/honors",
        headers=admin_headers,
        params={"category_code": "SCHOLARSHIP", "status": "ACTIVE", "year": 2026},
    )
    assert admin_filtered.status_code == 200, admin_filtered.text
    filtered_items = admin_filtered.json()["data"]["items"]
    assert len(filtered_items) == 1
    assert filtered_items[0]["id"] == current["id"]
    assert filtered_items[0]["category_name"] == "奖学金"
    assert filtered_items[0]["updated_by_name"] == "Honor Admin"
    assert filtered_items[0]["updated_at"]
    assert filtered_items[0]["is_historical"] is False

    admin_archived = await client.get(
        "/api/v1/admin/honors",
        headers=admin_headers,
        params={"status": "ARCHIVED"},
    )
    assert admin_archived.status_code == 200, admin_archived.text
    archived_item = admin_archived.json()["data"]["items"][0]
    assert archived_item["id"] == archived["id"]
    assert archived_item["category_name"] == "奖学金"
    assert archived_item["updated_by_name"] == "Honor Admin"
    assert archived_item["is_historical"] is True
    assert archived_item["history_reason"] == "已归档"

    admin_detail = await client.get(
        f"/api/v1/admin/honors/{archived['id']}",
        headers=admin_headers,
    )
    assert admin_detail.status_code == 200, admin_detail.text
    admin_detail_data = admin_detail.json()["data"]
    assert admin_detail_data["category_name"] == "奖学金"
    assert admin_detail_data["updated_by_name"] == "Honor Admin"
    assert admin_detail_data["archive_reason"] == "届满归档"


async def test_honor_public_history_toggle_hides_revoked_and_consentless(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    student = await _create_student(db, student_no="H300002", full_name="荣誉学生乙")
    viewer_headers = await _create_headers(
        db,
        work_no="S300002",
        display_name="Honor Public Viewer",
        student_id=student.id,
        roles=[("STUDENT", None)],
    )
    admin_headers = await _create_headers(
        db,
        work_no="T300002",
        display_name="Honor Steward",
        roles=[("SUPER_ADMIN", None)],
    )
    await _create_category(
        client,
        admin_headers,
        code="SCHOLARSHIP",
        name="奖学金",
        is_active=True,
        sort_order=1,
    )

    await _create_record(
        client,
        admin_headers,
        category_code="SCHOLARSHIP",
        title="当前荣誉",
        announced_at="2026-04-10",
        effective_to="2026-12-31",
        student_id=student.id,
        display_name=student.full_name,
    )
    expired = await _create_record(
        client,
        admin_headers,
        category_code="SCHOLARSHIP",
        title="过期荣誉",
        announced_at="2025-04-10",
        effective_to="2025-05-31",
        student_id=student.id,
        display_name=student.full_name,
    )
    archived = await _create_record(
        client,
        admin_headers,
        category_code="SCHOLARSHIP",
        title="归档荣誉",
        announced_at="2024-04-10",
        effective_to="2024-12-31",
        student_id=student.id,
        display_name=student.full_name,
    )
    archived = await _archive_record(
        client,
        admin_headers,
        record_id=archived["id"],
        new_status="ARCHIVED",
        reason="届次结束",
    )
    revoked = await _create_record(
        client,
        admin_headers,
        category_code="SCHOLARSHIP",
        title="撤销荣誉",
        announced_at="2023-04-10",
        effective_to="2023-12-31",
        student_id=student.id,
        display_name=student.full_name,
    )
    revoked = await _archive_record(
        client,
        admin_headers,
        record_id=revoked["id"],
        new_status="REVOKED",
        reason="信息有误",
    )
    consentless = await _create_record(
        client,
        admin_headers,
        category_code="SCHOLARSHIP",
        title="未授权荣誉",
        announced_at="2026-02-10",
        effective_to="2026-12-31",
        consent_flag=False,
        student_id=student.id,
        display_name=student.full_name,
    )

    public_default = await client.get("/api/v1/honors", headers=viewer_headers)
    assert public_default.status_code == 200, public_default.text
    default_items = public_default.json()["data"]["items"]
    assert [item["title"] for item in default_items] == ["当前荣誉"]
    assert default_items[0]["category_name"] == "奖学金"
    assert default_items[0]["is_historical"] is False

    public_with_history = await client.get(
        "/api/v1/honors",
        headers=viewer_headers,
        params={"include_archived": True},
    )
    assert public_with_history.status_code == 200, public_with_history.text
    items_by_title = {
        item["title"]: item for item in public_with_history.json()["data"]["items"]
    }
    assert set(items_by_title) == {"当前荣誉", "过期荣誉", "归档荣誉"}
    assert items_by_title["当前荣誉"]["is_historical"] is False
    assert items_by_title["过期荣誉"]["is_historical"] is True
    assert items_by_title["过期荣誉"]["history_reason"] == "公示期已结束"
    assert items_by_title["归档荣誉"]["is_historical"] is True
    assert items_by_title["归档荣誉"]["history_reason"] == "已归档"
    assert "撤销荣誉" not in items_by_title
    assert "未授权荣誉" not in items_by_title

    archived_detail = await client.get(
        f"/api/v1/honors/{archived['id']}",
        headers=viewer_headers,
    )
    assert archived_detail.status_code == 200, archived_detail.text
    archived_detail_data = archived_detail.json()["data"]
    assert archived_detail_data["is_historical"] is True
    assert archived_detail_data["history_reason"] == "已归档"

    revoked_detail = await client.get(
        f"/api/v1/honors/{revoked['id']}",
        headers=viewer_headers,
    )
    assert revoked_detail.status_code == 404

    consentless_detail = await client.get(
        f"/api/v1/honors/{consentless['id']}",
        headers=viewer_headers,
    )
    assert consentless_detail.status_code == 404
    assert expired["effective_to"] < date.today().isoformat()
