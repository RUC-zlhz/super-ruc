"""Runtime scheduler for audit archive jobs."""
from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import uuid
from datetime import datetime, timedelta

from redis.asyncio import Redis

from app.audit.service import archive_expired_logs
from app.core.config import settings
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

_LOCK_KEY = "sip:audit-archive:lock"
_LOCK_VALUE = f"{os.getpid()}:{uuid.uuid4().hex}"


def _parse_run_at(value: str) -> tuple[int, int]:
    hour_text, minute_text = value.split(":", 1)
    return int(hour_text), int(minute_text)


def seconds_until_next_run(run_at: str, *, now: datetime | None = None) -> float:
    current = now or datetime.now().astimezone()
    hour, minute = _parse_run_at(run_at)
    target = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= current:
        target += timedelta(days=1)
    return max((target - current).total_seconds(), 0.0)


class AuditArchiveScheduler:
    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._redis: Redis | None = None

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event = asyncio.Event()
        self._redis = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        self._task = asyncio.create_task(
            self._run_forever(),
            name="audit-archive-scheduler",
        )

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    async def run_once(self) -> bool:
        if self._redis is None:
            self._redis = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        lock_acquired = await self._redis.set(
            _LOCK_KEY,
            _LOCK_VALUE,
            ex=settings.AUDIT_ARCHIVE_LOCK_TTL_SECONDS,
            nx=True,
        )
        if not lock_acquired:
            logger.info("skip audit archive run because another worker holds the lock")
            return False

        try:
            async with AsyncSessionLocal() as db:
                summary = await archive_expired_logs(
                    db,
                    retention_days=settings.AUDIT_ARCHIVE_RETENTION_DAYS,
                    batch_size=settings.AUDIT_ARCHIVE_BATCH_SIZE,
                )
            logger.info("audit archive scheduler run completed | %s", summary)
            return True
        finally:
            if self._redis is not None and (await self._redis.get(_LOCK_KEY)) == _LOCK_VALUE:
                await self._redis.delete(_LOCK_KEY)

    async def _run_forever(self) -> None:
        logger.info(
            "audit archive scheduler started | run_at=%s retention_days=%s batch_size=%s",
            settings.AUDIT_ARCHIVE_RUN_AT,
            settings.AUDIT_ARCHIVE_RETENTION_DAYS,
            settings.AUDIT_ARCHIVE_BATCH_SIZE,
        )
        while not self._stop_event.is_set():
            delay = seconds_until_next_run(settings.AUDIT_ARCHIVE_RUN_AT)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=delay)
                break
            except TimeoutError:
                try:
                    await self.run_once()
                except Exception:  # noqa: BLE001
                    logger.exception("audit archive scheduler run failed")


_scheduler: AuditArchiveScheduler | None = None


def get_audit_archive_scheduler() -> AuditArchiveScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AuditArchiveScheduler()
    return _scheduler
