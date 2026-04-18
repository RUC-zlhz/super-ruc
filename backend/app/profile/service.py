"""profile 服务层 — FR-018 学生画像。

责任边界（C-04 + FR-018 原文约束）：
- 不输出综合素质评分或排名结论
- 敏感字段（is_sensitive）对学生端隐藏
- 学生端访问仅限本人
- 辅导员/班主任按权限访问
- 所有访问留痕（log_action）
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_action
from app.core.exceptions import BizError, NotFoundError
from app.profile import repository as repo
from app.profile.models import (
    PROFILE_APPROVAL_APPROVED,
    PROFILE_APPROVAL_PENDING,
    PROFILE_APPROVAL_REJECTED,
    PROFILE_FACT_COMPETITION,
    PROFILE_FACT_LEADERSHIP,
    PROFILE_FACT_PRACTICE,
    PROFILE_FACT_RESEARCH,
    PROFILE_FACT_VOLUNTEER,
    PROFILE_SOURCE_STUDENT_SELF,
    ProfileCorrection,
    ProfileFact,
)
from app.profile.schemas import (
    ProfileFactOut,
    ProfileFactStudentView,
    ProfileStudentSelfView,
    ProfileSummary,
    StudentBasic,
)


def _summary_counters(counts: dict[str, float]) -> dict[str, Any]:
    return {
        "research_count": int(counts.get(PROFILE_FACT_RESEARCH, 0)),
        "competition_count": int(counts.get(PROFILE_FACT_COMPETITION, 0)),
        "practice_count": int(counts.get(PROFILE_FACT_PRACTICE, 0)),
        "volunteer_hours": float(counts.get("VOLUNTEER_HOURS", 0)),
        "leadership_count": int(counts.get(PROFILE_FACT_LEADERSHIP, 0)),
    }


async def build_summary_admin(
    db: AsyncSession, student_id: int,
    *, viewer_user_id: int, viewer_role: str | None,
) -> ProfileSummary:
    student = await repo.get_student(db, student_id)
    if student is None:
        raise NotFoundError("学生不存在")
    facts = await repo.list_facts(db, student_id, only_approved=True)
    counts = await repo.count_by_type(db, student_id)
    summary = ProfileSummary(
        student=StudentBasic.model_validate(student),
        facts=[ProfileFactOut.model_validate(f) for f in facts],
        generated_at=datetime.now(timezone.utc),
        **_summary_counters(counts),
    )
    await log_action(
        db, event_type="PROFILE", entity_code="STUDENT_PROFILE",
        action="READ_ADMIN", entity_id=student_id,
        actor_user_id=viewer_user_id, actor_role=viewer_role,
    )
    await db.commit()
    return summary


async def build_summary_self(
    db: AsyncSession, student_id: int, *, viewer_user_id: int, viewer_role: str | None,
) -> ProfileStudentSelfView:
    student = await repo.get_student(db, student_id)
    if student is None:
        raise NotFoundError("学生不存在")
    facts = await repo.list_facts(db, student_id, only_approved=True)
    visible = [f for f in facts if not f.is_sensitive]
    counts = await repo.count_by_type(db, student_id)
    out = ProfileStudentSelfView(
        student=StudentBasic.model_validate(student),
        facts=[ProfileFactStudentView.model_validate(f) for f in visible],
        generated_at=datetime.now(timezone.utc),
        **_summary_counters(counts),
    )
    await log_action(
        db, event_type="PROFILE", entity_code="STUDENT_PROFILE",
        action="READ_SELF", entity_id=student_id,
        actor_user_id=viewer_user_id, actor_role=viewer_role,
    )
    await db.commit()
    return out


async def create_fact(
    db: AsyncSession,
    student_id: int,
    payload: dict[str, Any],
    *, operator_id: int, operator_role: str | None,
) -> ProfileFact:
    payload = dict(payload)
    payload["student_id"] = student_id
    payload["created_by"] = operator_id
    payload["updated_by"] = operator_id
    # 非学生自录默认 APPROVED
    if payload.get("source") == PROFILE_SOURCE_STUDENT_SELF:
        payload["approval_status"] = PROFILE_APPROVAL_PENDING
    else:
        payload["approval_status"] = PROFILE_APPROVAL_APPROVED
        payload["approved_by"] = operator_id
        payload["approved_at"] = datetime.now(timezone.utc)
    row = await repo.create_fact(db, payload)
    await log_action(
        db, event_type="PROFILE", entity_code="PROFILE_FACT",
        action="CREATE", entity_id=row.id,
        actor_user_id=operator_id, actor_role=operator_role,
        detail={"student_id": student_id, "fact_type": row.fact_type},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def update_fact(
    db: AsyncSession, fact_id: int, payload: dict[str, Any],
    *, operator_id: int, operator_role: str | None,
) -> ProfileFact:
    row = await repo.get_fact(db, fact_id)
    if row is None:
        raise NotFoundError("画像条目不存在")
    for k, v in payload.items():
        if k in ("student_id", "created_by", "approved_by", "approved_at"):
            continue
        setattr(row, k, v)
    row.updated_by = operator_id
    await log_action(
        db, event_type="PROFILE", entity_code="PROFILE_FACT",
        action="UPDATE", entity_id=row.id,
        actor_user_id=operator_id, actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_fact(
    db: AsyncSession, fact_id: int, *, operator_id: int, operator_role: str | None
) -> None:
    row = await repo.get_fact(db, fact_id)
    if row is None:
        raise NotFoundError("画像条目不存在")
    student_id = row.student_id
    await repo.delete_fact(db, row)
    await log_action(
        db, event_type="PROFILE", entity_code="PROFILE_FACT",
        action="DELETE", entity_id=fact_id,
        actor_user_id=operator_id, actor_role=operator_role,
        detail={"student_id": student_id},
    )
    await db.commit()


# ---- 纠错申诉 ----
async def submit_correction(
    db: AsyncSession,
    student_id: int,
    payload: dict[str, Any],
    *, viewer_user_id: int,
) -> ProfileCorrection:
    data = dict(payload)
    data["student_id"] = student_id
    # 如果关联 fact，抓取当前值作为 current_value 快照
    if data.get("fact_id"):
        fact = await repo.get_fact(db, data["fact_id"])
        if fact is None:
            raise NotFoundError("所引用的画像条目不存在")
        if fact.student_id != student_id:
            raise BizError("不允许修改他人画像", code=40180)
        data["current_value"] = str(getattr(fact, data["field_name"], "") or "")
    row = await repo.create_correction(db, data)
    await log_action(
        db, event_type="PROFILE", entity_code="PROFILE_CORRECTION",
        action="SUBMIT", entity_id=row.id,
        actor_user_id=viewer_user_id,
        detail={"student_id": student_id, "field": data["field_name"]},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def decide_correction(
    db: AsyncSession, correction_id: int,
    *, decision: str, comment: str | None, apply_to_fact: bool,
    operator_id: int, operator_role: str | None,
) -> ProfileCorrection:
    if decision not in (PROFILE_APPROVAL_APPROVED, PROFILE_APPROVAL_REJECTED):
        raise BizError(f"无效的处理结果 {decision}", code=40181)
    row = await repo.get_correction(db, correction_id)
    if row is None:
        raise NotFoundError("申诉记录不存在")
    if row.status != PROFILE_APPROVAL_PENDING:
        raise BizError("该申诉已处理", code=40182)

    row.status = decision
    row.handled_by = operator_id
    row.handled_at = datetime.now(timezone.utc)
    row.handler_comment = comment

    if decision == PROFILE_APPROVAL_APPROVED and apply_to_fact and row.fact_id:
        fact = await repo.get_fact(db, row.fact_id)
        if fact is not None and hasattr(fact, row.field_name):
            setattr(fact, row.field_name, row.proposed_value)
            fact.updated_by = operator_id

    await log_action(
        db, event_type="PROFILE", entity_code="PROFILE_CORRECTION",
        action="DECIDE", entity_id=row.id,
        actor_user_id=operator_id, actor_role=operator_role,
        detail={"decision": decision, "apply": apply_to_fact},
    )
    await db.commit()
    await db.refresh(row)
    return row
