"""数据种子包。

每个子模块暴露两个对外入口：

- `DOMAIN: str`          领域代号，供 CLI `--only` / `--skip` 过滤
- `async def seed(db)`   执行幂等种子写入，返回 `SeedResult`

注册表 `SEEDERS` 决定执行顺序——角色字典必须先于荣誉类别之前落地，
故在这里按依赖顺序显式列出。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SeedResult:
    """单个种子域的执行报告。"""

    domain: str
    inserted: int = 0
    updated: int = 0
    skipped: int = 0

    @property
    def total(self) -> int:
        return self.inserted + self.updated + self.skipped

    def as_line(self) -> str:
        return (
            f"[{self.domain:<20}] "
            f"inserted={self.inserted:>3} "
            f"updated={self.updated:>3} "
            f"skipped={self.skipped:>3} "
            f"total={self.total:>3}"
        )


# Import submodules *after* SeedResult is defined — they depend on it.
from . import (  # noqa: E402
    admin_user,
    audit_policies,
    data_dicts,
    honor_categories,
    knowledge_categories,
    knowledge_entries,
    proof_templates,
    request_types,
    roles,
    workflow_templates,
)

# 依赖顺序：先角色，再流程/类目字典
SEEDERS = (
    roles,
    admin_user,
    audit_policies,
    data_dicts,
    knowledge_categories,
    knowledge_entries,
    honor_categories,
    request_types,
    proof_templates,
    workflow_templates,
)

__all__ = ["SeedResult", "SEEDERS"]
