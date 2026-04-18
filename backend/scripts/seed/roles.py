"""角色字典种子（对应 CLAUDE.md 5 级权限模型）。

level 约定：1=SUPER_ADMIN, 2=COLLEGE_LEADER, 3=教师类, 4=学生骨干, 5=普通学生。
新增角色时请同步 `app/core/dependencies.py::require_role` 的调用点，避免未知角色代码被忽略。
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Role
from scripts.seed import SeedResult
from scripts.seed._upsert import upsert_by_code

DOMAIN = "roles"

_ROLES: list[dict] = [
    # L1
    {"code": "SUPER_ADMIN", "name": "超级管理员", "level": 1,
     "description": "全量配置、导入导出、权限管理、审计查看"},
    # L2
    {"code": "COLLEGE_LEADER", "name": "学院领导", "level": 2,
     "description": "关键审批、统计看板查看"},
    # L3 教师类
    {"code": "COUNSELOR", "name": "辅导员", "level": 3,
     "description": "审批、知识维护、通知发布"},
    {"code": "HEAD_TEACHER", "name": "班主任", "level": 3,
     "description": "审批、学业预警协同"},
    {"code": "YOUTH_LEAGUE_TEACHER", "name": "团委老师", "level": 3,
     "description": "团员发展流程维护、通知发布"},
    {"code": "PARTY_BUILD_TEACHER", "name": "党建老师", "level": 3,
     "description": "党员发展流程维护、审批"},
    # L4 学生骨干（不进入审批责任链）
    {"code": "PARTY_BRANCH_SECRETARY", "name": "党支部书记", "level": 4,
     "description": "支部材料汇总与初审"},
    {"code": "YOUTH_LEAGUE_SECRETARY", "name": "团支书", "level": 4,
     "description": "团员材料汇总"},
    {"code": "CLASS_MONITOR", "name": "班长", "level": 4,
     "description": "班级通知协同与汇总"},
    # L5 学生
    {"code": "STUDENT", "name": "学生", "level": 5,
     "description": "查询、申请、查看本人状态、接收通知"},
]


async def seed(db: AsyncSession) -> SeedResult:
    outcome = await upsert_by_code(
        db, Role, _ROLES,
        update_fields=("name", "level", "description"),
    )
    return SeedResult(
        domain=DOMAIN,
        inserted=outcome.inserted,
        updated=outcome.updated,
        skipped=outcome.skipped,
    )
