"""全局异常类型与 FastAPI 异常处理器。

所有 API 错误最终封装为统一响应体：{code, message, data}。
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class BizError(Exception):
    """业务异常基类。code 为业务错误码（非 HTTP 状态）。"""

    def __init__(
        self,
        message: str,
        code: int = 40000,
        http_status: int = status.HTTP_400_BAD_REQUEST,
        data: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.data = data


class AuthError(BizError):
    def __init__(self, message: str = "未登录或凭证失效", code: int = 40100) -> None:
        super().__init__(message, code=code, http_status=status.HTTP_401_UNAUTHORIZED)


class PermissionError(BizError):
    def __init__(self, message: str = "无权限执行该操作", code: int = 40300) -> None:
        super().__init__(message, code=code, http_status=status.HTTP_403_FORBIDDEN)


class NotFoundError(BizError):
    def __init__(self, message: str = "资源不存在", code: int = 40400) -> None:
        super().__init__(message, code=code, http_status=status.HTTP_404_NOT_FOUND)


class ConflictError(BizError):
    def __init__(self, message: str = "资源冲突", code: int = 40900) -> None:
        super().__init__(message, code=code, http_status=status.HTTP_409_CONFLICT)


def _envelope(code: int, message: str, data: object | None = None) -> dict:
    return {"code": code, "message": message, "data": data}


def _validation_errors(exc: RequestValidationError) -> object:
    return jsonable_encoder(exc.errors(), custom_encoder={Exception: str})


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BizError)
    async def handle_biz(_: Request, exc: BizError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=_envelope(exc.code, exc.message, exc.data),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.status_code * 100, str(exc.detail), None),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope(42200, "请求参数校验失败", {"errors": _validation_errors(exc)}),
        )

    @app.exception_handler(Exception)
    async def handle_unknown(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("未处理异常", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope(50000, "服务器内部错误", None),
        )
