"""auth 模块 Pydantic 请求/响应 schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class WxLoginRequest(BaseModel):
    code: str = Field(..., description="微信 wx.login 返回的 code")
    # 首次登录可选：传入学号完成绑定
    student_no: str | None = Field(default=None, description="首次登录时绑定学号")


class WorkNoLoginRequest(BaseModel):
    work_no: str = Field(..., min_length=2, max_length=32)
    password: str = Field(..., min_length=4, max_length=128)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=4, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserInfo


class RoleInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    scope_code: str | None = None


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    avatar_url: str | None = None
    email: EmailStr | None = None
    work_no: str | None = None
    student_no: str | None = None
    student_id: int | None = None
    roles: list[RoleInfo] = []
    must_change_password: bool = False


class BindStudentRequest(BaseModel):
    student_no: str
    # 可选二次核验因子（身份证后 6 位、姓名等），service 层据此加强绑定校验
    full_name: str | None = None
    id_card_tail: str | None = Field(default=None, min_length=4, max_length=6)


class StudentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_no: str
    full_name: str
    grade_code: str | None
    major_code: str | None
    class_code: str | None
    political_status: str | None
    enrollment_status: str | None = None
    created_at: datetime


class EnrollmentStatusUpdate(BaseModel):
    """管理员更新学生学籍生命周期状态（v1.5）。"""

    status: str = Field(
        ..., description="ACTIVE/SUSPENDED/TRANSFERRED/GRADUATED/ARCHIVED"
    )
    reason: str | None = Field(default=None, max_length=256)


TokenResponse.model_rebuild()
