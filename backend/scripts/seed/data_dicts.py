"""数据字典种子。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data_dict.models import DataDict
from scripts.seed import SeedResult

DOMAIN = "data_dicts"

_DATA_DICTS: list[tuple[str, str, str, int]] = [
    # (dict_type, value, label, sort_order)
    # 性别
    ("student_gender", "男", "男", 10),
    ("student_gender", "女", "女", 20),
    # 年级
    ("student_grade", "2022", "2022", 10),
    ("student_grade", "2023", "2023", 20),
    ("student_grade", "2024", "2024", 30),
    ("student_grade", "2025", "2025", 40),
    ("student_grade", "2026", "2026", 50),
    # 专业
    ("student_major", "计算机科学与技术专业", "计算机科学与技术专业", 10),
    ("student_major", "信息管理与信息系统专业", "信息管理与信息系统专业", 20),
    ("student_major", "软件工程专业", "软件工程专业", 30),
    ("student_major", "信息安全专业", "信息安全专业", 40),
    ("student_major", "数据科学与大数据技术专业", "数据科学与大数据技术专业", 50),
    ("student_major", "数据科学与大数据技术（理学）专业", "数据科学与大数据技术（理学）专业", 60),
    # 政治面貌
    ("political_status", "群众", "群众", 10),
    ("political_status", "共青团员", "共青团员", 20),
    ("political_status", "入党积极分子", "入党积极分子", 30),
    ("political_status", "发展对象", "发展对象", 40),
    ("political_status", "预备党员", "预备党员", 50),
    ("political_status", "中共党员", "中共党员", 60),
    # 入学年份
    ("enrollment_year", "2020", "2020", 10),
    ("enrollment_year", "2021", "2021", 20),
    ("enrollment_year", "2022", "2022", 30),
    ("enrollment_year", "2023", "2023", 40),
    ("enrollment_year", "2024", "2024", 50),
    ("enrollment_year", "2025", "2025", 60),
    ("enrollment_year", "2026", "2026", 70),
    # 预计毕业年份
    ("graduation_year", "2024", "2024", 10),
    ("graduation_year", "2025", "2025", 20),
    ("graduation_year", "2026", "2026", 30),
    ("graduation_year", "2027", "2027", 40),
    ("graduation_year", "2028", "2028", 50),
    ("graduation_year", "2029", "2029", 60),
    ("graduation_year", "2030", "2030", 70),
]


async def seed(db: AsyncSession) -> SeedResult:
    result = SeedResult(domain=DOMAIN)

    for dict_type, value, label, sort_order in _DATA_DICTS:
        existing = await db.execute(
            select(DataDict).where(DataDict.dict_type == dict_type, DataDict.value == value)
        )
        if existing.scalar_one_or_none() is not None:
            result.skipped += 1
            continue
        db.add(DataDict(
            dict_type=dict_type,
            value=value,
            label=label,
            sort_order=sort_order,
        ))
        result.inserted += 1

    return result
