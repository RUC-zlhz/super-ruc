from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    entity_code: str
    entity_id: int | None
    actor_user_id: int | None
    actor_role: str | None
    action: str
    result_code: str
    ip_address: str | None
    message: str | None
    occurred_at: datetime


class RoleFieldPolicyIn(BaseModel):
    role_code: str
    entity_code: str
    field_name: str
    can_read: bool = False
    can_write: bool = False
    mask_strategy: str | None = None


class RoleFieldPolicyOut(RoleFieldPolicyIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
