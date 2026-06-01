"""MinIO 对象存储客户端封装。

提供统一的 bucket 创建、上传、下载预签名 URL 生成能力。
所有附件/模板/导出文件都通过本模块收敛调用。
"""
from __future__ import annotations

import io
import logging
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)


def _use_local_fallback() -> bool:
    return settings.APP_ENV == "test" or bool(settings.LOCAL_OBJECT_STORAGE_ROOT)


def _local_storage_root() -> Path:
    configured_root = settings.LOCAL_OBJECT_STORAGE_ROOT
    if configured_root:
        return Path(configured_root).expanduser()
    return Path(__file__).resolve().parents[3] / "tmp" / "local-object-storage"


def _local_object_path(bucket: str, object_key: str) -> Path:
    parts = [part for part in object_key.replace("\\", "/").split("/") if part]
    return _local_storage_root().joinpath(bucket, *parts)


def _local_store_object(
    *, bucket: str, object_key: str, data: bytes | BinaryIO
) -> str:
    path = _local_object_path(bucket, object_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        payload = data
    else:
        payload = data.read()
    path.write_bytes(payload)
    return object_key


@lru_cache
def get_minio_client() -> Minio:
    client = Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )
    return client


def ensure_bucket(bucket: str) -> None:
    if _use_local_fallback():
        _local_object_path(bucket, ".keep").parent.mkdir(parents=True, exist_ok=True)
        return

    client = get_minio_client()
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info("Created MinIO bucket: %s", bucket)
    except S3Error as e:
        logger.warning("ensure_bucket(%s) failed: %s", bucket, e)


def put_object(
    *,
    bucket: str,
    object_key: str,
    data: bytes | BinaryIO,
    length: int,
    content_type: str = "application/octet-stream",
) -> str:
    """上传对象，返回 object_key。"""
    if _use_local_fallback():
        return _local_store_object(bucket=bucket, object_key=object_key, data=data)

    ensure_bucket(bucket)
    if isinstance(data, bytes):
        stream: BinaryIO = io.BytesIO(data)
    else:
        stream = data
    client = get_minio_client()
    client.put_object(
        bucket_name=bucket,
        object_name=object_key,
        data=stream,
        length=length,
        content_type=content_type,
    )
    return object_key


def presigned_get(bucket: str, object_key: str, expires_minutes: int = 10) -> str:
    if _use_local_fallback():
        return _local_object_path(bucket, object_key).resolve().as_uri()

    client = get_minio_client()
    return client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_key,
        expires=timedelta(minutes=expires_minutes),
    )


def get_object_bytes(bucket: str, object_key: str) -> bytes:
    if _use_local_fallback():
        path = _local_object_path(bucket, object_key)
        return path.read_bytes()

    client = get_minio_client()
    response = client.get_object(bucket, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def remove_object(bucket: str, object_key: str) -> None:
    if _use_local_fallback():
        path = _local_object_path(bucket, object_key)
        try:
            path.unlink(missing_ok=True)
        except OSError as e:
            logger.warning("remove_object(%s/%s) failed: %s", bucket, object_key, e)
        return

    client = get_minio_client()
    try:
        client.remove_object(bucket, object_key)
    except S3Error as e:
        logger.warning("remove_object(%s/%s) failed: %s", bucket, object_key, e)
