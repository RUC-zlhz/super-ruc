"""Runtime scheduler for workflow reminder jobs."""
from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import uuid

from redis.asyncio import Redis

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.workflow import service as workflow_service

logger = logging.getLogger(__name__)

_LOCK_KEY = "sip:workflow-reminder:lock"
_LOCK_VALUE = f"{os.getpid()}:{uuid.uuid4().hex}"


class WorkflowReminderScheduler:
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
            name="workflow-reminder-scheduler",
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
            ex=settings.WORKFLOW_REMINDER_LOCK_TTL_SECONDS,
            nx=True,
        )
        if not lock_acquired:
            logger.info("skip workflow reminder run because another worker holds the lock")
            return False

        try:
            async with AsyncSessionLocal() as db:
                run = await workflow_service.run_reminder_cycle(
                    db,
                    as_of=None,
                    channel=settings.WORKFLOW_REMINDER_CHANNEL,
                    trigger_mode="AUTO",
                    operator_id=None,
                    operator_role=None,
                )
            logger.info(
                "workflow reminder scheduler run completed | run_id=%s created=%s sent=%s skipped=%s failed=%s",
                run.id,
                run.created_count,
                run.sent_count,
                run.skipped_count,
                run.failed_count,
            )
            return True
        finally:
            if self._redis is not None and (await self._redis.get(_LOCK_KEY)) == _LOCK_VALUE:
                await self._redis.delete(_LOCK_KEY)

    async def _run_forever(self) -> None:
        logger.info(
            "workflow reminder scheduler started | interval_minutes=%s channel=%s",
            settings.WORKFLOW_REMINDER_INTERVAL_MINUTES,
            settings.WORKFLOW_REMINDER_CHANNEL,
        )
        delay = settings.WORKFLOW_REMINDER_INTERVAL_MINUTES * 60
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=delay)
                break
            except TimeoutError:
                try:
                    await self.run_once()
                except Exception:  # noqa: BLE001
                    logger.exception("workflow reminder scheduler run failed")


_scheduler: WorkflowReminderScheduler | None = None


def get_workflow_reminder_scheduler() -> WorkflowReminderScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = WorkflowReminderScheduler()
    return _scheduler
