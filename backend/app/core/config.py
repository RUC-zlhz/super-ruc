"""全局配置：基于 pydantic-settings，从 .env 加载。"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 开发默认值；生产环境必须替换为强随机值，否则 Settings 在启动时报错
# Fernet 开发密钥由 cryptography.fernet.Fernet.generate_key() 生成，
# 仅用于本机/CI；任何环境（包括 staging）都应覆写为新生成的密钥。
_DEV_JWT_SECRET = "change-me-in-production-please-use-random-32bytes"
_DEV_FERNET_KEY = "2tTqAlzPdUU2GzGD6BCXq5q8SWHLqULfGjzktKh9jrw="


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_ENV: Literal["dev", "test", "staging", "prod"] = "dev"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://sip_user:sip_pass_dev@localhost:54322/sip_db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    REDIS_URL: str = "redis://:sip_redis_dev@localhost:6379/0"

    MINIO_ENDPOINT: str = "localhost:9010"
    MINIO_ACCESS_KEY: str = "sip_minio"
    MINIO_SECRET_KEY: str = "sip_minio_dev"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_ATTACHMENT: str = "sip-attachments"
    MINIO_BUCKET_TEMPLATE: str = "sip-templates"
    MINIO_BUCKET_EXPORT: str = "sip-exports"

    JWT_SECRET_KEY: str = _DEV_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    FIELD_ENCRYPTION_KEY: str = Field(
        default=_DEV_FERNET_KEY,
        description="Fernet key (base64, 32 bytes)；cryptography.fernet.Fernet.generate_key() 生成",
    )

    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""
    WECHAT_MOCK_ENABLED: bool = True

    AI_QA_ENABLED: bool = False
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-haiku-4-5"

    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@sip.example.edu"

    SMS_ENABLED: bool = False
    SMS_PROVIDER: str = ""
    SMS_ACCESS_KEY: str = ""
    SMS_SECRET_KEY: str = ""
    SMS_SIGN: str = ""

    UPLOAD_MAX_SIZE_MB: int = 30

    @property
    def UPLOAD_MAX_SIZE_BYTES(self) -> int:
        return self.UPLOAD_MAX_SIZE_MB * 1024 * 1024

    @property
    def IS_DEV(self) -> bool:
        return self.APP_ENV == "dev"

    @property
    def IS_PROD(self) -> bool:
        return self.APP_ENV == "prod"

    # ------------------------------------------------------------------
    # 生产守卫：确保部署环境不会带着 dev 默认值 / 空密钥上线。
    # ------------------------------------------------------------------
    @model_validator(mode="after")
    def _enforce_prod_invariants(self) -> "Settings":
        errors: list[str] = []

        # 关键密钥：dev/prod 都至少要有，prod 禁止使用 dev 默认值
        if not self.JWT_SECRET_KEY:
            errors.append("JWT_SECRET_KEY 不能为空")
        if not self.FIELD_ENCRYPTION_KEY:
            errors.append("FIELD_ENCRYPTION_KEY 不能为空")

        if self.IS_PROD:
            if self.APP_DEBUG:
                errors.append("APP_DEBUG 在 prod 下必须为 False")
            if self.JWT_SECRET_KEY == _DEV_JWT_SECRET:
                errors.append("JWT_SECRET_KEY 仍为开发默认值，必须在生产环境替换")
            if self.FIELD_ENCRYPTION_KEY == _DEV_FERNET_KEY:
                errors.append("FIELD_ENCRYPTION_KEY 仍为开发默认值，必须在生产环境替换")
            if not self.WECHAT_MOCK_ENABLED:
                if not self.WECHAT_APPID or not self.WECHAT_SECRET:
                    errors.append(
                        "生产环境启用真实微信登录时必须配置 WECHAT_APPID / WECHAT_SECRET"
                    )

        # 非生产也生效的功能开关守卫
        if self.AI_QA_ENABLED and not self.ANTHROPIC_API_KEY:
            errors.append("AI_QA_ENABLED=True 时必须配置 ANTHROPIC_API_KEY")
        if self.SMS_ENABLED and not (
            self.SMS_PROVIDER and self.SMS_ACCESS_KEY and self.SMS_SECRET_KEY
        ):
            errors.append(
                "SMS_ENABLED=True 时必须配置 SMS_PROVIDER / SMS_ACCESS_KEY / SMS_SECRET_KEY"
            )

        if errors:
            raise ValueError(
                "配置校验失败：\n  - " + "\n  - ".join(errors)
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
