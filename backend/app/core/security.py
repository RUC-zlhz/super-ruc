"""安全工具：JWT 签发/校验、密码哈希、字段加解密（敏感字段 Fernet AES）。"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

try:
    import bcrypt as _bcrypt_module
except ImportError:  # pragma: no cover - bcrypt is expected in normal runtime
    _bcrypt_module = None
else:
    _original_hashpw = _bcrypt_module.hashpw

    if not getattr(_original_hashpw, "__codex_truncate_72__", False):

        def _compat_hashpw(secret: bytes, salt: bytes, *args: Any, **kwargs: Any):
            if isinstance(secret, (bytes, bytearray, memoryview)) and len(secret) > 72:
                secret = bytes(secret[:72])
            return _original_hashpw(secret, salt, *args, **kwargs)

        _compat_hashpw.__codex_truncate_72__ = True  # type: ignore[attr-defined]
        _bcrypt_module.hashpw = _compat_hashpw

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
_fernet = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())

TokenType = Literal["access", "refresh"]


# ---------- 密码 ----------
def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


# ---------- JWT ----------
def create_token(
    subject: str,
    token_type: TokenType = "access",
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(UTC)
    if expires_delta is None:
        expires_delta = (
            timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            if token_type == "access"
            else timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "typ": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """解码并校验 JWT。失败抛出 JWTError。"""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def safe_decode_token(token: str) -> dict[str, Any] | None:
    try:
        return decode_token(token)
    except JWTError:
        return None


# ---------- 敏感字段加解密（Fernet = AES-128-CBC + HMAC） ----------
def encrypt_field(plain: str | None) -> str | None:
    if plain is None or plain == "":
        return None
    return _fernet.encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_field(cipher: str | None) -> str | None:
    if cipher is None or cipher == "":
        return None
    try:
        return _fernet.decrypt(cipher.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None


# ---------- 脱敏 ----------
def mask_id_card(raw: str | None) -> str | None:
    if not raw or len(raw) < 8:
        return raw
    return raw[:4] + "*" * (len(raw) - 8) + raw[-4:]


def mask_phone(raw: str | None) -> str | None:
    if not raw or len(raw) < 7:
        return raw
    return raw[:3] + "****" + raw[-4:]
