from __future__ import annotations

from datetime import date, datetime

from app.exchange.service import _parse_date


def test_parse_date_accepts_common_import_formats() -> None:
    assert _parse_date("2024-01-01") == date(2024, 1, 1)
    assert _parse_date("2024/01/01") == date(2024, 1, 1)
    assert _parse_date("2024年1月1日") == date(2024, 1, 1)
    assert _parse_date("2024-01-01T00:00:00+08:00") == date(2024, 1, 1)
    assert _parse_date(datetime(2024, 1, 1, 12, 30)) == date(2024, 1, 1)


def test_parse_date_returns_none_for_invalid_values() -> None:
    assert _parse_date("") is None
    assert _parse_date(None) is None
    assert _parse_date("2024-99-99") is None
