from __future__ import annotations

import pytest_asyncio
from pydantic import ValidationError

from app.core.config import settings
from app.core.workflow_reminder_scheduler import (
    _LOCK_KEY,
    WorkflowReminderScheduler,
)
from app.workflow.schemas import ReminderGenerateIn, WorkflowNodeIn


@pytest_asyncio.fixture(scope="session", autouse=True, loop_scope="session")
async def _prepare_database():
    yield


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def _clean_between_tests():
    yield


class _FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def set(self, key: str, value: str, *, ex: int | None = None, nx: bool = False):
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    async def get(self, key: str):
        return self.store.get(key)

    async def delete(self, key: str):
        self.store.pop(key, None)

    async def aclose(self):
        return None


class _FakeSessionFactory:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _RunResult:
    id = 11
    created_count = 2
    sent_count = 2
    skipped_count = 1
    failed_count = 0


async def test_workflow_reminder_scheduler_run_once_honors_lock(monkeypatch) -> None:
    scheduler = WorkflowReminderScheduler()
    scheduler._redis = _FakeRedis()
    calls: list[tuple[str | None, str, str | None]] = []

    async def fake_run_cycle(_db, *, as_of, channel: str | None, trigger_mode: str, operator_id, operator_role):
        calls.append((as_of, channel, trigger_mode))
        return _RunResult()

    monkeypatch.setattr(
        "app.core.workflow_reminder_scheduler.workflow_service.run_reminder_cycle",
        fake_run_cycle,
    )
    monkeypatch.setattr(
        "app.core.workflow_reminder_scheduler.AsyncSessionLocal",
        _FakeSessionFactory,
    )

    ran = await scheduler.run_once()
    assert ran is True
    assert calls == [(None, settings.WORKFLOW_REMINDER_CHANNEL, "AUTO")]

    scheduler._redis.store[_LOCK_KEY] = "occupied-by-other"
    ran_again = await scheduler.run_once()
    assert ran_again is False


def test_workflow_reminder_schema_rejects_external_channels() -> None:
    assert ReminderGenerateIn(channel="IN_APP").channel == "IN_APP"
    try:
        ReminderGenerateIn(channel="SMS")
    except ValidationError as exc:
        assert "流程提醒一期仅支持站内提醒 IN_APP" in str(exc)
    else:
        raise AssertionError("SMS reminder channel should be rejected")

    try:
        WorkflowNodeIn(code="N1", name="节点", reminder_channel="EMAIL")
    except ValidationError as exc:
        assert "流程提醒一期仅支持站内提醒 IN_APP" in str(exc)
    else:
        raise AssertionError("EMAIL reminder channel should be rejected")
