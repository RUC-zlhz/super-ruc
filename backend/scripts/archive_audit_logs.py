"""定时任务脚本：审计日志归档（v1.5 / NFR-002）。

示例 crontab（每日 03:30 触发）：
    30 3 * * *  cd /opt/sip/backend && /opt/sip/.venv/bin/python -m scripts.archive_audit_logs

或通过系统任务调度器（Windows Task Scheduler / systemd timer）调用。
"""
from __future__ import annotations

import argparse
import asyncio
import logging

from app.audit.service import DEFAULT_RETENTION_DAYS, archive_expired_logs
from app.core.database import AsyncSessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def _main(retention_days: int, batch_size: int) -> None:
    async with AsyncSessionLocal() as db:
        summary = await archive_expired_logs(
            db, retention_days=retention_days, batch_size=batch_size
        )
        logger.info("archive summary: %s", summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SIP audit log archive job")
    parser.add_argument(
        "--retention-days", type=int, default=DEFAULT_RETENTION_DAYS,
        help="保留天数，默认 180 (~1 学期)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000,
        help="每批搬迁条数，默认 1000",
    )
    args = parser.parse_args()
    asyncio.run(_main(args.retention_days, args.batch_size))
