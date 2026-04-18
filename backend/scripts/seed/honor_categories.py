"""荣誉类别种子（FR-017 附录：校级及以上正式荣誉分类）。

原则：
- 仅收录"校级及以上"类别；班级/学院小型荣誉不纳入本公示体系。
- `code` 写入即永久字段，修改前需同步迁移脚本，否则会造成历史条目的孤儿类别。
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.honor.models import HonorCategory
from scripts.seed import SeedResult
from scripts.seed._upsert import upsert_by_code

DOMAIN = "honor_categories"

_CATEGORIES: list[dict] = [
    {"code": "NATIONAL_SCHOLARSHIP", "name": "国家奖学金",
     "description": "教育部评定的国家级本专科奖学金", "sort_order": 10},
    {"code": "NATIONAL_INSPIRATION_SCHOLARSHIP", "name": "国家励志奖学金",
     "description": "面向家庭经济困难学生的国家级奖学金", "sort_order": 20},
    {"code": "SCHOOL_EXCELLENT_STUDENT", "name": "校级优秀学生",
     "description": "学校层面评定的优秀学生", "sort_order": 30},
    {"code": "SCHOOL_EXCELLENT_CADRE", "name": "校级优秀学生干部",
     "description": "学校层面评定的优秀学生干部", "sort_order": 40},
    {"code": "EXCELLENT_YOUTH_LEAGUE_MEMBER", "name": "优秀共青团员",
     "description": "校级/市级/省级优秀共青团员", "sort_order": 50},
    {"code": "ADVANCED_CLASS", "name": "先进班集体",
     "description": "校级及以上先进班集体", "sort_order": 60},
    {"code": "COMPETITION_NATIONAL", "name": "学科竞赛国家级奖项",
     "description": "国家级学科竞赛获奖（如全国大学生数学建模竞赛等）", "sort_order": 70},
    {"code": "COMPETITION_PROVINCIAL", "name": "学科竞赛省部级奖项",
     "description": "省部级学科竞赛获奖", "sort_order": 80},
    {"code": "OTHER_OFFICIAL_HONOR", "name": "其他正式荣誉",
     "description": "其他经红头文件或正式证书认定的校级及以上荣誉", "sort_order": 99},
]


async def seed(db: AsyncSession) -> SeedResult:
    outcome = await upsert_by_code(
        db, HonorCategory, _CATEGORIES,
        update_fields=("name", "description", "sort_order", "is_active"),
    )
    return SeedResult(
        domain=DOMAIN,
        inserted=outcome.inserted,
        updated=outcome.updated,
        skipped=outcome.skipped,
    )
