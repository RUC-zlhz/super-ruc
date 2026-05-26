"""Import example downloadable templates into the knowledge library."""
from __future__ import annotations

import asyncio
import hashlib
import logging
import mimetypes
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import build_audit_detail, log_action
from app.auth.models import User
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.storage import put_object, remove_object
from app.knowledge import repository as repo
from app.knowledge.models import (
    ENTRY_STATUS_PUBLISHED,
    REVISION_PUBLISH,
    TEMPLATE_STATUS_ACTIVE,
    KnowledgeEntry,
    KnowledgeSource,
    TemplateAsset,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("import-common-template-examples")

_TEMPLATE_ROOT_ENV = "COMMON_TEMPLATE_EXAMPLE_ROOT"
_DEFAULT_TEMPLATE_RELATIVE_ROOT = Path("docs/source/common-templates")
_LEGACY_TEMPLATE_RELATIVE_ROOT = Path("常用模板")


@dataclass(frozen=True)
class TemplateExampleSeed:
    filename: str
    template_name: str
    template_type: str
    category_code: str
    applicable_scenario: str
    version_label: str
    source_name: str
    issuing_org: str
    entry_slug: str
    entry_title: str
    entry_summary: str
    entry_tags: tuple[str, ...]
    body_md: str
    applicable_condition: str | None = None
    process_steps: str | None = None
    manual_consult_hint: str | None = None


def _template_body(
    *,
    source_file: str,
    usage: str,
    fields: tuple[str, ...],
    note: str | None = None,
) -> str:
    lines = [
        f"来源文件：{source_file}",
        "",
        f"模板用途：{usage}",
        "",
        "模板包含字段：",
        *[f"- {field}" for field in fields],
    ]
    if note:
        lines.extend(["", f"补充说明：{note}"])
    return "\n".join(lines)


_TEMPLATE_SEEDS: tuple[TemplateExampleSeed, ...] = (
    TemplateExampleSeed(
        filename="党员证明模板.docx",
        template_name="党员证明模板",
        template_type="DOCX",
        category_code="CERTIFICATE",
        applicable_scenario="党员身份证明、组织关系证明等开具场景",
        version_label="示例模板",
        source_name="党员证明模板.docx",
        issuing_org="中国人民大学信息学院党委",
        entry_slug="party-member-proof-template-download",
        entry_title="党员证明模板下载",
        entry_summary=(
            "用于开具党员证明。模板中包含姓名、学号、身份证号、专业年级、入党时间、所属党支部、联系人、联系电话和日期等字段。"
        ),
        entry_tags=("党员证明", "证明模板", "组织关系", "党支部", "模板下载"),
        applicable_condition="需要开具党员身份或组织关系相关证明时使用。",
        process_steps="1. 下载模板；2. 按模板填写个人信息；3. 提交学院党委审核与盖章。",
        body_md=_template_body(
            source_file="党员证明模板.docx",
            usage="用于出具党员身份与组织关系证明。",
            fields=(
                "姓名",
                "学号",
                "身份证号",
                "专业与年级",
                "入党时间",
                "所属党支部",
                "联系人与联系电话",
                "落款日期",
            ),
            note="模板正文显示落款为中国人民大学信息学院党委。",
        ),
        manual_consult_hint="正式出具前请以学院党委实际审核口径和盖章流程为准。",
    ),
    TemplateExampleSeed(
        filename="团员证明.docx",
        template_name="团员证明模板",
        template_type="DOCX",
        category_code="CERTIFICATE",
        applicable_scenario="团员身份证明开具场景",
        version_label="示例模板",
        source_name="团员证明.docx",
        issuing_org="中国人民大学信息学院团委",
        entry_slug="league-member-proof-template-download",
        entry_title="团员证明模板下载",
        entry_summary=(
            "用于开具团员证明。模板中包含姓名、学号、身份证号、班级身份、入团时间、团员编号、联系人、联系电话和日期等字段。"
        ),
        entry_tags=("团员证明", "证明模板", "入团时间", "团员编号", "模板下载"),
        applicable_condition="需要开具团员身份证明时使用。",
        process_steps="1. 下载模板；2. 填写团员信息；3. 提交学院团委审核与盖章。",
        body_md=_template_body(
            source_file="团员证明.docx",
            usage="用于出具中国共产主义青年团团员证明。",
            fields=(
                "姓名",
                "学号",
                "身份证号",
                "班级与培养层次",
                "入团时间",
                "团员编号",
                "联系人与联系电话",
                "落款日期",
            ),
            note="模板正文显示落款为中国人民大学信息学院团委。",
        ),
        manual_consult_hint="正式出具前请以学院团委当前审核口径和盖章流程为准。",
    ),
    TemplateExampleSeed(
        filename="中国人民大学教室借用审批表.pdf",
        template_name="教室借用审批表",
        template_type="PDF",
        category_code="DAILY_AFFAIRS",
        applicable_scenario="借用校内教室开展活动时填写审批表",
        version_label="示例模板",
        source_name="中国人民大学教室借用审批表.pdf",
        issuing_org="中国人民大学",
        entry_slug="classroom-borrow-approval-template-download",
        entry_title="教室借用审批表下载",
        entry_summary=(
            "用于借用教室时填写审批。模板首页包含申请人信息、借用教室信息、日期/节次/教学楼/教室编号/教室类型/教室规模、活动详情和审核信息。"
        ),
        entry_tags=("教室借用", "审批表", "活动申请", "教室编号", "模板下载"),
        applicable_condition="需要借用学校教室开展活动时使用。",
        process_steps="1. 下载审批表；2. 填写申请人、借用教室信息和活动详情；3. 按要求提交审核。",
        body_md=_template_body(
            source_file="中国人民大学教室借用审批表.pdf",
            usage="用于提交教室借用审批。",
            fields=(
                "申请人信息",
                "日期",
                "节次",
                "教学楼",
                "教室编号",
                "教室类型",
                "教室规模",
                "借用活动详情",
                "审核信息",
            ),
            note="首页页眉直接标明为“中国人民大学教室借用审批表”。",
        ),
        manual_consult_hint="具体借用流程、审批部门和可借时间以学校当期正式通知与场地管理要求为准。",
    ),
    TemplateExampleSeed(
        filename="“求是学术”品牌研究项目立项申报书.docx",
        template_name="“求是学术”品牌研究项目立项申报书",
        template_type="DOCX",
        category_code="ACADEMIC",
        applicable_scenario="“求是学术”品牌研究项目申报场景",
        version_label="示例模板",
        source_name="“求是学术”品牌研究项目立项申报书.docx",
        issuing_org="中国人民大学教务处",
        entry_slug="qiushi-academic-project-application-template-download",
        entry_title="“求是学术”品牌研究项目立项申报书下载",
        entry_summary=(
            "用于“求是学术”品牌研究项目申报。模板中包含项目题目、书院/学院、负责人、指导教师、项目简介、项目申请条件、立项依据与文献综述、研究方案、项目特色与创新等栏目。"
        ),
        entry_tags=("求是学术", "项目申报", "立项申报书", "本科生项目", "模板下载"),
        applicable_condition="负责人为本科生的“求是学术”品牌研究项目申报场景。",
        process_steps="1. 下载申报书；2. 填写项目与成员信息；3. 完成简介、申请条件、文献综述、研究方案和创新点；4. 按要求提交。",
        body_md=_template_body(
            source_file="“求是学术”品牌研究项目立项申报书.docx",
            usage="用于“求是学术”品牌研究项目立项申报。",
            fields=(
                "项目题目",
                "项目所在书院",
                "项目负责人、学号、所在学院（系）、电话、邮箱",
                "项目指导教师、职工号、所在单位",
                "项目团队成员信息",
                "项目简介",
                "项目申请条件",
                "项目立项依据与文献综述",
                "项目研究方案",
                "项目特色与创新之处",
            ),
            note="模板首页显示“中国人民大学教务处制表”，并标注负责人为本科生。",
        ),
        manual_consult_hint="正式申报要求、字数限制和提交时间请以当期项目通知为准。",
    ),
)


def _required_template_filenames() -> tuple[str, ...]:
    return tuple(seed.filename for seed in _TEMPLATE_SEEDS)


def _candidate_template_roots() -> list[Path]:
    script_path = Path(__file__).resolve()
    candidates = [
        Path("/docs/source/common-templates"),
        script_path.parents[2] / _DEFAULT_TEMPLATE_RELATIVE_ROOT,
        script_path.parents[1] / _DEFAULT_TEMPLATE_RELATIVE_ROOT,
        script_path.parents[2] / _LEGACY_TEMPLATE_RELATIVE_ROOT,
        script_path.parents[1] / _LEGACY_TEMPLATE_RELATIVE_ROOT,
        Path("/app") / _LEGACY_TEMPLATE_RELATIVE_ROOT,
        Path("/") / _LEGACY_TEMPLATE_RELATIVE_ROOT,
    ]

    seen: set[Path] = set()
    unique: list[Path] = []
    for path in candidates:
        resolved = path.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def _missing_template_files(root: Path) -> list[str]:
    return [filename for filename in _required_template_filenames() if not (root / filename).is_file()]


def _format_template_root_error(candidates: list[Path]) -> str:
    required = "、".join(_required_template_filenames())
    searched = "；".join(str(path) for path in candidates)
    return f"Template example files not found. Required: {required}. Searched: {searched}"


@lru_cache(maxsize=1)
def get_template_example_root() -> Path:
    """Resolve the runtime directory that contains the bundled example templates."""
    env_root = os.environ.get(_TEMPLATE_ROOT_ENV)
    if env_root and env_root.strip():
        root = Path(env_root.strip()).expanduser()
        missing = _missing_template_files(root)
        if missing:
            raise FileNotFoundError(
                f"{_TEMPLATE_ROOT_ENV}={root} is missing template files: {', '.join(missing)}"
            )
        return root

    candidates = _candidate_template_roots()
    for root in candidates:
        if root.is_dir() and not _missing_template_files(root):
            return root

    raise FileNotFoundError(_format_template_root_error(candidates))


def assert_template_example_files_available() -> Path:
    """Fail early when default-data seeding cannot see all bundled templates."""
    return get_template_example_root()


async def _resolve_operator(db: AsyncSession) -> tuple[int, str]:
    admin = (
        await db.execute(select(User).where(User.work_no == "admin").limit(1))
    ).scalar_one_or_none()
    if admin:
        return admin.id, "SUPER_ADMIN"
    return 0, "COMMON_TEMPLATE_IMPORT"


async def _upsert_source(
    db: AsyncSession,
    *,
    source_name: str,
    issuing_org: str,
    version_label: str,
    only_missing: bool = False,
) -> tuple[KnowledgeSource, str]:
    current = (
        await db.execute(select(KnowledgeSource).where(KnowledgeSource.source_name == source_name))
    ).scalar_one_or_none()
    fields = {
        "source_name": source_name,
        "source_url": None,
        "issuing_org": issuing_org,
        "version_label": version_label,
        "is_official": False,
        "is_active": True,
    }
    if current is None:
        current = await repo.create_source(db, **fields)
        return current, "created"
    if only_missing:
        return current, "skipped"

    changed = False
    for key, value in fields.items():
        if getattr(current, key) != value:
            setattr(current, key, value)
            changed = True
    if changed:
        await db.flush()
        return current, "updated"
    return current, "skipped"


def _template_file_path(seed: TemplateExampleSeed) -> Path:
    return get_template_example_root() / seed.filename


def _template_content_type(seed: TemplateExampleSeed) -> str:
    guessed, _ = mimetypes.guess_type(seed.filename)
    return guessed or "application/octet-stream"


async def _find_template_by_name(db: AsyncSession, template_name: str) -> TemplateAsset | None:
    return (
        await db.execute(select(TemplateAsset).where(TemplateAsset.template_name == template_name))
    ).scalar_one_or_none()


async def _upsert_template(
    db: AsyncSession,
    seed: TemplateExampleSeed,
    *,
    operator_id: int,
    operator_role: str,
    only_missing: bool = False,
) -> tuple[TemplateAsset, str]:
    path = _template_file_path(seed)
    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {path}")

    current = await _find_template_by_name(db, seed.template_name)
    if current is not None and only_missing:
        return current, "skipped"

    content = path.read_bytes()
    checksum = hashlib.sha256(content).hexdigest()
    content_type = _template_content_type(seed)
    fields = {
        "template_name": seed.template_name,
        "template_type": seed.template_type,
        "category_code": seed.category_code,
        "applicable_scenario": seed.applicable_scenario,
        "version_label": seed.version_label,
        "file_size": len(content),
        "mime_type": content_type,
        "checksum_sha256": checksum,
        "status": TEMPLATE_STATUS_ACTIVE,
        "uploaded_by": operator_id,
    }

    if current is not None:
        same = all(getattr(current, key) == value for key, value in fields.items())
        if same:
            return current, "skipped"

    bucket = settings.MINIO_BUCKET_TEMPLATE
    object_key = f"templates/examples/{uuid.uuid4().hex}_{path.name}"
    put_object(
        bucket=bucket,
        object_key=object_key,
        data=content,
        length=len(content),
        content_type=content_type,
    )

    if current is None:
        row = await repo.create_template(
            db,
            object_bucket=bucket,
            object_key=object_key,
            **fields,
        )
        await log_action(
            db,
            event_type="KNOWLEDGE",
            entity_code="TEMPLATE",
            action="IMPORT_COMMON_TEMPLATE",
            entity_id=row.id,
            actor_user_id=operator_id or None,
            actor_role=operator_role,
            detail=build_audit_detail(
                target={"template_id": row.id, "template_name": row.template_name},
                refs={"source_file": seed.filename},
                metrics={"created": 1},
            ),
        )
        return row, "created"

    old_bucket = current.object_bucket
    old_object_key = current.object_key
    for key, value in fields.items():
        setattr(current, key, value)
    current.object_bucket = bucket
    current.object_key = object_key
    current.deprecated_at = None
    current.deprecated_by = None
    await db.flush()
    if old_bucket != bucket or old_object_key != object_key:
        remove_object(old_bucket, old_object_key)
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="TEMPLATE",
        action="IMPORT_COMMON_TEMPLATE",
        entity_id=current.id,
        actor_user_id=operator_id or None,
        actor_role=operator_role,
        detail=build_audit_detail(
            target={"template_id": current.id, "template_name": current.template_name},
            refs={"source_file": seed.filename},
            metrics={"updated": 1},
        ),
    )
    return current, "updated"


def _entry_changed(entry: KnowledgeEntry, seed: TemplateExampleSeed, *, source_id: int, template_id: int) -> bool:
    comparable_fields = {
        "title": seed.entry_title,
        "summary": seed.entry_summary,
        "category_code": seed.category_code,
        "applicable_condition": seed.applicable_condition,
        "required_materials": None,
        "process_steps": seed.process_steps,
        "body_md": seed.body_md,
        "source_id": source_id,
        "version_label": seed.version_label,
        "ambiguity_flag": False,
        "manual_consult_hint": seed.manual_consult_hint,
        "status": ENTRY_STATUS_PUBLISHED,
    }
    for key, expected in comparable_fields.items():
        if getattr(entry, key) != expected:
            return True
    current_tags = {tag.tag for tag in (entry.tags or [])}
    current_template_ids = {item.template_id for item in (entry.templates or [])}
    return current_tags != set(seed.entry_tags) or current_template_ids != {template_id}


async def _upsert_entry(
    db: AsyncSession,
    seed: TemplateExampleSeed,
    *,
    source_id: int,
    template_id: int,
    operator_id: int,
    operator_role: str,
    only_missing: bool = False,
) -> str:
    now = datetime.now(UTC)
    entry = await repo.get_entry_by_slug(db, seed.entry_slug)
    snapshot = {
        "title": seed.entry_title,
        "summary": seed.entry_summary,
        "category_code": seed.category_code,
        "applicable_condition": seed.applicable_condition,
        "process_steps": seed.process_steps,
        "body_md": seed.body_md,
        "source_id": source_id,
        "version_label": seed.version_label,
        "tags": list(seed.entry_tags),
        "template_ids": [template_id],
    }
    if entry is None:
        entry = KnowledgeEntry(
            slug=seed.entry_slug,
            title=seed.entry_title,
            summary=seed.entry_summary,
            category_code=seed.category_code,
            applicable_condition=seed.applicable_condition,
            required_materials=None,
            process_steps=seed.process_steps,
            body_md=seed.body_md,
            source_id=source_id,
            version_label=seed.version_label,
            status=ENTRY_STATUS_PUBLISHED,
            ambiguity_flag=False,
            manual_consult_hint=seed.manual_consult_hint,
            published_at=now,
            published_by=operator_id,
            deprecated_at=None,
            deprecated_by=None,
            created_by=operator_id,
            updated_by=operator_id,
        )
        db.add(entry)
        await db.flush()
        await repo.set_entry_tags(db, entry.id, list(seed.entry_tags))
        await repo.set_entry_templates(db, entry.id, [template_id])
        await repo.add_revision(
            db,
            entry_id=entry.id,
            action=REVISION_PUBLISH,
            version_label=seed.version_label,
            status_before=None,
            status_after=ENTRY_STATUS_PUBLISHED,
            snapshot=snapshot,
            operator_id=operator_id,
            operator_role=operator_role,
            note="common template example import create+publish",
        )
        await log_action(
            db,
            event_type="KNOWLEDGE",
            entity_code="KNOWLEDGE_ENTRY",
            action="IMPORT_COMMON_TEMPLATE_ENTRY",
            entity_id=entry.id,
            actor_user_id=operator_id or None,
            actor_role=operator_role,
            detail=build_audit_detail(
                target={"entry_id": entry.id, "slug": entry.slug, "title": entry.title},
                refs={"source_name": seed.source_name, "template_name": seed.template_name},
                metrics={"created": 1},
            ),
        )
        return "created"

    if only_missing:
        return "skipped"

    if not _entry_changed(entry, seed, source_id=source_id, template_id=template_id):
        return "skipped"

    previous_status = entry.status
    entry.title = seed.entry_title
    entry.summary = seed.entry_summary
    entry.category_code = seed.category_code
    entry.applicable_condition = seed.applicable_condition
    entry.required_materials = None
    entry.process_steps = seed.process_steps
    entry.body_md = seed.body_md
    entry.source_id = source_id
    entry.version_label = seed.version_label
    entry.status = ENTRY_STATUS_PUBLISHED
    entry.ambiguity_flag = False
    entry.manual_consult_hint = seed.manual_consult_hint
    entry.deprecated_at = None
    entry.deprecated_by = None
    if entry.published_at is None:
        entry.published_at = now
    entry.published_by = operator_id
    entry.updated_by = operator_id
    await db.flush()
    await repo.set_entry_tags(db, entry.id, list(seed.entry_tags))
    await repo.set_entry_templates(db, entry.id, [template_id])
    await repo.add_revision(
        db,
        entry_id=entry.id,
        action=REVISION_PUBLISH,
        version_label=seed.version_label,
        status_before=previous_status,
        status_after=ENTRY_STATUS_PUBLISHED,
        snapshot=snapshot,
        operator_id=operator_id,
        operator_role=operator_role,
        note="common template example import refresh",
    )
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="KNOWLEDGE_ENTRY",
        action="IMPORT_COMMON_TEMPLATE_ENTRY",
        entity_id=entry.id,
        actor_user_id=operator_id or None,
        actor_role=operator_role,
        detail=build_audit_detail(
            target={"entry_id": entry.id, "slug": entry.slug, "title": entry.title},
            refs={"source_name": seed.source_name, "template_name": seed.template_name},
            metrics={"updated": 1},
        ),
    )
    return "updated"


async def import_common_template_examples(
    db: AsyncSession,
    *,
    only_missing: bool = False,
    skip_if_any_templates: bool = False,
) -> tuple[dict[str, int], dict[str, int], dict[str, int], bool]:
    operator_id, operator_role = await _resolve_operator(db)
    source_stats = {"created": 0, "updated": 0, "skipped": 0}
    template_stats = {"created": 0, "updated": 0, "skipped": 0}
    entry_stats = {"created": 0, "updated": 0, "skipped": 0}

    existing_templates = await db.scalar(select(func.count()).select_from(TemplateAsset))
    skipped_due_to_existing_templates = bool(
        skip_if_any_templates and existing_templates and existing_templates > 0
    )
    if skipped_due_to_existing_templates:
        source_stats["skipped"] = len(_TEMPLATE_SEEDS)
        template_stats["skipped"] = len(_TEMPLATE_SEEDS)
        entry_stats["skipped"] = len(_TEMPLATE_SEEDS)
        return source_stats, template_stats, entry_stats, True

    for seed in _TEMPLATE_SEEDS:
        source, source_status = await _upsert_source(
            db,
            source_name=seed.source_name,
            issuing_org=seed.issuing_org,
            version_label=seed.version_label,
            only_missing=only_missing,
        )
        source_stats[source_status] += 1

        template, template_status = await _upsert_template(
            db,
            seed,
            operator_id=operator_id,
            operator_role=operator_role,
            only_missing=only_missing,
        )
        template_stats[template_status] += 1

        entry_status = await _upsert_entry(
            db,
            seed,
            source_id=source.id,
            template_id=template.id,
            operator_id=operator_id,
            operator_role=operator_role,
            only_missing=only_missing,
        )
        entry_stats[entry_status] += 1

    return source_stats, template_stats, entry_stats, False


async def _main() -> int:
    async with AsyncSessionLocal() as db:
        source_stats, template_stats, entry_stats, skipped = await import_common_template_examples(db)
        await db.commit()

    if skipped:
        logger.info("common template example import skipped because template assets already exist")
        return 0

    logger.info(
        "common template example import finished: sources created=%s updated=%s skipped=%s; "
        "templates created=%s updated=%s skipped=%s; "
        "entries created=%s updated=%s skipped=%s",
        source_stats["created"],
        source_stats["updated"],
        source_stats["skipped"],
        template_stats["created"],
        template_stats["updated"],
        template_stats["skipped"],
        entry_stats["created"],
        entry_stats["updated"],
        entry_stats["skipped"],
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
