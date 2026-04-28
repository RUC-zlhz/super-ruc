"""FastAPI 应用入口。

- 路由挂载：所有模块路由统一挂载到 /api/v1 前缀下
- 异常处理：BizError / 校验失败 / 500 统一封装为 {code, message, data}
- 中间件：CORS、请求 ID（简易）
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.audit.router import router as audit_router
from app.auth.router import admin_router as auth_admin_router
from app.auth.router import router as auth_router
from app.core.audit_archive_scheduler import get_audit_archive_scheduler
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.response import ApiResponse, ok
from app.exchange.router import curriculum_router as curriculum_router
from app.exchange.router import router as exchange_router
from app.honor.router import admin_router as honor_admin_router
from app.honor.router import router as honor_router
from app.knowledge.router import admin_router as knowledge_admin_router
from app.knowledge.router import router as knowledge_router
from app.notice.router import admin_router as notice_admin_router
from app.notice.router import router as notice_router
from app.profile.router import admin_router as profile_admin_router
from app.profile.router import router as profile_router
from app.report.router import router as report_router
from app.workflow.router import admin_router as workflow_admin_router
from app.workflow.router import quiz_router as quiz_router
from app.workflow.router import request_router as request_router
from app.workflow.router import router as workflow_router

logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "SIP backend starting up | env=%s debug=%s prefix=%s",
        settings.APP_ENV,
        settings.APP_DEBUG,
        settings.API_V1_PREFIX,
    )
    scheduler = None
    if settings.AUDIT_ARCHIVE_ENABLED:
        scheduler = get_audit_archive_scheduler()
        await scheduler.start()
        logger.info("audit archive scheduler enabled")
    else:
        logger.info("audit archive scheduler disabled")
    yield
    if scheduler is not None:
        await scheduler.stop()
    logger.info("SIP backend shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="SIP Backend",
        description="信息学院学生综合服务与党团管理平台 — 后端 API",
        version="0.1.0",
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
        openapi_url="/openapi.json" if settings.APP_DEBUG else None,
        lifespan=lifespan,
    )

    # CORS — 管理前端 & 学生端均为跨域
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.IS_DEV else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/", include_in_schema=False)
    async def root() -> ApiResponse[dict]:
        return ok({"service": "sip-backend", "version": "0.1.0", "env": settings.APP_ENV})

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> ApiResponse[dict]:
        return ok({"status": "ok"})

    prefix = settings.API_V1_PREFIX
    app.include_router(auth_router, prefix=prefix)
    app.include_router(auth_admin_router, prefix=prefix)
    app.include_router(knowledge_router, prefix=prefix)
    app.include_router(knowledge_admin_router, prefix=prefix)
    app.include_router(workflow_router, prefix=prefix)
    app.include_router(request_router, prefix=prefix)
    app.include_router(workflow_admin_router, prefix=prefix)
    app.include_router(quiz_router, prefix=prefix)
    app.include_router(notice_router, prefix=prefix)
    app.include_router(notice_admin_router, prefix=prefix)
    app.include_router(exchange_router, prefix=prefix)
    app.include_router(curriculum_router, prefix=prefix)
    app.include_router(report_router, prefix=prefix)
    app.include_router(honor_router, prefix=prefix)
    app.include_router(honor_admin_router, prefix=prefix)
    app.include_router(profile_router, prefix=prefix)
    app.include_router(profile_admin_router, prefix=prefix)
    app.include_router(audit_router, prefix=prefix)

    return app


app = create_app()
