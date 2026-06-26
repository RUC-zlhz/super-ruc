"""轻量 Redis 缓存：热点只读结果缓存。

设计原则
--------
- **故障降级**：任何 Redis 异常都不得让业务请求失败——读失败当未命中（直算），
  写失败静默忽略。缓存只是加速层，绝不能成为硬依赖。
- **可开关**：`settings.CACHE_ENABLED=False` 时所有操作短路为 no-op（测试默认关，保证确定性）。
- 复用 scheduler 相同的 `Redis.from_url(..., decode_responses=True)` 连接方式。
"""
from __future__ import annotations

import logging

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis: Redis | None = None


def _get_client() -> Redis | None:
    global _redis
    if not settings.CACHE_ENABLED:
        return None
    if _redis is None:
        _redis = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def cache_get_text(key: str) -> str | None:
    """读缓存；未配置/未命中/故障一律返回 None（调用方据此直算）。"""
    client = _get_client()
    if client is None:
        return None
    try:
        return await client.get(key)
    except Exception as exc:  # noqa: BLE001 — 缓存故障降级为直算
        logger.warning("cache get failed key=%s: %s", key, exc)
        return None


async def cache_set_text(key: str, value: str, ttl_seconds: int) -> None:
    """写缓存（带 TTL）；故障静默忽略。"""
    client = _get_client()
    if client is None:
        return
    try:
        await client.set(key, value, ex=ttl_seconds)
    except Exception as exc:  # noqa: BLE001 — 缓存故障不影响主流程
        logger.warning("cache set failed key=%s: %s", key, exc)


async def cache_delete_prefix(prefix: str) -> int:
    """按前缀批量删除（SCAN 渐进，不阻塞）。返回删除条数。"""
    client = _get_client()
    if client is None:
        return 0
    deleted = 0
    try:
        async for key in client.scan_iter(match=f"{prefix}*", count=200):
            await client.delete(key)
            deleted += 1
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache delete prefix failed prefix=%s: %s", prefix, exc)
    return deleted


async def close_cache() -> None:
    """应用关闭时释放连接。"""
    global _redis
    if _redis is not None:
        try:
            await _redis.aclose()
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache close failed: %s", exc)
        _redis = None
