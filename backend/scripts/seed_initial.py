"""初始种子数据入口脚本。

用法示例：
    python -m scripts.seed_initial                # 全量执行
    python -m scripts.seed_initial --only roles   # 仅执行指定域（可重复）
    python -m scripts.seed_initial --skip workflow_templates
    python -m scripts.seed_initial --dry-run      # 只计算不提交

设计约定：
- 每个种子域独立事务：任一域失败，只回滚该域，不影响已提交的前序域。
- 幂等：按业务唯一键 `code` upsert；`update_fields` 决定是否覆盖既有字段。
- 依赖顺序由 `scripts.seed.SEEDERS` 硬编码维护，避免 CLI 输入顺序不当导致外键失败。
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from scripts.seed import SEEDERS, SeedResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("seed")


async def _run_one(session: AsyncSession, module, *, dry_run: bool) -> SeedResult:
    result = await module.seed(session)
    if dry_run:
        await session.rollback()
        logger.info("[DRY-RUN] %s rolled back", module.DOMAIN)
    else:
        await session.commit()
    return result


async def _main(only: set[str], skip: set[str], dry_run: bool) -> int:
    failures: list[str] = []
    for module in SEEDERS:
        domain = module.DOMAIN
        if only and domain not in only:
            continue
        if domain in skip:
            continue

        async with AsyncSessionLocal() as session:
            try:
                result = await _run_one(session, module, dry_run=dry_run)
            except Exception as exc:  # noqa: BLE001
                await session.rollback()
                logger.exception("seed domain %s failed: %s", domain, exc)
                failures.append(domain)
                continue
        logger.info(result.as_line())

    if failures:
        logger.error("seed completed with failures: %s", ", ".join(failures))
        return 1
    logger.info("seed completed successfully")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SIP initial data seeder")
    parser.add_argument(
        "--only", action="append", default=[],
        help="仅执行指定种子域，可多次指定（例：--only roles --only request_types）",
    )
    parser.add_argument(
        "--skip", action="append", default=[],
        help="跳过指定种子域，可多次指定",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只计算不提交；用于校验脚本与数据匹配",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    exit_code = asyncio.run(
        _main(set(args.only), set(args.skip), args.dry_run)
    )
    sys.exit(exit_code)
