from __future__ import annotations

import io
import json
import statistics
import time

from httpx import AsyncClient
from openpyxl import Workbook

TRIALS = 3
ROW_COUNT = 100


def _build_student_xlsx(rows: list[dict[str, object]]) -> bytes:
    headers = [
        "student_no",
        "full_name",
        "gender",
        "birth_date",
        "grade_code",
        "major_code",
        "class_code",
        "political_status",
        "enrollment_year",
        "expected_graduation_year",
        "email",
        "status",
    ]
    wb = Workbook()
    ws = wb.active
    ws.title = "students"
    ws.append(headers)
    for row in rows:
        ws.append([row.get(header) for header in headers])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _build_standard_rows(trial: int, row_count: int = ROW_COUNT) -> list[dict[str, object]]:
    return [
        {
            "student_no": f"PB{trial:02d}{idx:04d}",
            "full_name": f"Benchmark Student {trial}-{idx}",
            "gender": "男" if idx % 2 == 0 else "女",
            "grade_code": "2024",
            "major_code": "CS",
            "class_code": f"CS24{(idx % 4) + 1:02d}",
            "political_status": "共青团员" if idx % 3 else "群众",
            "enrollment_year": 2024,
            "expected_graduation_year": 2028,
            "email": f"benchmark-{trial}-{idx}@example.com",
            "status": "IN_SCHOOL",
        }
        for idx in range(1, row_count + 1)
    ]


def _round_seconds(value: float) -> float:
    return round(value, 6)


async def _run_student_import_trial(
    admin_client: AsyncClient,
    *,
    trial: int,
) -> dict[str, object]:
    xlsx = _build_student_xlsx(_build_standard_rows(trial))

    validate_started = time.perf_counter()
    upload = await admin_client.post(
        "/api/v1/admin/exchange/imports/student",
        files={
            "file": (
                f"students-benchmark-{trial}.xlsx",
                xlsx,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    validate_elapsed = time.perf_counter() - validate_started
    assert upload.status_code == 200, upload.text

    batch = upload.json()["data"]["batch"]
    assert batch["status"] == "VALIDATED"
    assert batch["total_rows"] == ROW_COUNT
    assert batch["fatal_rows"] == 0

    commit_started = time.perf_counter()
    commit = await admin_client.post(
        f"/api/v1/admin/exchange/imports/{batch['id']}/commit",
        json={"note": f"performance benchmark trial {trial}"},
    )
    commit_elapsed = time.perf_counter() - commit_started
    assert commit.status_code == 200, commit.text
    assert commit.json()["data"]["status"] == "COMMITTED"

    return {
        "trial": trial,
        "rows": ROW_COUNT,
        "validate_seconds": _round_seconds(validate_elapsed),
        "commit_seconds": _round_seconds(commit_elapsed),
        "total_seconds": _round_seconds(validate_elapsed + commit_elapsed),
    }


async def test_standard_student_import_benchmark(
    admin_client: AsyncClient,
    record_property,
) -> None:
    trial_results = [
        await _run_student_import_trial(admin_client, trial=trial)
        for trial in range(1, TRIALS + 1)
    ]

    raw_validate = [result["validate_seconds"] for result in trial_results]
    raw_commit = [result["commit_seconds"] for result in trial_results]
    raw_total = [result["total_seconds"] for result in trial_results]
    report = {
        "benchmark": "student_import_standard_100_rows",
        "trial_count": TRIALS,
        "row_count": ROW_COUNT,
        "trials": trial_results,
        "raw_validate_seconds": raw_validate,
        "raw_commit_seconds": raw_commit,
        "raw_total_seconds": raw_total,
        "median_validate_seconds": _round_seconds(statistics.median(raw_validate)),
        "median_commit_seconds": _round_seconds(statistics.median(raw_commit)),
        "median_total_seconds": _round_seconds(statistics.median(raw_total)),
    }

    record_property("student_import_benchmark", json.dumps(report, ensure_ascii=False))
    print(f"student_import_benchmark={json.dumps(report, ensure_ascii=False, sort_keys=True)}")

    assert len(trial_results) == TRIALS
    assert all(result["rows"] == ROW_COUNT for result in trial_results)
