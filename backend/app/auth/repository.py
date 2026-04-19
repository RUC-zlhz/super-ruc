"""auth 模块仓储层：User / Role / Student 访问。"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Role, Student, User, UserRole


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_openid(db: AsyncSession, openid: str) -> User | None:
    stmt = select(User).where(User.openid == openid, User.deleted_at.is_(None))
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_user_by_work_no(db: AsyncSession, work_no: str) -> User | None:
    stmt = select(User).where(User.work_no == work_no, User.deleted_at.is_(None))
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_user_from_wechat(
    db: AsyncSession,
    *,
    openid: str,
    unionid: str | None = None,
    display_name: str = "",
) -> User:
    user = User(openid=openid, unionid=unionid, display_name=display_name or openid[:8])
    db.add(user)
    await db.flush()
    return user


async def update_last_login(db: AsyncSession, user: User) -> None:
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()


async def list_user_roles(db: AsyncSession, user_id: int) -> Sequence[UserRole]:
    stmt = select(UserRole).where(UserRole.user_id == user_id)
    return (await db.execute(stmt)).scalars().all()


async def add_user_role(
    db: AsyncSession,
    *,
    user_id: int,
    role_code: str,
    scope_code: str | None = None,
    granted_by: int | None = None,
) -> UserRole:
    ur = UserRole(
        user_id=user_id, role_code=role_code, scope_code=scope_code, granted_by=granted_by
    )
    db.add(ur)
    await db.flush()
    return ur


async def get_student_by_no(db: AsyncSession, student_no: str) -> Student | None:
    stmt = select(Student).where(Student.student_no == student_no, Student.deleted_at.is_(None))
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_role_by_code(db: AsyncSession, code: str) -> Role | None:
    stmt = select(Role).where(Role.code == code)
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_users_by_ids(
    db: AsyncSession, user_ids: set[int] | list[int]
) -> dict[int, User]:
    ids = [int(user_id) for user_id in user_ids if user_id is not None]
    if not ids:
        return {}
    rows = (
        await db.execute(select(User).where(User.id.in_(ids), User.deleted_at.is_(None)))
    ).scalars().all()
    return {row.id: row for row in rows}
