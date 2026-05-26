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
    reminder_enabled: bool = True
    repeat_interval_days: int | None = None
    max_reminders: int | None = 1
    is_terminal: bool = False


@dataclass(frozen=True, slots=True)
class _TemplateSpec:
    code: str
    name: str
    kind: str
    description: str
    version_label: str
    nodes: tuple[_NodeSpec, ...]
    is_active: bool = True
    sync_nodes_on_update: bool = True


_PARTY_DEVELOPMENT_LEGACY = _TemplateSpec(
    code="PARTY_DEVELOPMENT_V1",
    name="党员发展关键节点简版（历史兼容）",
    kind="PARTY",
    description="历史兼容模板：以关键节点概括党员发展流程，新发起流程请使用官方 29 步模板。",
    version_label="v1",
    is_active=False,
    sync_nodes_on_update=False,
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

_PARTY_DEVELOPMENT_OFFICIAL = _TemplateSpec(
    code="PARTY_DEVELOPMENT_OFFICIAL_V2",
    name="发展党员工作程序（官方29步）",
    kind="PARTY",
    description="依据仓库内《发展党员工作程序》结构化资料建立的 4 阶段 29 步官方对齐模板。",
    version_label="official-v2",
    nodes=(
        _NodeSpec("PARTY_01_EDUCATION_GUIDANCE", "教育引导", 10,
                 stage_group="ACTIVIST_CONFIRMATION", trigger_rule="MANUAL"),
        _NodeSpec("PARTY_02_RECEIVE_APPLICATION_TALK", "接收入党申请书并派人谈话", 20,
                 stage_group="ACTIVIST_CONFIRMATION",
                 required_task="提交入党申请书；后续谈话由党组织安排"),
        _NodeSpec("PARTY_03_CONFIRM_ACTIVIST_FILE", "确定入党积极分子并报党委备案", 30,
                 stage_group="ACTIVIST_CONFIRMATION"),
        _NodeSpec("PARTY_04_ASSIGN_MENTOR_EDUCATION", "指定培养联系人并进行培养教育", 40,
                 stage_group="ACTIVIST_CONFIRMATION"),
        _NodeSpec("PARTY_05_INSPECTION", "考察", 50,
                 stage_group="ACTIVIST_CONFIRMATION",
                 required_task="按支部要求提交思想汇报等培养考察材料"),
        _NodeSpec("PARTY_06_BRANCH_COMMITTEE_DISCUSSION", "支部委员会听取意见后讨论", 60,
                 stage_group="DEVELOPMENT_TARGET"),
        _NodeSpec("PARTY_07_FILE_CONFIRM_TARGET", "报党委备案后确定发展对象", 70,
                 stage_group="DEVELOPMENT_TARGET"),
        _NodeSpec("PARTY_08_CONFIRM_INTRODUCER", "确定入党介绍人", 80,
                 stage_group="DEVELOPMENT_TARGET"),
        _NodeSpec("PARTY_09_POLITICAL_REVIEW", "政治审查", 90,
                 stage_group="DEVELOPMENT_TARGET"),
        _NodeSpec("PARTY_10_SHORT_TRAINING", "短期集中培训", 100,
                 stage_group="DEVELOPMENT_TARGET",
                 required_task="参加短期集中培训并按要求提交结业证明"),
        _NodeSpec("PARTY_11_BRANCH_COMMITTEE_PREVIEW", "支部委员会听取意见后讨论", 110,
                 stage_group="PROBATION_ACCEPTANCE"),
        _NodeSpec("PARTY_12_PRE_REVIEW", "报党委预审", 120,
                 stage_group="PROBATION_ACCEPTANCE"),
        _NodeSpec("PARTY_13_PUBLIC_NOTICE", "公示", 130,
                 stage_group="PROBATION_ACCEPTANCE"),
        _NodeSpec("PARTY_14_BRANCH_MEETING_ACCEPT_PROBATION", "召开支部大会讨论接收预备党员", 140,
                 stage_group="PROBATION_ACCEPTANCE"),
        _NodeSpec("PARTY_15_SUBMIT_MATERIALS_ORG_DEPT", "将有关材料报党委组织部", 150,
                 stage_group="PROBATION_ACCEPTANCE"),
        _NodeSpec("PARTY_16_ORG_DEPT_TALK", "党委组织部派人进行谈话", 160,
                 stage_group="PROBATION_ACCEPTANCE"),
        _NodeSpec("PARTY_17_PARTY_COMMITTEE_APPROVAL", "党委审批", 170,
                 stage_group="PROBATION_ACCEPTANCE"),
        _NodeSpec("PARTY_18_NOTIFY_BRANCH_APPROVAL", "党委审批结果通知党支部", 180,
                 stage_group="PROBATION_ACCEPTANCE"),
        _NodeSpec("PARTY_19_HIGHER_ORG_FILE", "报上级党委组织部备案", 190,
                 stage_group="PROBATION_ACCEPTANCE"),
        _NodeSpec("PARTY_20_ASSIGN_BRANCH_GROUP", "编入党支部和党小组", 200,
                 stage_group="PROBATION_EDUCATION_FULL_MEMBER"),
        _NodeSpec("PARTY_21_OATH", "组织入党宣誓", 210,
                 stage_group="PROBATION_EDUCATION_FULL_MEMBER"),
        _NodeSpec("PARTY_22_CONTINUED_EDUCATION", "继续教育考察", 220,
                 stage_group="PROBATION_EDUCATION_FULL_MEMBER"),
        _NodeSpec("PARTY_23_SUBMIT_FULL_MEMBER_APPLICATION", "递交转正申请书", 230,
                 stage_group="PROBATION_EDUCATION_FULL_MEMBER",
                 required_task="提交转正申请书"),
        _NodeSpec("PARTY_24_FULL_MEMBER_PUBLIC_NOTICE", "公示", 240,
                 stage_group="PROBATION_EDUCATION_FULL_MEMBER"),
        _NodeSpec("PARTY_25_BRANCH_MEETING_FULL_MEMBER", "召开支部大会讨论预备党员转正", 250,
                 stage_group="PROBATION_EDUCATION_FULL_MEMBER"),
        _NodeSpec("PARTY_26_SUBMIT_FULL_MEMBER_MATERIALS", "将有关材料报党委组织部", 260,
                 stage_group="PROBATION_EDUCATION_FULL_MEMBER"),
        _NodeSpec("PARTY_27_FULL_MEMBER_APPROVAL", "党委审批", 270,
                 stage_group="PROBATION_EDUCATION_FULL_MEMBER"),
        _NodeSpec("PARTY_28_NOTIFY_FULL_MEMBER_APPROVAL", "党委审批结果通知党支部", 280,
                 stage_group="PROBATION_EDUCATION_FULL_MEMBER"),
        _NodeSpec("PARTY_29_ARCHIVE", "存档", 290,
                 stage_group="PROBATION_EDUCATION_FULL_MEMBER", is_terminal=True),
    ),
)

_YOUTH_LEAGUE_LEGACY = _TemplateSpec(
    code="YOUTH_LEAGUE_V1",
    name="团员发展与团籍管理简版（历史兼容）",
    kind="YOUTH_LEAGUE",
    description="历史兼容模板：混合了入团发展、推优入党与毕业转出，新发起入团发展请使用官方 15 步模板。",
    version_label="v1",
    is_active=False,
    sync_nodes_on_update=False,
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

_YOUTH_LEAGUE_DEVELOPMENT_OFFICIAL = _TemplateSpec(
    code="YOUTH_LEAGUE_DEVELOPMENT_OFFICIAL_V2",
    name="发展团员工作流程（官方15步）",
    kind="YOUTH_LEAGUE",
    description="依据仓库内《五个阶段15个步骤》发展团员资料建立的 5 阶段 15 步官方对齐模板。",
    version_label="official-v2",
    nodes=(
        _NodeSpec("YOUTH_01_SUBMIT_APPLICATION", "提交入团申请书", 10,
                 stage_group="APPLY", required_task="提交入团申请书",
                 trigger_rule="MANUAL"),
        _NodeSpec("YOUTH_02_TALK", "派人谈话", 20,
                 stage_group="APPLY", due_rule_days=30, reminder_lead_days=7),
        _NodeSpec("YOUTH_03_APPROVE_ACTIVIST", "确定和批准入团积极分子", 30,
                 stage_group="ACTIVIST_CONFIRMATION"),
        _NodeSpec("YOUTH_04_ASSIGN_MENTOR", "指定培养联系人", 40,
                 stage_group="ACTIVIST_CONFIRMATION"),
        _NodeSpec("YOUTH_05_EDUCATION_INSPECTION", "入团积极分子的教育、培养和考察", 50,
                 stage_group="ACTIVIST_EDUCATION", due_rule_days=90, reminder_lead_days=14),
        _NodeSpec("YOUTH_06_RECOMMEND_TARGET", "推荐发展对象", 60,
                 stage_group="DEVELOPMENT_TARGET"),
        _NodeSpec("YOUTH_07_PRE_REVIEW_TARGET", "预审发展对象", 70,
                 stage_group="DEVELOPMENT_TARGET"),
        _NodeSpec("YOUTH_08_PUBLIC_NOTICE_TARGET", "公示发展对象", 80,
                 stage_group="DEVELOPMENT_TARGET", due_rule_days=5, reminder_lead_days=1),
        _NodeSpec("YOUTH_09_CONFIRM_INTRODUCER", "确定入团介绍人", 90,
                 stage_group="DEVELOPMENT_TARGET"),
        _NodeSpec("YOUTH_10_FILL_APPLICATION_FORM", "填写入团志愿书", 100,
                 stage_group="NEW_MEMBER_ACCEPTANCE",
                 required_task="填写入团志愿书"),
        _NodeSpec("YOUTH_11_BRANCH_MEETING_DISCUSSION", "支部大会讨论", 110,
                 stage_group="NEW_MEMBER_ACCEPTANCE"),
        _NodeSpec("YOUTH_12_APPROVAL_AND_FILE", "基层团（工）委审批、县级以上团委备案", 120,
                 stage_group="NEW_MEMBER_ACCEPTANCE", due_rule_days=30, reminder_lead_days=7),
        _NodeSpec("YOUTH_13_RESULT_FEEDBACK", "审批结果反馈", 130,
                 stage_group="NEW_MEMBER_ACCEPTANCE"),
        _NodeSpec("YOUTH_14_JOINING_CEREMONY", "入团仪式", 140,
                 stage_group="NEW_MEMBER_ACCEPTANCE"),
        _NodeSpec("YOUTH_15_ARCHIVE", "档案管理", 150,
                 stage_group="NEW_MEMBER_ACCEPTANCE", due_rule_days=30,
                 reminder_lead_days=7, is_terminal=True),
    ),
)

_YOUTH_LEAGUE_MEMBERSHIP_MANAGEMENT = _TemplateSpec(
    code="YOUTH_LEAGUE_MEMBERSHIP_MANAGEMENT_V1",
    name="团籍管理与推优流程",
    kind="YOUTH_LEAGUE",
    description="承载入团发展主流程之外的团籍管理事项，包括推优入党与毕业团员转出。",
    version_label="v1",
    nodes=(
        _NodeSpec("LEAGUE_RECOMMEND_PARTY", "推优入党", 10,
                 stage_group="MEMBERSHIP_MANAGEMENT", trigger_rule="MANUAL"),
        _NodeSpec("LEAGUE_GRADUATE_TRANSFER", "毕业团员转出", 20,
                 stage_group="MEMBERSHIP_MANAGEMENT", is_terminal=True),
    ),
)

_TEMPLATES: tuple[_TemplateSpec, ...] = (
    _PARTY_DEVELOPMENT_OFFICIAL,
    _YOUTH_LEAGUE_DEVELOPMENT_OFFICIAL,
    _YOUTH_LEAGUE_MEMBERSHIP_MANAGEMENT,
    _PARTY_DEVELOPMENT_LEGACY,
    _YOUTH_LEAGUE_LEGACY,
)


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
            is_active=spec.is_active,
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
        ("is_active", spec.is_active),
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
                reminder_enabled=spec.reminder_enabled,
                repeat_interval_days=spec.repeat_interval_days,
                max_reminders=spec.max_reminders,
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
            ("reminder_enabled", spec.reminder_enabled),
            ("repeat_interval_days", spec.repeat_interval_days),
            ("max_reminders", spec.max_reminders),
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
        if spec.sync_nodes_on_update or action == "insert":
            await _sync_nodes(db, tpl, spec.nodes)
    return SeedResult(
        domain=DOMAIN, inserted=inserted, updated=updated, skipped=skipped
    )
