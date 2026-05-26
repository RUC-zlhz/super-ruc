"""敏感字段写入与脱敏 helper。

所有身份证号、手机号入库前都应通过本模块生成 *_enc 字段；日志、导入行
和 API 预览只保留掩码或字段名，避免明文扩散。
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.core.security import encrypt_field, mask_id_card, mask_phone

_ID_CARD_KEYS = {
    "id_card",
    "id_card_no",
    "identity_card",
    "identity_no",
    "id_number",
    "cert_no",
}
_PHONE_KEYS = {
    "phone",
    "phone_no",
    "mobile",
    "mobile_no",
    "tel",
    "telephone",
    "contact",
    "contact_info",
}
_SENSITIVE_SUFFIXES = ("_enc",)


def normalize_sensitive_plain(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def encrypted_student_sensitive_fields(payload: Mapping[str, Any]) -> dict[str, str | None]:
    """从明文入参生成学生主档可写入的加密字段。"""
    result: dict[str, str | None] = {}
    if "id_card" in payload:
        result["id_card_enc"] = encrypt_field(normalize_sensitive_plain(payload.get("id_card")))
    if "phone" in payload:
        result["phone_enc"] = encrypt_field(normalize_sensitive_plain(payload.get("phone")))
    return result


def protect_student_import_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """学生导入行落库前移除明文字段，并保留加密值与掩码。"""
    protected = dict(record)
    sensitive = encrypted_student_sensitive_fields(protected)

    id_card = normalize_sensitive_plain(protected.pop("id_card", None))
    phone = normalize_sensitive_plain(protected.pop("phone", None))
    if id_card is not None:
        protected["id_card_masked"] = mask_id_card(id_card)
    if phone is not None:
        protected["phone_masked"] = mask_phone(phone)
    protected.update(sensitive)
    return protected


def _sensitive_key_kind(key: str) -> str | None:
    normalized = key.strip().lower()
    if normalized.endswith(_SENSITIVE_SUFFIXES):
        return "encrypted"
    if normalized in _ID_CARD_KEYS or "id_card" in normalized or "identity" in normalized:
        return "id_card"
    if normalized in _PHONE_KEYS or "phone" in normalized or "mobile" in normalized:
        return "phone"
    if normalized.startswith("contact"):
        return "phone"
    return None


def mask_sensitive_value(key: str, value: Any) -> Any:
    kind = _sensitive_key_kind(key)
    if kind is None:
        return value
    if value in (None, ""):
        return value
    if kind == "id_card":
        return mask_id_card(str(value))
    if kind == "phone":
        return mask_phone(str(value))
    return "***encrypted***"


def sanitize_sensitive_data(value: Any, *, parent_key: str | None = None) -> Any:
    """递归脱敏 dict/list 中的敏感键。"""
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _sensitive_key_kind(key_text) is not None:
                sanitized[key_text] = mask_sensitive_value(key_text, item)
            else:
                sanitized[key_text] = sanitize_sensitive_data(item, parent_key=key_text)
        return sanitized
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [sanitize_sensitive_data(item, parent_key=parent_key) for item in value]
    if parent_key and _sensitive_key_kind(parent_key) is not None:
        return mask_sensitive_value(parent_key, value)
    return value
