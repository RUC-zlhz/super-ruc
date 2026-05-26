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
    is_collective: bool = False,
    display_order: int = 0,
    cover_image_url: str | None = None,
    media: dict | None = None,
    consent_flag: bool = True,
    student_id: int | None = None,
    display_name: str = "Honor Student",
    recipients: list[dict] | None = None,
) -> dict:
    honor_recipients = recipients or [
        {
            "student_id": student_id,
            "student_no_snapshot": None,
            "display_name": display_name,
            "major_snapshot": "CS",
            "grade_snapshot": "2022",
        }
    ]
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
            "is_collective": is_collective,
            "display_order": display_order,
            "summary": f"{title} summary",
            "story_md": f"## {title}",
            "cover_image_url": cover_image_url,
            "media": media,
            "consent_flag": consent_flag,
            "recipients": honor_recipients,
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


async def test_honor_display_order_and_collective_filters(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    viewer_headers = await _create_headers(
        db,
        work_no="S300003",
        display_name="Honor Sort Viewer",
        roles=[("STUDENT", None)],
    )
    admin_headers = await _create_headers(
        db,
        work_no="T300003",
        display_name="Honor Sort Admin",
        roles=[("SUPER_ADMIN", None)],
    )
    await _create_category(
        client,
        admin_headers,
        code="MERIT",
        name="荣誉称号",
        is_active=True,
        sort_order=1,
    )

    late_personal = await _create_record(
        client,
        admin_headers,
        category_code="MERIT",
        title="晚序个人",
        announced_at="2026-05-01",
        display_order=20,
        display_name="个人甲",
    )
    collective = await _create_record(
        client,
        admin_headers,
        category_code="MERIT",
        title="优先集体",
        announced_at="2026-04-01",
        is_collective=True,
        display_order=5,
        display_name="先进班集体",
    )
    newer_personal = await _create_record(
        client,
        admin_headers,
        category_code="MERIT",
        title="同序较新个人",
        announced_at="2026-06-01",
        display_order=5,
        display_name="个人乙",
    )

    admin_list = await client.get("/api/v1/admin/honors", headers=admin_headers)
    assert admin_list.status_code == 200, admin_list.text
    admin_items = admin_list.json()["data"]["items"]
    assert [item["id"] for item in admin_items] == [
        newer_personal["id"],
        collective["id"],
        late_personal["id"],
    ]
    assert admin_items[0]["display_order"] == 5

    admin_collective = await client.get(
        "/api/v1/admin/honors",
        headers=admin_headers,
        params={"is_collective": True},
    )
    assert admin_collective.status_code == 200, admin_collective.text
    assert [item["id"] for item in admin_collective.json()["data"]["items"]] == [
        collective["id"]
    ]

    public_personal = await client.get(
        "/api/v1/honors",
        headers=viewer_headers,
        params={"is_collective": False},
    )
    assert public_personal.status_code == 200, public_personal.text
    assert [item["id"] for item in public_personal.json()["data"]["items"]] == [
        newer_personal["id"],
        late_personal["id"],
    ]


async def test_honor_manual_media_recipients_and_empty_guard(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    admin_headers = await _create_headers(
        db,
        work_no="T300004",
        display_name="Honor Manual Admin",
        roles=[("SUPER_ADMIN", None)],
    )
    await _create_category(
        client,
        admin_headers,
        code="MODEL",
        name="榜样宣传",
        is_active=True,
        sort_order=1,
    )

    empty_create = await client.post(
        "/api/v1/admin/honors",
        headers=admin_headers,
        json={
            "category_code": "MODEL",
            "title": "无获奖人荣誉",
            "level": "SCHOOL",
            "awarded_by": "学院",
            "announced_at": "2026-05-01",
            "consent_flag": True,
            "recipients": [],
        },
    )
    assert empty_create.status_code == 400
    assert empty_create.json()["code"] == 40172

    created = await _create_record(
        client,
        admin_headers,
        category_code="MODEL",
        title="榜样个人",
        announced_at="2026-05-02",
        display_order=7,
        cover_image_url="https://example.edu/honor-cover.jpg",
        media={"photos": ["https://example.edu/p1.jpg"], "videos": []},
        recipients=[
            {
                "student_id": None,
                "student_no_snapshot": "20240001",
                "display_name": "  张三  ",
                "major_snapshot": "  信息安全  ",
                "grade_snapshot": "2024",
                "class_snapshot": "  信安2401  ",
                "role_in_collective": None,
            }
        ],
    )
    assert created["display_order"] == 7
    assert created["cover_image_url"] == "https://example.edu/honor-cover.jpg"
    assert created["media"]["photos"] == ["https://example.edu/p1.jpg"]
    assert created["recipients"][0]["display_name"] == "张三"
    assert created["recipients"][0]["major_snapshot"] == "信息安全"

    update_resp = await client.patch(
        f"/api/v1/admin/honors/{created['id']}",
        headers=admin_headers,
        json={
            "category_code": "MODEL",
            "title": "榜样集体",
            "level": "SCHOOL",
            "awarded_by": "学院",
            "announced_at": "2026-05-03",
            "display_order": 2,
            "is_collective": True,
            "cover_image_url": "https://example.edu/new-cover.jpg",
            "media": {"photos": ["https://example.edu/p2.jpg"]},
            "consent_flag": True,
            "recipients": [
                {
                    "student_id": None,
                    "student_no_snapshot": None,
                    "display_name": "   ",
                    "major_snapshot": None,
                    "grade_snapshot": None,
                    "class_snapshot": None,
                    "role_in_collective": None,
                },
                {
                    "student_id": None,
                    "student_no_snapshot": None,
                    "display_name": "示范团队",
                    "major_snapshot": None,
                    "grade_snapshot": "2024",
                    "class_snapshot": "信安2401",
                    "role_in_collective": "团队",
                },
            ],
        },
    )
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()["data"]
    assert updated["display_order"] == 2
    assert updated["is_collective"] is True
    assert updated["cover_image_url"] == "https://example.edu/new-cover.jpg"
    assert updated["media"]["photos"] == ["https://example.edu/p2.jpg"]
    assert [recipient["display_name"] for recipient in updated["recipients"]] == ["示范团队"]

    empty_update = await client.patch(
        f"/api/v1/admin/honors/{created['id']}",
        headers=admin_headers,
        json={
            "category_code": "MODEL",
            "title": "榜样集体",
            "level": "SCHOOL",
            "awarded_by": "学院",
            "announced_at": "2026-05-03",
            "display_order": 2,
            "is_collective": True,
            "consent_flag": True,
            "recipients": [
                {
                    "student_id": None,
                    "student_no_snapshot": None,
                    "display_name": "   ",
                    "major_snapshot": None,
                    "grade_snapshot": None,
                    "class_snapshot": None,
                    "role_in_collective": None,
                }
            ],
        },
    )
    assert empty_update.status_code == 400
    assert empty_update.json()["code"] == 40172
