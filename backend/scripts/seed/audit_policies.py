"""字段权限矩阵种子。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import RoleFieldPolicy
from app.audit.policies import iter_default_role_field_policies
from scripts.seed import SeedResult

DOMAIN = "audit_policies"


async def seed(db: AsyncSession) -> SeedResult:
    inserted = 0
    updated = 0
    skipped = 0

    for payload in iter_default_role_field_policies():
        existing = (
            await db.execute(
                select(RoleFieldPolicy).where(
                    RoleFieldPolicy.role_code == payload["role_code"],
                    RoleFieldPolicy.entity_code == payload["entity_code"],
                    RoleFieldPolicy.field_name == payload["field_name"],
                )
            )
        ).scalar_one_or_none()

        if existing is None:
            db.add(RoleFieldPolicy(**payload))
            inserted += 1
            continue

        changed = False
        for field in ("can_read", "can_write", "mask_strategy"):
            if getattr(existing, field) != payload[field]:
                setattr(existing, field, payload[field])
                changed = True
        if changed:
            updated += 1
        else:
            skipped += 1

    await db.flush()
    return SeedResult(
        domain=DOMAIN,
        inserted=inserted,
        updated=updated,
        skipped=skipped,
    )
