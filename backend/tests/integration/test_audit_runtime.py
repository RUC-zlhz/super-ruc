from __future__ import annotations

from datetime import UTC, datetime

import pytest_asyncio

from app.core.audit_archive_scheduler import (
    _LOCK_KEY,
    AuditArchiveScheduler,
    seconds_until_next_run,
)
from app.core.config import settings


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


async def test_audit_archive_scheduler_run_once_honors_lock(monkeypatch) -> None:
    scheduler = AuditArchiveScheduler()
    scheduler._redis = _FakeRedis()
    calls: list[tuple[int, int]] = []

    async def fake_archive(_db, *, retention_days: int, batch_size: int):
        calls.append((retention_days, batch_size))
        return {"moved": 1}

    monkeypatch.setattr("app.core.audit_archive_scheduler.archive_expired_logs", fake_archive)
    monkeypatch.setattr("app.core.audit_archive_scheduler.AsyncSessionLocal", _FakeSessionFactory)

    ran = await scheduler.run_once()
    assert ran is True
    assert calls == [
        (settings.AUDIT_ARCHIVE_RETENTION_DAYS, settings.AUDIT_ARCHIVE_BATCH_SIZE)
    ]

    scheduler._redis.store[_LOCK_KEY] = "occupied-by-other"
    ran_again = await scheduler.run_once()
    assert ran_again is False


def test_seconds_until_next_run_rolls_to_next_day() -> None:
    now = datetime(2026, 4, 20, 4, 0, tzinfo=UTC)
    assert seconds_until_next_run("04:30", now=now) == 1800
    assert seconds_until_next_run("03:30", now=now) == 84600
