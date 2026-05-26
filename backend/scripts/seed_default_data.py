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
from scripts import import_common_template_examples as example_templates
from scripts import import_party_platform_file2_knowledge as example_knowledge

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
        knowledge_sources, knowledge_entries, knowledge_skipped_due_to_existing = (
            await example_knowledge.import_party_platform_file2_knowledge(
                session,
                only_missing=True,
                skip_if_any_entries=True,
            )
        )
        template_sources, template_assets, template_entries, template_skipped_due_to_existing = (
            await example_templates.import_common_template_examples(
                session,
                only_missing=True,
                skip_if_any_templates=True,
            )
        )
        await session.commit()
    logger.info(
        "default data seeded: students inserted=%s updated=%s skipped=%s; "
        "curriculum inserted=%s updated=%s skipped=%s; "
        "knowledge sources created=%s updated=%s skipped=%s; "
        "knowledge entries created=%s updated=%s skipped=%s; "
        "knowledge skipped_due_to_existing=%s; "
        "template sources created=%s updated=%s skipped=%s; "
        "template assets created=%s updated=%s skipped=%s; "
        "template entries created=%s updated=%s skipped=%s; "
        "templates skipped_due_to_existing=%s",
        students.created_count,
        students.updated_count,
        students.skipped_count,
        curriculum.created_count,
        curriculum.updated_count,
        curriculum.skipped_count,
        knowledge_sources["created"],
        knowledge_sources["updated"],
        knowledge_sources["skipped"],
        knowledge_entries["created"],
        knowledge_entries["updated"],
        knowledge_entries["skipped"],
        knowledge_skipped_due_to_existing,
        template_sources["created"],
        template_sources["updated"],
        template_sources["skipped"],
        template_assets["created"],
        template_assets["updated"],
        template_assets["skipped"],
        template_entries["created"],
        template_entries["updated"],
        template_entries["skipped"],
        template_skipped_due_to_existing,
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
