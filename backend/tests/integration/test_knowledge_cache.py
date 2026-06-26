"""S75 后续：知识库热点只读缓存——命中 + 写操作事件失效。

缓存默认在测试中关闭（conftest CACHE_ENABLED=false），本文件用 monkeypatch 单独开启。
需 docker-compose 的 Redis 在线。
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete_prefix
from app.core.config import settings
from app.knowledge.models import KnowledgeEntry

_CACHE_PREFIX = "knowledge:"


async def _create_published_entry(
    admin_client: AsyncClient, *, slug: str, title: str
) -> int:
    src = await admin_client.post(
        "/api/v1/admin/knowledge/sources",
        json={
            "source_name": "缓存测试来源",
            "source_url": "https://example.edu/cache-test",
            "issuing_org": "测试",
            "version_label": "v1",
        },
    )
    assert src.status_code == 200, src.text
    entry = await admin_client.post(
        "/api/v1/admin/knowledge/entries",
        json={
            "slug": slug,
            "title": title,
            "summary": "缓存测试条目",
            "category_code": "LEAVE",
            "body_md": "正文",
            "source_id": src.json()["data"]["id"],
            "version_label": "v1",
            "tags": ["缓存"],
        },
    )
    assert entry.status_code == 200, entry.text
    entry_id = entry.json()["data"]["id"]
    pub = await admin_client.post(
        f"/api/v1/admin/knowledge/entries/{entry_id}/publish",
        json={"note": "publish"},
    )
    assert pub.status_code == 200, pub.text
    return entry_id


async def test_entry_detail_cached_then_invalidated_on_write(
    admin_client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "CACHE_ENABLED", True)
    await cache_delete_prefix(_CACHE_PREFIX)

    entry_id = await _create_published_entry(
        admin_client, slug="cache-detail", title="原始标题"
    )

    # 1) 学生端详情 -> 写入缓存
    d1 = await admin_client.get(f"/api/v1/knowledge/{entry_id}")
    assert d1.status_code == 200, d1.text
    assert d1.json()["data"]["title"] == "原始标题"

    # 2) 直接改库（绕过 service，不触发失效）
    row = await db.get(KnowledgeEntry, entry_id)
    assert row is not None
    row.title = "直改未失效"
    await db.commit()

    # 3) 再读 -> 仍返回缓存旧值，证明缓存命中（DB 已是新值）
    d2 = await admin_client.get(f"/api/v1/knowledge/{entry_id}")
    assert d2.json()["data"]["title"] == "原始标题"

    # 4) 走 service 的更新 -> 触发知识缓存命名空间失效
    upd = await admin_client.patch(
        f"/api/v1/admin/knowledge/entries/{entry_id}",
        json={"title": "已更新标题"},
    )
    assert upd.status_code == 200, upd.text

    # 5) 再读 -> 反映新值，证明写失效生效
    d3 = await admin_client.get(f"/api/v1/knowledge/{entry_id}")
    assert d3.json()["data"]["title"] == "已更新标题"

    await cache_delete_prefix(_CACHE_PREFIX)


async def test_categories_cache_invalidated_on_upsert(
    admin_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "CACHE_ENABLED", True)
    await cache_delete_prefix(_CACHE_PREFIX)

    first = await admin_client.get("/api/v1/knowledge/categories")
    assert first.status_code == 200, first.text
    # 第二次命中缓存，数据一致
    cached = await admin_client.get("/api/v1/knowledge/categories")
    assert {c["code"] for c in cached.json()["data"]} == {
        c["code"] for c in first.json()["data"]
    }

    new_code = "CACHE_TEST_CAT"
    up = await admin_client.post(
        "/api/v1/admin/knowledge/categories",
        json={"code": new_code, "name": "缓存测试分类", "sort_order": 999},
    )
    assert up.status_code == 200, up.text

    after = await admin_client.get("/api/v1/knowledge/categories")
    assert new_code in {c["code"] for c in after.json()["data"]}

    await cache_delete_prefix(_CACHE_PREFIX)
