"""基线 smoke test：conftest 能拉起 app + DB，/healthz 返回 ok。"""
from __future__ import annotations

from httpx import AsyncClient


async def test_healthz(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "ok"


async def test_categories_seeded(client: AsyncClient) -> None:
    """知识分类字典由 SEEDERS 写入，/knowledge/categories 无需鉴权。"""
    resp = await client.get("/api/v1/knowledge/categories")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    codes = {c["code"] for c in body["data"]}
    assert {"PARTY", "YOUTH_LEAGUE", "SCHOLARSHIP", "OTHER"}.issubset(codes)
