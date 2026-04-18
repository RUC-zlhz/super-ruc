"""知识库分类种子（FR-001）。

扁平结构，覆盖一期主业务域：党团、奖助、学业、事务办理、请假证明。
新增分类应保持 `code` 稳定，`sort_order` 以 10 为步长便于插入新项。
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.models import KnowledgeCategory
from scripts.seed import SeedResult
from scripts.seed._upsert import upsert_by_code

DOMAIN = "knowledge_categories"

_CATEGORIES: list[dict] = [
    {"code": "PARTY", "name": "党员发展", "sort_order": 10},
    {"code": "YOUTH_LEAGUE", "name": "团员管理", "sort_order": 20},
    {"code": "SCHOLARSHIP", "name": "奖助学金", "sort_order": 30},
    {"code": "ACADEMIC", "name": "学业管理", "sort_order": 40},
    {"code": "CERTIFICATE", "name": "证明与盖章", "sort_order": 50},
    {"code": "LEAVE", "name": "请假与销假", "sort_order": 60},
    {"code": "DAILY_AFFAIRS", "name": "日常事务", "sort_order": 70},
    {"code": "OTHER", "name": "其他", "sort_order": 99},
]


async def seed(db: AsyncSession) -> SeedResult:
    outcome = await upsert_by_code(
        db, KnowledgeCategory, _CATEGORIES,
        update_fields=("name", "sort_order", "is_active"),
    )
    return SeedResult(
        domain=DOMAIN,
        inserted=outcome.inserted,
        updated=outcome.updated,
        skipped=outcome.skipped,
    )
