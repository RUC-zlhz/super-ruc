"""data_dict 数据库操作。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data_dict.models import DataDict


async def list_by_type(db: AsyncSession, dict_type: str) -> list[DataDict]:
    """按字典类型列出所有启用选项，按 sort_order 排序。"""
    stmt = (
        select(DataDict)
        .where(DataDict.dict_type == dict_type, DataDict.is_active.is_(True))
        .order_by(DataDict.sort_order, DataDict.id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_item(
    db: AsyncSession,
    dict_type: str,
    value: str,
    label: str,
    sort_order: int = 0,
) -> DataDict:
    """创建字典条目（幂等：若已存在则返回已有）。"""
    existing = await db.execute(
        select(DataDict).where(DataDict.dict_type == dict_type, DataDict.value == value)
    )
    item = existing.scalar_one_or_none()
    if item is not None:
        if not item.is_active:
            item.is_active = True
            item.label = label
        return item

    item = DataDict(dict_type=dict_type, value=value, label=label, sort_order=sort_order)
    db.add(item)
    await db.flush()
    return item


async def delete_item(db: AsyncSession, item_id: int) -> bool:
    """删除字典条目（软删除：标记 is_active=False）。"""
    result = await db.execute(select(DataDict).where(DataDict.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        return False
    item.is_active = False
    return True
