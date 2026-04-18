"""常见事务申请类型种子（FR-006 / FR-008）。

- `form_schema` 约定：采用 JSON Schema 子集，对象内每个字段必须包含 `type` 与 `title`，
  可选 `required`、`description`、`enum`（下拉）、`format=date`（日期）、`widget=textarea`。
- `approver_roles` 为逗号分隔角色列表；审批工作台按 JWT 角色匹配过滤待办。
- `withdraw_hours_limit = None` 表示终审前均可撤回（FR-008）。
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.workflow.models import RequestType
from scripts.seed import SeedResult
from scripts.seed._upsert import upsert_by_code

DOMAIN = "request_types"

_REQUEST_TYPES: list[dict] = [
    {
        "code": "LEAVE_PERSONAL",
        "name": "个人请假",
        "category": "LEAVE",
        "description": "因个人事务请假（病假/事假）。",
        "form_schema": {
            "type": "object",
            "required": ["reason", "start_date", "end_date"],
            "properties": {
                "reason": {"type": "string", "title": "请假事由", "widget": "textarea"},
                "start_date": {"type": "string", "title": "起始日期", "format": "date"},
                "end_date": {"type": "string", "title": "结束日期", "format": "date"},
                "leave_type": {
                    "type": "string", "title": "请假类型",
                    "enum": ["病假", "事假", "其他"],
                },
                "contact": {"type": "string", "title": "在外联系方式"},
            },
        },
        "attachment_required": False,
        "allow_withdraw": True,
        "withdraw_hours_limit": None,
        "approver_roles": "COUNSELOR,HEAD_TEACHER",
    },
    {
        "code": "CERTIFICATE_IN_SCHOOL",
        "name": "在读证明",
        "category": "CERTIFICATE",
        "description": "开具在读证明，线上审批通过后生成 PDF。",
        "form_schema": {
            "type": "object",
            "required": ["purpose"],
            "properties": {
                "purpose": {"type": "string", "title": "用途说明", "widget": "textarea"},
                "deliver_to": {"type": "string", "title": "递交单位（可选）"},
            },
        },
        "attachment_required": False,
        "allow_withdraw": True,
        "withdraw_hours_limit": 72,
        "approver_roles": "COUNSELOR",
    },
    {
        "code": "STAMP_OFFICIAL",
        "name": "学院公章盖章",
        "category": "STAMP",
        "description": "学院公章盖章申请。涉密/敏感文件由审批老师标记转线下办理。",
        "form_schema": {
            "type": "object",
            "required": ["purpose"],
            "properties": {
                "purpose": {"type": "string", "title": "盖章用途", "widget": "textarea"},
                "file_name": {"type": "string", "title": "待盖章文件说明"},
            },
        },
        "attachment_required": True,
        "allow_withdraw": True,
        "withdraw_hours_limit": 24,
        "approver_roles": "COUNSELOR,COLLEGE_LEADER",
    },
    {
        "code": "MATERIAL_PARTY_APPLICATION",
        "name": "入党申请材料提交",
        "category": "MATERIAL",
        "description": "提交入党申请书/自传/思想汇报等材料。",
        "form_schema": {
            "type": "object",
            "required": ["material_type"],
            "properties": {
                "material_type": {
                    "type": "string", "title": "材料类型",
                    "enum": ["入党申请书", "自传", "思想汇报", "谈话记录", "其他"],
                },
                "note": {"type": "string", "title": "备注", "widget": "textarea"},
            },
        },
        "attachment_required": True,
        "allow_withdraw": True,
        "withdraw_hours_limit": 48,
        "approver_roles": "PARTY_BUILD_TEACHER,COUNSELOR",
    },
    {
        "code": "REGISTRATION_EVENT",
        "name": "活动/会议报名",
        "category": "REGISTRATION",
        "description": "面向本学院的线上活动报名。",
        "form_schema": {
            "type": "object",
            "required": ["event_name"],
            "properties": {
                "event_name": {"type": "string", "title": "活动名称"},
                "remark": {"type": "string", "title": "备注（饮食禁忌等）"},
            },
        },
        "attachment_required": False,
        "allow_withdraw": True,
        "withdraw_hours_limit": None,
        "approver_roles": "COUNSELOR,YOUTH_LEAGUE_TEACHER",
    },
]


async def seed(db: AsyncSession) -> SeedResult:
    outcome = await upsert_by_code(
        db, RequestType, _REQUEST_TYPES,
        update_fields=(
            "name", "category", "description", "form_schema",
            "attachment_required", "allow_withdraw", "withdraw_hours_limit",
            "approver_roles",
        ),
    )
    return SeedResult(
        domain=DOMAIN,
        inserted=outcome.inserted,
        updated=outcome.updated,
        skipped=outcome.skipped,
    )
