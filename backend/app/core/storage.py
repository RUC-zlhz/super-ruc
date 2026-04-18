"""MinIO 对象存储客户端封装。

提供统一的 bucket 创建、上传、下载预签名 URL 生成能力。
所有附件/模板/导出文件都通过本模块收敛调用。
"""
from __future__ import annotations

import io
import logging
from datetime import timedelta
from functools import lru_cache
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)


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
    client = get_minio_client()
    return client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_key,
        expires=timedelta(minutes=expires_minutes),
    )


def remove_object(bucket: str, object_key: str) -> None:
    client = get_minio_client()
    try:
        client.remove_object(bucket, object_key)
    except S3Error as e:
        logger.warning("remove_object(%s/%s) failed: %s", bucket, object_key, e)
