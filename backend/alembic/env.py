"""Alembic 异步迁移入口。

从 app.core.config 读取 `KINGBASE_DATABASE_URL or DATABASE_URL`，
以确保 alembic 与运行时共享同一套配置。
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import inspect, pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.admin_users import models as _admin_user_models  # noqa: F401
from app.audit import models as _audit_models  # noqa: F401

# 导入所有模型以注册到 Base.metadata
from app.auth import models as _auth_models  # noqa: F401
from app.core.config import settings
from app.core.database import Base
from app.exchange import models as _exchange_models  # noqa: F401
from app.honor import models as _honor_models  # noqa: F401
from app.knowledge import models as _knowledge_models  # noqa: F401
from app.notice import models as _notice_models  # noqa: F401
from app.profile import models as _profile_models  # noqa: F401
from app.workflow import models as _workflow_models  # noqa: F401
from app.workflow import quiz_models as _workflow_quiz_models  # noqa: F401

config = context.config
config.set_main_option(
    "sqlalchemy.url",
    settings.KINGBASE_MIGRATION_URL or settings.DATABASE_URL,
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def ensure_alembic_version_capacity(connection: Connection) -> None:
    """Alembic's default VARCHAR(32) is too short for existing named revisions."""

    inspector = inspect(connection)
    if not inspector.has_table("alembic_version"):
        connection.execute(
            text(
                "CREATE TABLE alembic_version "
                "(version_num VARCHAR(128) NOT NULL PRIMARY KEY)"
            )
        )
        return

    version_num = next(
        (
            column
            for column in inspector.get_columns("alembic_version")
            if column["name"] == "version_num"
        ),
        None,
    )
    if version_num is None:
        return

    column_type = version_num["type"]
    length = getattr(column_type, "length", None)
    if length is not None and length < 128:
        connection.execute(
            text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)")
        )


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    ensure_alembic_version_capacity(connection)
    if connection.in_transaction():
        connection.commit()
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
