"""S12 默认学生花名册与培养方案 bootstrap。

该入口有意独立于 `seed_initial.py`：`seed_initial` 保持基础字典/账号种子，
默认学生与培养方案作为演示/验收 bootstrap 单独执行。
"""
from __future__ import annotations

import asyncio
import logging
import sys

from app.core.database import AsyncSessionLocal
from app.exchange import default_imports

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("seed-default-data")


async def _main() -> int:
    async with AsyncSessionLocal() as session:
        students = await default_imports.import_default_students(
            session,
            operator_id=None,
            operator_role="SEED_DEFAULT_DATA",
        )
        curriculum = await default_imports.import_default_curriculum(
            session,
            operator_id=None,
            operator_role="SEED_DEFAULT_DATA",
        )
    logger.info(
        "default data seeded: students inserted=%s updated=%s skipped=%s; "
        "curriculum inserted=%s updated=%s skipped=%s",
        students.created_count,
        students.updated_count,
        students.skipped_count,
        curriculum.created_count,
        curriculum.updated_count,
        curriculum.skipped_count,
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
