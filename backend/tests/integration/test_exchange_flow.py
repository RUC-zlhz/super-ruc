"""exchange 导入导出闭环 — FR-009 + v1.5 行级错误报告。

覆盖：
- student 导入：happy-path 上传 → VALIDATED → commit → COMMITTED；正式表可见
- student 导入：含缺失学号的行 → status=FAILED；不可 commit
- v1.5：失败批次 /error-report 下载 Excel，末列含"错误原因"定位行与字段
- C-03：无 token 401
"""
from __future__ import annotations

import io

from httpx import AsyncClient
from openpyxl import Workbook, load_workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Student
from app.exchange.service import ERROR_REPORT_COLUMN


def _build_student_xlsx(rows: list[dict]) -> bytes:
    """按 _apply_student 期望的列头拼装一个最小 Excel。"""
    headers = [
        "student_no", "full_name", "gender", "birth_date",
        "grade_code", "major_code", "class_code",
        "political_status", "enrollment_year", "expected_graduation_year",
        "email", "status",
    ]
    wb = Workbook()
    ws = wb.active
    ws.title = "students"
    ws.append(headers)
    for r in rows:
        ws.append([r.get(h) for h in headers])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


async def test_student_import_happy_path_validate_and_commit(
    admin_client: AsyncClient, db: AsyncSession
) -> None:
    xlsx = _build_student_xlsx([
        {
            "student_no": "IMP2001",
            "full_name": "导入学生甲",
            "gender": "男",
            "grade_code": "2024",
            "major_code": "CS",
            "class_code": "CS2401",
            "enrollment_year": 2024,
            "expected_graduation_year": 2028,
        },
        {
            "student_no": "IMP2002",
            "full_name": "导入学生乙",
            "gender": "女",
            "grade_code": "2024",
            "major_code": "CS",
            "class_code": "CS2402",
        },
    ])

    upload = await admin_client.post(
        "/api/v1/admin/exchange/imports/student",
        files={
            "file": (
                "students.xlsx", xlsx,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert upload.status_code == 200, upload.text
    batch = upload.json()["data"]["batch"]
    assert batch["status"] == "VALIDATED"
    assert batch["total_rows"] == 2
    assert batch["fatal_rows"] == 0

    commit = await admin_client.post(
        f"/api/v1/admin/exchange/imports/{batch['id']}/commit",
        json={"note": "一期主档初始化"},
    )
    assert commit.status_code == 200, commit.text
    assert commit.json()["data"]["status"] == "COMMITTED"

    # 正式表落库：学生可查到
    stu = (
        await db.execute(select(Student).where(Student.student_no == "IMP2001"))
    ).scalar_one_or_none()
    assert stu is not None
    assert stu.full_name == "导入学生甲"


async def test_student_import_with_bad_row_fails_batch(
    admin_client: AsyncClient,
) -> None:
    xlsx = _build_student_xlsx([
        {"student_no": "IMP3001", "full_name": "正常行"},
        # 缺 student_no → FATAL
        {"student_no": None, "full_name": "缺学号"},
    ])
    upload = await admin_client.post(
        "/api/v1/admin/exchange/imports/student",
        files={"file": ("bad.xlsx", xlsx,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert upload.status_code == 200, upload.text
    batch = upload.json()["data"]["batch"]
    assert batch["status"] == "FAILED"
    assert batch["fatal_rows"] == 1
    assert batch["total_rows"] == 2

    # C-06：FAILED 批次不可 commit
    commit = await admin_client.post(
        f"/api/v1/admin/exchange/imports/{batch['id']}/commit",
        json={"note": "应被拒绝"},
    )
    assert commit.status_code == 400


async def test_v15_error_report_download_has_reason_column(
    admin_client: AsyncClient,
) -> None:
    """fix.md 修改点 4：失败批次返回带"错误原因"列的 Excel。"""
    xlsx = _build_student_xlsx([
        {"student_no": "IMP4001", "full_name": "正常行一"},
        {"student_no": None, "full_name": "缺学号两位"},   # FATAL
        {"student_no": "IMP4003", "full_name": None},      # FATAL（姓名空）
    ])
    upload = await admin_client.post(
        "/api/v1/admin/exchange/imports/student",
        files={"file": ("bad.xlsx", xlsx,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    batch_id = upload.json()["data"]["batch"]["id"]

    resp = await admin_client.get(
        f"/api/v1/admin/exchange/imports/{batch_id}/error-report"
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml"
    )
    wb = load_workbook(io.BytesIO(resp.content), read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    # header 末列应是 错误原因
    header = list(rows[0])
    assert header[-1] == ERROR_REPORT_COLUMN
    # 至少有两条错误行，且 reason 非空
    err_rows = rows[1:]
    assert len(err_rows) == 2
    for r in err_rows:
        reason = r[-1]
        assert reason is not None and len(str(reason)) > 0
        # 应定位到行号与字段
        assert "row" in str(reason)


async def test_exchange_endpoints_reject_anonymous(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/admin/exchange/imports")
    assert resp.status_code == 401
