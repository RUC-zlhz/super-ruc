"""统一响应包装：{ code: 0, message: "ok", data: ... }。"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = Field(default=0, description="业务错误码；0 表示成功")
    message: str = Field(default="ok")
    data: T | None = None


def ok(data: T | None = None, message: str = "ok") -> ApiResponse[T]:
    return ApiResponse[T](code=0, message=message, data=data)


class PageMeta(BaseModel):
    page: int = 1
    size: int = 20
    total: int = 0


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMeta
