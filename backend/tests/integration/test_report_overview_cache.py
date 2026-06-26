"""S75.9: 看板概览 Redis 缓存 —— 命中确定性与失效行为。

缓存默认在测试中关闭（conftest 设 CACHE_ENABLED=false），本文件用 monkeypatch
单独开启，验证缓存命中 / TTL 失效路径。需 docker-compose 的 Redis 在线。
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.cache import cache_delete_prefix
from app.core.config import settings

_OVERVIEW_URL = "/api/v1/admin/report/overview"
_CACHE_PREFIX = "report:overview:"


async def test_overview_served_from_cache_within_ttl(
    admin_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "CACHE_ENABLED", True)
    await cache_delete_prefix(_CACHE_PREFIX)

    first = await admin_client.get(_OVERVIEW_URL)
    assert first.status_code == 200, first.text
    first_generated = first.json()["data"]["generated_at"]

    # 第二次：命中缓存 —— generated_at 完全一致（重算会产生新时间戳）
    second = await admin_client.get(_OVERVIEW_URL)
    assert second.status_code == 200, second.text
    assert second.json()["data"]["generated_at"] == first_generated

    # 缓存失效后应重算，generated_at 变化
    await cache_delete_prefix(_CACHE_PREFIX)
    third = await admin_client.get(_OVERVIEW_URL)
    assert third.status_code == 200, third.text
    assert third.json()["data"]["generated_at"] != first_generated

    await cache_delete_prefix(_CACHE_PREFIX)
