"""Default administrator account seeder.

Creates a first-run SUPER_ADMIN user with work_no=admin and password=admin123.
The password is only written when the account does not exist or has no password,
so later manual password changes are preserved by repeated seed runs.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.bootstrap import (
    INITIAL_ADMIN_DISPLAY_NAME,
    INITIAL_ADMIN_PLAIN,
    INITIAL_ADMIN_WORK_NO,
)
from app.auth.models import User
from app.auth.repository import ensure_user_role
from app.core.security import hash_password
from scripts.seed import SeedResult

DOMAIN = "admin_user"


async def seed(db: AsyncSession) -> SeedResult:
    inserted = 0
    updated = 0
    skipped = 0

    user = (
        await db.execute(
            select(User).where(
                User.work_no == INITIAL_ADMIN_WORK_NO,
                User.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()

    if user is None:
        user = User(
            work_no=INITIAL_ADMIN_WORK_NO,
            display_name=INITIAL_ADMIN_DISPLAY_NAME,
            password_hash=hash_password(INITIAL_ADMIN_PLAIN),
            is_active=True,
        )
        db.add(user)
        await db.flush()
        inserted += 1
    elif user.password_hash is None:
        user.password_hash = hash_password(INITIAL_ADMIN_PLAIN)
        if not user.display_name:
            user.display_name = INITIAL_ADMIN_DISPLAY_NAME
        updated += 1
        await db.flush()
    else:
        skipped += 1

    await ensure_user_role(
        db,
        user_id=user.id,
        role_code="SUPER_ADMIN",
        granted_by=user.id,
    )
    return SeedResult(domain=DOMAIN, inserted=inserted, updated=updated, skipped=skipped)
