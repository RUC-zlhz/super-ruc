"""S49 静态回归：敏感明文字段不能绕过统一 helper。"""
from __future__ import annotations

from pathlib import Path


def test_sensitive_plain_fields_are_not_assigned_to_encrypted_columns() -> None:
    app_root = Path(__file__).resolve().parents[1] / "app"
    forbidden_snippets = (
        'id_card_enc=payload.get("id_card")',
        "id_card_enc=payload.get('id_card')",
        '"id_card_enc": payload.get("id_card")',
        "'id_card_enc': payload.get('id_card')",
        'phone_enc=payload.get("phone")',
        "phone_enc=payload.get('phone')",
        '"phone_enc": payload.get("phone")',
        "'phone_enc': payload.get('phone')",
        '"id_card_enc": d.get("id_card")',
        '"phone_enc": d.get("phone")',
    )
    offenders: list[str] = []
    for path in app_root.rglob("*.py"):
        if path.name == "models.py":
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in forbidden_snippets:
            if snippet in text:
                offenders.append(f"{path.relative_to(app_root)} contains {snippet}")
    assert offenders == []
