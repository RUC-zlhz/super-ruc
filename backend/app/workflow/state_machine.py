"""申请状态机 + 节点状态机。

把散落在 service.py 里的"当前状态 X 是否可以做动作 Y"判断统一到这里，
方便单元测试，以及后续扩展（例如审计回溯合法迁移）。

约束（见 models.py 顶部注释）：

    DRAFT ─submit─▶ SUBMITTED ─claim──▶ IN_REVIEW ─approve─▶ APPROVED
                                              └─reject───▶ REJECTED ─resubmit─▶ SUBMITTED
                   SUBMITTED ─approve/reject──▶ 同上
                   SUBMITTED/IN_REVIEW ─withdraw──▶ WITHDRAWN
                   SUBMITTED/IN_REVIEW ─offline ──▶ OFFLINE_HANDLED
                   APPROVED/OFFLINE_HANDLED/WITHDRAWN ─reopen─▶ IN_REVIEW/SUBMITTED
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import BizError
from app.workflow.models import (
    REQUEST_ACTION_APPROVE,
    REQUEST_ACTION_OFFLINE,
    REQUEST_ACTION_REJECT,
    REQUEST_ACTION_REOPEN,
    REQUEST_ACTION_RESUBMIT,
    REQUEST_ACTION_SUBMIT,
    REQUEST_ACTION_WITHDRAW,
    REQUEST_STATUS_APPROVED,
    REQUEST_STATUS_DRAFT,
    REQUEST_STATUS_IN_REVIEW,
    REQUEST_STATUS_OFFLINE_HANDLED,
    REQUEST_STATUS_REJECTED,
    REQUEST_STATUS_SUBMITTED,
    REQUEST_STATUS_WITHDRAWN,
    WORKFLOW_NODE_DONE,
    WORKFLOW_NODE_OVERDUE,
    WORKFLOW_NODE_PENDING,
)

# =====================================================================
# 申请（Request）状态机
# =====================================================================
# action → (允许的前置状态集合, 目标状态)
_REQUEST_TRANSITIONS: dict[str, tuple[frozenset[str], str]] = {
    REQUEST_ACTION_SUBMIT: (
        frozenset({REQUEST_STATUS_DRAFT}),
        REQUEST_STATUS_SUBMITTED,
    ),
    REQUEST_ACTION_RESUBMIT: (
        frozenset({REQUEST_STATUS_REJECTED}),
        REQUEST_STATUS_SUBMITTED,
    ),
    "CLAIM": (
        frozenset({REQUEST_STATUS_SUBMITTED}),
        REQUEST_STATUS_IN_REVIEW,
    ),
    REQUEST_ACTION_APPROVE: (
        frozenset({REQUEST_STATUS_SUBMITTED, REQUEST_STATUS_IN_REVIEW}),
        REQUEST_STATUS_APPROVED,
    ),
    REQUEST_ACTION_REJECT: (
        frozenset({REQUEST_STATUS_SUBMITTED, REQUEST_STATUS_IN_REVIEW}),
        REQUEST_STATUS_REJECTED,
    ),
    REQUEST_ACTION_WITHDRAW: (
        frozenset({REQUEST_STATUS_SUBMITTED, REQUEST_STATUS_IN_REVIEW}),
        REQUEST_STATUS_WITHDRAWN,
    ),
    REQUEST_ACTION_OFFLINE: (
        frozenset({REQUEST_STATUS_SUBMITTED, REQUEST_STATUS_IN_REVIEW}),
        REQUEST_STATUS_OFFLINE_HANDLED,
    ),
}
_REQUEST_REOPEN_ALLOWED_STATUSES: frozenset[str] = frozenset(
    {
        REQUEST_STATUS_APPROVED,
        REQUEST_STATUS_WITHDRAWN,
        REQUEST_STATUS_OFFLINE_HANDLED,
    }
)
_REQUEST_REOPEN_TARGET_STATUSES: frozenset[str] = frozenset(
    {REQUEST_STATUS_SUBMITTED, REQUEST_STATUS_IN_REVIEW}
)
_REQUEST_TRANSITIONS[REQUEST_ACTION_REOPEN] = (
    _REQUEST_REOPEN_ALLOWED_STATUSES,
    REQUEST_STATUS_IN_REVIEW,
)

# 前端 / 学生可编辑的状态
REQUEST_EDITABLE_STATUSES: frozenset[str] = frozenset(
    {REQUEST_STATUS_DRAFT, REQUEST_STATUS_REJECTED}
)
# 终态（不可再流转）
REQUEST_TERMINAL_STATUSES: frozenset[str] = frozenset(
    {
        REQUEST_STATUS_APPROVED,
        REQUEST_STATUS_WITHDRAWN,
        REQUEST_STATUS_OFFLINE_HANDLED,
    }
)


@dataclass(frozen=True)
class TransitionResult:
    status_before: str
    status_after: str
    action: str


class ApprovalStateMachine:
    """申请状态机。

    用法::

        sm = ApprovalStateMachine()
        result = sm.transition(req.status, REQUEST_ACTION_APPROVE)
        req.status = result.status_after
    """

    @staticmethod
    def can_transition(current_status: str, action: str) -> bool:
        entry = _REQUEST_TRANSITIONS.get(action)
        return entry is not None and current_status in entry[0]

    @staticmethod
    def transition(current_status: str, action: str) -> TransitionResult:
        entry = _REQUEST_TRANSITIONS.get(action)
        if entry is None:
            raise BizError(f"未知的申请动作：{action}", code=40025)
        allowed, target = entry
        if current_status not in allowed:
            raise BizError(
                f"当前状态 {current_status} 不允许执行 {action}（期望之一：{sorted(allowed)}）",
                code=40022,
            )
        return TransitionResult(
            status_before=current_status, status_after=target, action=action
        )

    @staticmethod
    def reopen(current_status: str, target_status: str) -> TransitionResult:
        if current_status not in _REQUEST_REOPEN_ALLOWED_STATUSES:
            raise BizError(
                f"当前状态 {current_status} 不允许执行 {REQUEST_ACTION_REOPEN}"
                f"（期望之一：{sorted(_REQUEST_REOPEN_ALLOWED_STATUSES)}）",
                code=40022,
            )
        if target_status not in _REQUEST_REOPEN_TARGET_STATUSES:
            raise BizError(
                f"重开目标状态不合法：{target_status}"
                f"（期望之一：{sorted(_REQUEST_REOPEN_TARGET_STATUSES)}）",
                code=40026,
            )
        return TransitionResult(
            status_before=current_status,
            status_after=target_status,
            action=REQUEST_ACTION_REOPEN,
        )

    @staticmethod
    def assert_editable(current_status: str) -> None:
        if current_status not in REQUEST_EDITABLE_STATUSES:
            raise BizError(f"当前状态 {current_status} 不可编辑/提交", code=40018)

    @staticmethod
    def is_terminal(current_status: str) -> bool:
        return current_status in REQUEST_TERMINAL_STATUSES


# =====================================================================
# 节点（StudentWorkflowNode）状态机
# =====================================================================
_NODE_MANUAL_STATUSES: frozenset[str] = frozenset(
    {"DEFERRED", "MANUAL_FOLLOW_UP", WORKFLOW_NODE_PENDING, WORKFLOW_NODE_OVERDUE}
)


class NodeStateMachine:
    """党团流程节点状态机（轻量）。完成节点时推进到下一节点的逻辑仍在 service。"""

    @staticmethod
    def assert_completable(current_status: str) -> None:
        if current_status == WORKFLOW_NODE_DONE:
            raise BizError("节点已完成", code=40916)

    @staticmethod
    def assert_manual_status_allowed(new_status: str) -> None:
        if new_status not in _NODE_MANUAL_STATUSES:
            raise BizError(f"状态不合法：{new_status}", code=40014)
