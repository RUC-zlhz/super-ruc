"""quiz 闭环 — FR-005 理论自测。

覆盖：
- 管理端创建三种题型（SINGLE / MULTI / JUDGE）
- 校验失败：错误题型、选项不足、correct_key 不在 options
- 学生抽题 → 提交 → 得分 / 判分正确性
- 单选大小写不敏感；多选顺序无关；判断题多种别名
- 软删除后不再抽到
- C-03：匿名 401；学生访问管理端 403
"""
from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student


async def _login_as_student(
    client: AsyncClient, db: AsyncSession, *, student_no: str, wx_code: str
) -> str:
    db.add(
        Student(
            student_no=student_no,
            full_name=f"quiz-{student_no}",
            grade_code="2022",
            major_code="CS",
            class_code="CS2201",
        )
    )
    await db.commit()
    resp = await client.post(
        "/api/v1/auth/wx-login",
        json={
            "code": wx_code,
            "student_no": student_no,
            "full_name": f"quiz-{student_no}",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


async def _create_question(
    admin_client: AsyncClient, **overrides
) -> dict:
    payload = {
        "topic": "党史",
        "qtype": "SINGLE",
        "stem": "中国共产党成立于哪一年？",
        "options_json": [
            {"key": "A", "text": "1919"},
            {"key": "B", "text": "1921"},
            {"key": "C", "text": "1949"},
            {"key": "D", "text": "1978"},
        ],
        "correct_key": "B",
        "explanation": "1921 年 7 月 23 日中国共产党第一次全国代表大会召开。",
        "difficulty": "EASY",
    }
    payload.update(overrides)
    resp = await admin_client.post("/api/v1/admin/quiz/questions", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def test_quiz_admin_crud_and_validation(admin_client: AsyncClient) -> None:
    # 创建 SINGLE
    single = await _create_question(admin_client)
    assert single["qtype"] == "SINGLE"
    assert single["correct_key"] == "B"
    assert single["is_active"] is True

    # 创建 MULTI
    multi = await _create_question(
        admin_client,
        topic="党建",
        qtype="MULTI",
        stem="党的三大法宝包括？",
        options_json=[
            {"key": "A", "text": "统一战线"},
            {"key": "B", "text": "武装斗争"},
            {"key": "C", "text": "党的建设"},
            {"key": "D", "text": "市场经济"},
        ],
        correct_key="a, c , b",
    )
    # 服务端规范化为排序、大写、逗号拼接
    assert multi["correct_key"] == "A,B,C"

    # 创建 JUDGE
    judge = await _create_question(
        admin_client,
        topic="党章",
        qtype="JUDGE",
        stem="入党积极分子考察期不得少于一年。",
        options_json=None,
        correct_key="对",
    )
    assert judge["correct_key"] == "TRUE"

    # 列表
    listing = await admin_client.get(
        "/api/v1/admin/quiz/questions", params={"page": 1, "size": 50}
    )
    assert listing.status_code == 200
    assert listing.json()["data"]["meta"]["total"] >= 3

    # 校验：未知题型
    bad1 = await admin_client.post(
        "/api/v1/admin/quiz/questions",
        json={
            "topic": "x",
            "qtype": "FILL",
            "stem": "?",
            "correct_key": "A",
        },
    )
    assert bad1.status_code in (400, 422)

    # 校验：SINGLE 选项不足
    bad2 = await admin_client.post(
        "/api/v1/admin/quiz/questions",
        json={
            "topic": "x",
            "qtype": "SINGLE",
            "stem": "?",
            "options_json": [{"key": "A", "text": "only"}],
            "correct_key": "A",
        },
    )
    assert bad2.status_code == 400

    # 校验：correct_key 不在 options
    bad3 = await admin_client.post(
        "/api/v1/admin/quiz/questions",
        json={
            "topic": "x",
            "qtype": "SINGLE",
            "stem": "?",
            "options_json": [
                {"key": "A", "text": "a"},
                {"key": "B", "text": "b"},
            ],
            "correct_key": "Z",
        },
    )
    assert bad3.status_code == 400

    # PATCH 更新 + 软删
    patched = await admin_client.patch(
        f"/api/v1/admin/quiz/questions/{single['id']}",
        json={"explanation": "（更新）解析"},
    )
    assert patched.status_code == 200
    assert "更新" in patched.json()["data"]["explanation"]

    deleted = await admin_client.delete(
        f"/api/v1/admin/quiz/questions/{single['id']}"
    )
    assert deleted.status_code == 200
    # 软删：仍可查，但 is_active=False
    again = await admin_client.get(
        "/api/v1/admin/quiz/questions",
        params={"is_active": "false"},
    )
    assert again.status_code == 200
    ids_inactive = [q["id"] for q in again.json()["data"]["items"]]
    assert single["id"] in ids_inactive


async def test_quiz_student_draw_and_submit_three_types(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient
) -> None:
    # 造 3 道题，一题一种题型
    q_single = await _create_question(
        admin_client,
        topic="自测",
        qtype="SINGLE",
        correct_key="B",
    )
    q_multi = await _create_question(
        admin_client,
        topic="自测",
        qtype="MULTI",
        stem="以下哪些属于社会主义核心价值观（任意两项以上）？",
        options_json=[
            {"key": "A", "text": "富强"},
            {"key": "B", "text": "自由"},
            {"key": "C", "text": "专制"},
            {"key": "D", "text": "和谐"},
        ],
        correct_key="A,B,D",
    )
    q_judge = await _create_question(
        admin_client,
        topic="自测",
        qtype="JUDGE",
        stem="党员必须按期交纳党费。",
        options_json=None,
        correct_key="TRUE",
    )

    token = await _login_as_student(
        client, db, student_no="Q100001", wx_code="wx_q100001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    # 抽题 — 只抽 topic=自测（3 道）
    draw = await client.get(
        "/api/v1/quiz/draw",
        headers=stu_headers,
        params={"topic": "自测", "limit": 10},
    )
    assert draw.status_code == 200, draw.text
    data = draw.json()["data"]
    batch_id = data["batch_id"]
    drawn_ids = {q["id"] for q in data["questions"]}
    assert {q_single["id"], q_multi["id"], q_judge["id"]}.issubset(drawn_ids)
    # 学生视图不含 correct_key / explanation
    for q in data["questions"]:
        assert "correct_key" not in q
        assert "explanation" not in q

    # 提交：单选大小写不敏感；多选顺序乱；判断用中文"对"
    submit = await client.post(
        "/api/v1/quiz/submit",
        headers=stu_headers,
        json={
            "batch_id": batch_id,
            "answers": [
                {"question_id": q_single["id"], "answer": "b"},  # 小写仍正确
                {"question_id": q_multi["id"], "answer": "D, a , B"},  # 顺序乱也对
                {"question_id": q_judge["id"], "answer": "对"},  # 别名
            ],
        },
    )
    assert submit.status_code == 200, submit.text
    result = submit.json()["data"]
    assert result["total"] == 3
    assert result["correct"] == 3
    assert result["score"] == 99  # 每题 33 分 * 3

    # 查看自己的记录
    records = await client.get(
        "/api/v1/quiz/my/records",
        headers=stu_headers,
        params={"batch_id": batch_id},
    )
    assert records.status_code == 200
    assert len(records.json()["data"]) == 3


async def test_quiz_partial_wrong_answers(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient
) -> None:
    """错答与漏选应判错，分数按正确数累计。"""
    q_multi = await _create_question(
        admin_client,
        topic="混合",
        qtype="MULTI",
        stem="以下哪些为三大作风？",
        options_json=[
            {"key": "A", "text": "理论联系实际"},
            {"key": "B", "text": "密切联系群众"},
            {"key": "C", "text": "批评与自我批评"},
            {"key": "D", "text": "享乐主义"},
        ],
        correct_key="A,B,C",
    )
    q_judge = await _create_question(
        admin_client,
        topic="混合",
        qtype="JUDGE",
        stem="团员可以不参加组织生活。",
        options_json=None,
        correct_key="FALSE",
    )

    token = await _login_as_student(
        client, db, student_no="Q200001", wx_code="wx_q200001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    draw = await client.get(
        "/api/v1/quiz/draw",
        headers=stu_headers,
        params={"topic": "混合", "limit": 10},
    )
    batch_id = draw.json()["data"]["batch_id"]

    submit = await client.post(
        "/api/v1/quiz/submit",
        headers=stu_headers,
        json={
            "batch_id": batch_id,
            "answers": [
                {"question_id": q_multi["id"], "answer": "A,B"},  # 漏选 C
                {"question_id": q_judge["id"], "answer": "对"},  # 错答
            ],
        },
    )
    assert submit.status_code == 200
    result = submit.json()["data"]
    assert result["total"] == 2
    assert result["correct"] == 0
    assert result["score"] == 0
    # 结果集里应暴露正确答案与解析以便学生学习
    for item in result["items"]:
        assert item["is_correct"] is False
        assert item["correct_key"]


async def test_quiz_deleted_question_not_drawn(
    client: AsyncClient, db: AsyncSession, admin_client: AsyncClient
) -> None:
    q = await _create_question(admin_client, topic="废弃")
    # 软删
    del_resp = await admin_client.delete(
        f"/api/v1/admin/quiz/questions/{q['id']}"
    )
    assert del_resp.status_code == 200

    token = await _login_as_student(
        client, db, student_no="Q300001", wx_code="wx_q300001"
    )
    stu_headers = {"Authorization": f"Bearer {token}"}

    draw = await client.get(
        "/api/v1/quiz/draw",
        headers=stu_headers,
        params={"topic": "废弃", "limit": 10},
    )
    # topic 下只有这一题且被软删，抽题应 404
    assert draw.status_code == 404


async def test_quiz_access_control(
    client: AsyncClient, db: AsyncSession
) -> None:
    """C-03：未登录 401；学生访问管理端 403。"""
    anon = await client.get("/api/v1/admin/quiz/questions")
    assert anon.status_code == 401

    token = await _login_as_student(
        client, db, student_no="Q900001", wx_code="wx_q900001"
    )
    resp = await client.get(
        "/api/v1/admin/quiz/questions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
