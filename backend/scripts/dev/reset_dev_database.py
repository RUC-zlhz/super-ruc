"""Reset the local development database schema.

This script is intentionally development-only. It removes all database content
so a startup script can rebuild the schema through Alembic and seed data from
the repository sources.
"""
from __future__ import annotations

import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.kingbase import install_sqlalchemy_kingbase_patch


async def _reset_schema() -> None:
    if settings.IS_PROD:
        raise RuntimeError("Refusing to reset database when APP_ENV=prod.")

    url = settings.KINGBASE_MIGRATION_URL or settings.DATABASE_URL
    install_sqlalchemy_kingbase_patch()
    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    finally:
        await engine.dispose()


def main() -> int:
    asyncio.run(_reset_schema())
    print("development database schema reset complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
