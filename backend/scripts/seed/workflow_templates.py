"""党团流程模板种子（FR-004 / FR-005）。

- 每个模板的 `nodes` 在同一事务中落地；节点按 `sort_order` 顺序排列。
- `trigger_rule = "PREV_DONE"` 表示前一节点完成即自动进入当前节点。
- `due_rule_days` / `reminder_lead_days` 为业务默认值，负责老师可在管理端按实际进度调整。
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.workflow.models import WorkflowNode, WorkflowTemplate
from scripts.seed import SeedResult

DOMAIN = "workflow_templates"


@dataclass(frozen=True, slots=True)
class _NodeSpec:
    code: str
    name: str
    sort_order: int
    stage_group: str | None = None
    required_task: str | None = None
    trigger_rule: str = "PREV_DONE"
    due_rule_days: int | None = None
    reminder_lead_days: int | None = None
    is_terminal: bool = False


@dataclass(frozen=True, slots=True)
class _TemplateSpec:
    code: str
    name: str
    kind: str
    description: str
    version_label: str
    nodes: tuple[_NodeSpec, ...]


_PARTY_DEVELOPMENT = _TemplateSpec(
    code="PARTY_DEVELOPMENT_V1",
    name="党员发展完整流程",
    kind="PARTY",
    description="从递交入党申请书至预备党员转正的完整流程，覆盖积极分子-发展对象-预备党员三阶段。",
    version_label="v1",
    nodes=(
        _NodeSpec("APPLY_SUBMIT", "递交入党申请书", 10,
                 stage_group="APPLICANT",
                 required_task="提交入党申请书并完成初次谈话",
                 trigger_rule="MANUAL"),
        _NodeSpec("ACTIVIST_RECOMMEND", "团推优/支部推荐为积极分子", 20,
                 stage_group="ACTIVIST", due_rule_days=90, reminder_lead_days=14),
        _NodeSpec("ACTIVIST_CERT", "积极分子备案", 30,
                 stage_group="ACTIVIST", due_rule_days=30, reminder_lead_days=7),
        _NodeSpec("PARTY_SCHOOL", "党校培训结业", 40,
                 stage_group="ACTIVIST",
                 required_task="完成党校学习并取得结业证",
                 due_rule_days=180, reminder_lead_days=30),
        _NodeSpec("DEVELOP_CANDIDATE", "确定为发展对象", 50,
                 stage_group="CANDIDATE", due_rule_days=365, reminder_lead_days=30),
        _NodeSpec("POLITICAL_REVIEW", "政审与谈话", 60,
                 stage_group="CANDIDATE",
                 required_task="完成政审材料与组织谈话",
                 due_rule_days=60, reminder_lead_days=14),
        _NodeSpec("PROBATION_APPROVAL", "预备党员接收", 70,
                 stage_group="PROBATION", due_rule_days=30, reminder_lead_days=7),
        _NodeSpec("PROBATION_EDUCATION", "预备期教育与考察", 80,
                 stage_group="PROBATION", due_rule_days=365, reminder_lead_days=30),
        _NodeSpec("FULL_MEMBER", "转正", 100,
                 stage_group="FULL_MEMBER", is_terminal=True),
    ),
)

_YOUTH_LEAGUE = _TemplateSpec(
    code="YOUTH_LEAGUE_V1",
    name="团员发展与团籍管理",
    kind="YOUTH_LEAGUE",
    description="团员入团申请-批准-注册-推优全流程。",
    version_label="v1",
    nodes=(
        _NodeSpec("LEAGUE_APPLY", "递交入团申请", 10,
                 stage_group="APPLICANT", trigger_rule="MANUAL"),
        _NodeSpec("LEAGUE_LECTURE", "团课学习", 20,
                 stage_group="APPLICANT",
                 required_task="完成团课学习并获得结业",
                 due_rule_days=60, reminder_lead_days=14),
        _NodeSpec("LEAGUE_APPROVE", "支部大会通过", 30,
                 stage_group="MEMBER", due_rule_days=30, reminder_lead_days=7),
        _NodeSpec("LEAGUE_REGISTER", "团籍注册", 40,
                 stage_group="MEMBER", due_rule_days=30, reminder_lead_days=7),
        _NodeSpec("LEAGUE_RECOMMEND_PARTY", "推优入党", 80,
                 stage_group="MEMBER"),
        _NodeSpec("LEAGUE_GRADUATE_TRANSFER", "毕业团员转出", 100,
                 stage_group="MEMBER", is_terminal=True),
    ),
)

_TEMPLATES: tuple[_TemplateSpec, ...] = (_PARTY_DEVELOPMENT, _YOUTH_LEAGUE)


async def _upsert_template(db: AsyncSession, spec: _TemplateSpec) -> tuple[str, WorkflowTemplate]:
    existing = (
        await db.execute(
            select(WorkflowTemplate).where(WorkflowTemplate.code == spec.code)
        )
    ).scalar_one_or_none()

    if existing is None:
        tpl = WorkflowTemplate(
            code=spec.code, name=spec.name, kind=spec.kind,
            description=spec.description, version_label=spec.version_label,
            is_active=True,
        )
        db.add(tpl)
        await db.flush()
        return "insert", tpl

    changed = False
    for field, new_value in (
        ("name", spec.name),
        ("kind", spec.kind),
        ("description", spec.description),
        ("version_label", spec.version_label),
    ):
        if getattr(existing, field) != new_value:
            setattr(existing, field, new_value)
            changed = True
    return ("update" if changed else "skip"), existing


async def _sync_nodes(
    db: AsyncSession, tpl: WorkflowTemplate, specs: tuple[_NodeSpec, ...]
) -> None:
    """确保模板节点集合与 spec 一致：缺失的节点新增；已有节点按 spec 更新。

    为避免破坏已有流程实例，这里不删除多余节点——若需下线旧节点，应通过数据库迁移完成。
    """
    existing_rows = (
        await db.execute(
            select(WorkflowNode).where(WorkflowNode.template_id == tpl.id)
        )
    ).scalars().all()
    existing_by_code = {row.code: row for row in existing_rows}

    for spec in specs:
        row = existing_by_code.get(spec.code)
        if row is None:
            db.add(WorkflowNode(
                template_id=tpl.id,
                code=spec.code,
                name=spec.name,
                sort_order=spec.sort_order,
                stage_group=spec.stage_group,
                required_task=spec.required_task,
                trigger_rule=spec.trigger_rule,
                due_rule_days=spec.due_rule_days,
                reminder_lead_days=spec.reminder_lead_days,
                is_terminal=spec.is_terminal,
                is_active=True,
            ))
            continue
        for field, new_value in (
            ("name", spec.name),
            ("sort_order", spec.sort_order),
            ("stage_group", spec.stage_group),
            ("required_task", spec.required_task),
            ("trigger_rule", spec.trigger_rule),
            ("due_rule_days", spec.due_rule_days),
            ("reminder_lead_days", spec.reminder_lead_days),
            ("is_terminal", spec.is_terminal),
        ):
            if getattr(row, field) != new_value:
                setattr(row, field, new_value)
    await db.flush()


async def seed(db: AsyncSession) -> SeedResult:
    inserted = updated = skipped = 0
    for spec in _TEMPLATES:
        action, tpl = await _upsert_template(db, spec)
        if action == "insert":
            inserted += 1
        elif action == "update":
            updated += 1
        else:
            skipped += 1
        await _sync_nodes(db, tpl, spec.nodes)
    return SeedResult(
        domain=DOMAIN, inserted=inserted, updated=updated, skipped=skipped
    )
