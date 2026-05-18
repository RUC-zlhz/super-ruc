"""pytest 集成测试 fixtures。

策略
----
- 专用测试数据库 `sip_db_test`（仍在 docker-compose 的 Postgres 54322 上）。
- session 作用域：建 schema + 初始种子数据（一次）。
- 每个测试前：TRUNCATE 所有业务表（RESTART IDENTITY CASCADE）并重新写入字典种子。
  这样避免了 "service 层自己 commit" 与 "SAVEPOINT rollback" 的冲突——service 里
  `await db.commit()` 如果跑在外层 SAVEPOINT 里，commit 只会释放 savepoint，
  真正提交在外层 rollback 时又被清掉，但对于某些驱动/SA 版本会混乱。
  全表 TRUNCATE + 重塞种子是最鲁棒的做法，每次毫秒级。

必须在 `app.*` import 之前设置 DATABASE_URL，因为 `app.core.config.settings`
在模块加载时立刻求值并被 `create_async_engine()` 消费。
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

# --- env setup: MUST be before any `app.*` import -----------------------
os.environ["APP_ENV"] = "test"
os.environ["APP_DEBUG"] = "true"
os.environ["WECHAT_MOCK_ENABLED"] = "true"
_TESTS_ROOT = Path(__file__).resolve().parent
_MANAGED_LOCAL_OBJECT_STORAGE_ROOT = (
    _TESTS_ROOT / "_runtime" / "local-object-storage"
)
os.environ.setdefault(
    "LOCAL_OBJECT_STORAGE_ROOT", str(_MANAGED_LOCAL_OBJECT_STORAGE_ROOT)
)
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://sip_user:sip_pass_dev@localhost:54322/sip_db_test",
)
# 测试里的网络调用全部走 mock，保证离线可运行
os.environ["AI_QA_ENABLED"] = "false"

from collections.abc import AsyncGenerator, Generator  # noqa: E402

import asyncpg  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.admin_users import models as _admin_user_models  # noqa: F401,E402
from app.audit import models as _audit_models  # noqa: F401,E402

# 导入所有模型以注册到 Base.metadata（同 alembic/env.py）
from app.auth import models as _auth_models  # noqa: F401,E402
from app.core.database import AsyncSessionLocal, Base, engine  # noqa: E402
from app.exchange import models as _exchange_models  # noqa: F401,E402
from app.honor import models as _honor_models  # noqa: F401,E402
from app.knowledge import models as _knowledge_models  # noqa: F401,E402
from app.main import app  # noqa: E402
from app.notice import models as _notice_models  # noqa: F401,E402
from app.profile import models as _profile_models  # noqa: F401,E402
from app.workflow import models as _workflow_models  # noqa: F401,E402
from app.workflow import quiz_models as _workflow_quiz_models  # noqa: F401,E402
from scripts.seed import SEEDERS  # noqa: E402

LOCAL_OBJECT_STORAGE_ROOT = Path(
    os.environ["LOCAL_OBJECT_STORAGE_ROOT"]
).resolve()


def _quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _iter_bootstrap_urls() -> list:
    target_url = make_url(os.environ["DATABASE_URL"])
    explicit = os.environ.get("TEST_DATABASE_BOOTSTRAP_URL")
    if explicit:
        return [make_url(explicit)]

    candidates: list[str] = []
    env_db = os.environ.get("TEST_DATABASE_BOOTSTRAP_DB")
    if env_db:
        candidates.append(env_db)
    candidates.extend(["postgres", "template1", target_url.username or "postgres"])

    urls = []
    seen: set[str] = set()
    for database in candidates:
        if not database or database == target_url.database or database in seen:
            continue
        seen.add(database)
        urls.append(target_url.set(database=database))
    return urls


async def _database_exists(conn: asyncpg.Connection, database_name: str) -> bool:
    for query in (
        "SELECT 1 FROM pg_database WHERE datname = $1",
        "SELECT 1 FROM sys_database WHERE datname = $1",
    ):
        try:
            exists = await conn.fetchval(query, database_name)
        except asyncpg.PostgresError:
            continue
        if exists:
            return True
    return False


async def _ensure_database_exists() -> None:
    target_url = make_url(os.environ["DATABASE_URL"])
    database_name = target_url.database
    if not database_name:
        return

    for bootstrap_url in _iter_bootstrap_urls():
        conn: asyncpg.Connection | None = None
        try:
            conn = await asyncpg.connect(
                user=bootstrap_url.username,
                password=bootstrap_url.password,
                host=bootstrap_url.host or "127.0.0.1",
                port=bootstrap_url.port or 5432,
                database=bootstrap_url.database,
            )
        except (asyncpg.PostgresError, OSError):
            continue

        try:
            if await _database_exists(conn, database_name):
                return
            owner = target_url.username or bootstrap_url.username or "postgres"
            await conn.execute(
                f"CREATE DATABASE {_quote_ident(database_name)} OWNER {_quote_ident(owner)}"
            )
            return
        except asyncpg.DuplicateDatabaseError:
            return
        finally:
            await conn.close()


async def _seed_reference(session: AsyncSession) -> None:
    """写入所有字典/种子数据。不改业务表。"""
    for module in SEEDERS:
        await module.seed(session)


async def _truncate_all(session: AsyncSession) -> None:
    """清空所有业务表；RESTART IDENTITY CASCADE 一次搞定外键和自增。"""
    tables = [
        t.name for t in Base.metadata.sorted_tables if t.name != "alembic_version"
    ]
    if not tables:
        return
    qualified = ", ".join(f'"{n}"' for n in tables)
    await session.execute(text(f"TRUNCATE {qualified} RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture(scope="session", autouse=True, loop_scope="session")
async def _prepare_database() -> AsyncGenerator[None, None]:
    """Drop + Create schema via ORM metadata, then seed reference data once."""
    await _ensure_database_exists()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await _seed_reference(session)
        await session.commit()
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def _clean_between_tests() -> AsyncGenerator[None, None]:
    async with AsyncSessionLocal() as session:
        await _truncate_all(session)
        await _seed_reference(session)
        await session.commit()
    yield


@pytest.fixture(autouse=True)
def _reset_local_object_storage() -> Generator[None, None, None]:
    root = LOCAL_OBJECT_STORAGE_ROOT
    managed_root = _MANAGED_LOCAL_OBJECT_STORAGE_ROOT.resolve()
    is_managed_root = root == managed_root or managed_root in root.parents
    if is_managed_root:
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    yield
    if is_managed_root:
        shutil.rmtree(root, ignore_errors=True)


@pytest_asyncio.fixture(loop_scope="session")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """测试直接访问 DB 用（arrange / assert 环节）。"""
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(loop_scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """进程内调用 FastAPI，不起端口。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(loop_scope="session")
async def admin_token(db: AsyncSession) -> str:
    """创建一个 SUPER_ADMIN 用户并签发 access token（跳过登录流程）。"""
    from app.auth.models import User, UserRole
    from app.core.security import create_token

    user = User(
        work_no="T0001",
        display_name="Test Admin",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_code="SUPER_ADMIN"))
    await db.commit()
    return create_token(str(user.id), "access", extra_claims={"roles": ["SUPER_ADMIN"]})


@pytest_asyncio.fixture(loop_scope="session")
async def admin_client(client: AsyncClient, admin_token: str) -> AsyncClient:
    client.headers["Authorization"] = f"Bearer {admin_token}"
    return client


@pytest_asyncio.fixture(loop_scope="session")
async def counselor_token(db: AsyncSession) -> str:
    """辅导员账号：COUNSELOR 在多数 request_type 的 approver_roles 中。"""
    from app.auth.models import User, UserRole
    from app.core.security import create_token

    user = User(work_no="T0002", display_name="Test Counselor", is_active=True)
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_code="COUNSELOR"))
    await db.commit()
    return create_token(str(user.id), "access", extra_claims={"roles": ["COUNSELOR"]})


@pytest_asyncio.fixture(loop_scope="session")
async def counselor_headers(counselor_token: str) -> dict[str, str]:
    """按请求独立携带，避免和 admin_client 的 Authorization 相互覆盖。"""
    return {"Authorization": f"Bearer {counselor_token}"}
