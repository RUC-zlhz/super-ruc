from __future__ import annotations

from io import BytesIO

import pytest
from starlette.datastructures import UploadFile

from app.core.exceptions import BizError
from app.core.uploads import read_upload_file_limited


def _upload(data: bytes) -> UploadFile:
    return UploadFile(file=BytesIO(data), filename="payload.bin")


async def test_read_upload_file_limited_accepts_small_and_exact_limit() -> None:
    assert await read_upload_file_limited(_upload(b"abc"), max_bytes=3, chunk_size=2) == b"abc"
    assert await read_upload_file_limited(_upload(b"ab"), max_bytes=3, chunk_size=2) == b"ab"


async def test_read_upload_file_limited_rejects_over_limit() -> None:
    with pytest.raises(BizError) as exc_info:
        await read_upload_file_limited(_upload(b"abcd"), max_bytes=3, chunk_size=2)

    assert exc_info.value.http_status == 413
    assert exc_info.value.code == 41300
