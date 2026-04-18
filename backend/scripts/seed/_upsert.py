"""种子脚本通用 upsert 工具。

设计目标：
- 以业务唯一键（通常是 `code`）判重，避免重复插入。
- 可指定需要"更新覆盖"的字段白名单；未列出的字段保留现状，避免覆盖线上人工调整。
- 所有操作在调用方的事务中进行（种子脚本自己决定何时 commit）。
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base


@dataclass(slots=True)
class UpsertOutcome:
    inserted: int = 0
    updated: int = 0
    skipped: int = 0

    def record(self, action: str) -> None:
        if action == "insert":
            self.inserted += 1
        elif action == "update":
            self.updated += 1
        else:
            self.skipped += 1


async def upsert_by_code(
    db: AsyncSession,
    model: type[Base],
    records: Iterable[dict[str, Any]],
    *,
    unique_field: str = "code",
    update_fields: Iterable[str] | None = None,
) -> UpsertOutcome:
    """按 `unique_field` 逐条 upsert 指定模型。

    :param records: 数据字典列表，必须包含 `unique_field`
    :param update_fields: 当记录已存在时需要覆盖的字段；None 表示只做幂等插入
    """
    outcome = UpsertOutcome()
    column = getattr(model, unique_field)
    update_set = set(update_fields or ())

    for data in records:
        key = data[unique_field]
        existing = (
            await db.execute(select(model).where(column == key))
        ).scalar_one_or_none()

        if existing is None:
            db.add(model(**data))
            outcome.record("insert")
            continue

        if not update_set:
            outcome.record("skip")
            continue

        changed = False
        for field in update_set:
            if field not in data:
                continue
            new_value = data[field]
            if getattr(existing, field) != new_value:
                setattr(existing, field, new_value)
                changed = True
        outcome.record("update" if changed else "skip")

    await db.flush()
    return outcome
