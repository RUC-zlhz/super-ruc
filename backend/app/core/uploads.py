"""Shared upload helpers."""
from __future__ import annotations

from fastapi import UploadFile, status

from app.core.config import settings
from app.core.exceptions import BizError

DEFAULT_UPLOAD_CHUNK_SIZE = 1024 * 1024


async def read_upload_file_limited(
    file: UploadFile,
    *,
    max_bytes: int | None = None,
    too_large_message: str | None = None,
    too_large_code: int = 41300,
    chunk_size: int = DEFAULT_UPLOAD_CHUNK_SIZE,
) -> bytes:
    """Read an UploadFile with a hard byte limit before materializing all content."""
    limit = max_bytes if max_bytes is not None else settings.UPLOAD_MAX_SIZE_BYTES
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise BizError(
                too_large_message or f"文件超过 {settings.UPLOAD_MAX_SIZE_MB} MB 上限",
                code=too_large_code,
                http_status=status.HTTP_413_CONTENT_TOO_LARGE,
            )
        chunks.append(chunk)
    return b"".join(chunks)
