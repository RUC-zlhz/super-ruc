"""Kingbase compatibility helpers for SQLAlchemy PostgreSQL dialects."""
from __future__ import annotations

import re
from functools import wraps
from typing import Any

from sqlalchemy.dialects.postgresql.asyncpg import PGDialect_asyncpg
from sqlalchemy.dialects.postgresql.base import PGDialect

_NUMERIC_VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")
_KINGBASE_MARKER = "kingbasees"
_PATCHED = False


def _parse_numeric_version(value: str) -> tuple[int, ...] | None:
    match = _NUMERIC_VERSION_RE.search(value)
    if not match:
        return None
    return tuple(int(part) for part in match.groups() if part is not None)


def _build_version_parser(original: Any) -> Any:
    @wraps(original)
    def wrapped(self: Any, connection: Any) -> tuple[int, ...]:
        try:
            return original(self, connection)
        except AssertionError as exc:
            banner = str(
                connection.exec_driver_sql("select pg_catalog.version()").scalar()
            )
            if _KINGBASE_MARKER not in banner.lower():
                raise

            server_version = str(
                connection.exec_driver_sql("show server_version").scalar()
            )
            parsed = _parse_numeric_version(server_version)
            if parsed is None:
                raise AssertionError(
                    "Could not determine Kingbase server version from "
                    f"banner={banner!r} server_version={server_version!r}"
                ) from exc
            return parsed

    return wrapped


def install_sqlalchemy_kingbase_patch() -> None:
    global _PATCHED
    if _PATCHED:
        return

    PGDialect._get_server_version_info = _build_version_parser(
        PGDialect._get_server_version_info
    )
    PGDialect_asyncpg._get_server_version_info = _build_version_parser(
        PGDialect_asyncpg._get_server_version_info
    )
    _PATCHED = True
