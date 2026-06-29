"""data_dict 模块 Pydantic schema。"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DataDictOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dict_type: str
    label: str
    value: str
    sort_order: int
    is_active: bool


class DataDictIn(BaseModel):
    dict_type: str = Field(..., min_length=1, max_length=64)
    label: str = Field(..., min_length=1, max_length=128)
    value: str = Field(..., min_length=1, max_length=128)
    sort_order: int = 0
