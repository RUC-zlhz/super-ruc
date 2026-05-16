"""S12 进度中心服务。"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.progress.schemas import ProgressItemOut, ProgressMyResult
from app.workflow.models import Request, StudentWorkflow

_REQUEST_STATUS_LABELS = {
    "DRAFT": "草稿",
    "SUBMITTED": "待受理",
    "IN_REVIEW": "审核中",
    "APPROVED": "已通过",
    "REJECTED": "已驳回",
    "WITHDRAWN": "已撤回",
    "OFFLINE_HANDLED": "转线下",
}

_WORKFLOW_STATUS_LABELS = {
    "ACTIVE": "进行中",
    "COMPLETED": "已完成",
    "SUSPENDED": "已暂停",
}


def _request_status_label(status: str) -> str:
    return _REQUEST_STATUS_LABELS.get(status, status)


def _workflow_status_label(status: str) -> str:
    return _WORKFLOW_STATUS_LABELS.get(status, status)


async def build_my_progress(
    db: AsyncSession,
    *,
    user_id: int,
    student_id: int,
) -> ProgressMyResult:
    request_rows = (
        await db.execute(
            select(Request)
            .where(Request.applicant_user_id == user_id)
            .order_by(Request.updated_at.desc(), Request.id.desc())
            .limit(50)
        )
    ).scalars().all()
    workflow_rows = (
        await db.execute(
            select(StudentWorkflow)
            .where(StudentWorkflow.student_id == student_id)
            .order_by(StudentWorkflow.updated_at.desc(), StudentWorkflow.id.desc())
            .limit(50)
        )
    ).scalars().unique().all()

    items: list[ProgressItemOut] = []
    for row in request_rows:
        items.append(
            ProgressItemOut(
                id=f"REQUEST-{row.id}",
                source_type="REQUEST",
                source_id=row.id,
                title=row.title,
                category=row.type_code,
                status=row.status,
                status_label=_request_status_label(row.status),
                current_step=row.decision_comment,
                updated_at=row.updated_at,
                detail_url=f"/pages/request/detail?id={row.id}",
            )
        )
    for row in workflow_rows:
        current_node_name = None
        due_date = None
        for state in row.node_states or []:
            if state.node_id == row.current_node_id:
                current_node_name = state.node.name if state.node else None
                due_date = state.due_date
                break
        items.append(
            ProgressItemOut(
                id=f"WORKFLOW-{row.id}",
                source_type="WORKFLOW",
                source_id=row.id,
                title=row.template.name if row.template else f"流程 {row.id}",
                category=row.template.kind if row.template else None,
                status=row.status,
                status_label=_workflow_status_label(row.status),
                current_step=current_node_name,
                due_date=due_date,
                updated_at=row.updated_at,
                detail_url=f"/pages/workflow/detail?id={row.id}",
            )
        )
    items.sort(key=lambda item: item.updated_at, reverse=True)
    return ProgressMyResult(items=items[:80], generated_at=datetime.now(UTC))
