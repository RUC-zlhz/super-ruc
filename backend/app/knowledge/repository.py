"""knowledge 模块仓储层。"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from sqlalchemy import String, and_, case, cast, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.models import (
    ENTRY_STATUS_PUBLISHED,
    KnowledgeCategory,
    KnowledgeEntry,
    KnowledgeEntryTag,
    KnowledgeEntryTemplate,
    KnowledgeRevision,
    KnowledgeSource,
    TemplateAsset,
)


# ---------- Category ----------
async def list_categories(db: AsyncSession) -> Sequence[KnowledgeCategory]:
    stmt = (
        select(KnowledgeCategory)
        .where(KnowledgeCategory.is_active.is_(True))
        .order_by(KnowledgeCategory.sort_order, KnowledgeCategory.code)
    )
    return (await db.execute(stmt)).scalars().all()


async def upsert_category(db: AsyncSession, code: str, **fields) -> KnowledgeCategory:
    existing = (
        await db.execute(select(KnowledgeCategory).where(KnowledgeCategory.code == code))
    ).scalar_one_or_none()
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        await db.flush()
        return existing
    row = KnowledgeCategory(code=code, **fields)
    db.add(row)
    await db.flush()
    return row


# ---------- Source ----------
async def list_sources(db: AsyncSession, *, active_only: bool = True) -> Sequence[KnowledgeSource]:
    stmt = select(KnowledgeSource)
    if active_only:
        stmt = stmt.where(KnowledgeSource.is_active.is_(True))
    return (
        await db.execute(
            stmt.order_by(KnowledgeSource.is_official.desc(), KnowledgeSource.id.desc())
        )
    ).scalars().all()


async def get_source(db: AsyncSession, source_id: int) -> KnowledgeSource | None:
    return await db.get(KnowledgeSource, source_id)


async def create_source(db: AsyncSession, **fields) -> KnowledgeSource:
    row = KnowledgeSource(**fields)
    db.add(row)
    await db.flush()
    return row


async def update_source(db: AsyncSession, source_id: int, **fields) -> KnowledgeSource | None:
    row = await get_source(db, source_id)
    if row is None:
        return None
    for key, value in fields.items():
        setattr(row, key, value)
    await db.flush()
    return row


# ---------- Entry ----------
async def get_entry(db: AsyncSession, entry_id: int) -> KnowledgeEntry | None:
    return await db.get(KnowledgeEntry, entry_id)


async def get_entry_by_slug(db: AsyncSession, slug: str) -> KnowledgeEntry | None:
    stmt = select(KnowledgeEntry).where(KnowledgeEntry.slug == slug)
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_entry(db: AsyncSession, **fields) -> KnowledgeEntry:
    row = KnowledgeEntry(**fields)
    db.add(row)
    await db.flush()
    return row


async def set_entry_tags(db: AsyncSession, entry_id: int, tags: list[str]) -> None:
    # 清空旧关联
    existing = (
        await db.execute(select(KnowledgeEntryTag).where(KnowledgeEntryTag.entry_id == entry_id))
    ).scalars().all()
    for row in existing:
        await db.delete(row)
    # 建新关联，去重
    for tag in {t.strip() for t in tags if t and t.strip()}:
        db.add(KnowledgeEntryTag(entry_id=entry_id, tag=tag))
    await db.flush()


async def set_entry_templates(db: AsyncSession, entry_id: int, template_ids: list[int]) -> None:
    existing = (
        await db.execute(
            select(KnowledgeEntryTemplate).where(KnowledgeEntryTemplate.entry_id == entry_id)
        )
    ).scalars().all()
    for row in existing:
        await db.delete(row)
    for tid in set(template_ids):
        db.add(KnowledgeEntryTemplate(entry_id=entry_id, template_id=tid))
    await db.flush()


async def search_published_entries(
    db: AsyncSession,
    *,
    q: str | None = None,
    category_code: str | None = None,
    tag: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[Sequence[KnowledgeEntry], int]:
    today = date.today()
    stmt = (
        select(KnowledgeEntry)
        .outerjoin(KnowledgeSource, KnowledgeSource.id == KnowledgeEntry.source_id)
        .where(KnowledgeEntry.status == ENTRY_STATUS_PUBLISHED)
    )
    if category_code:
        stmt = stmt.where(KnowledgeEntry.category_code == category_code)
    if q:
        like = f"%{q}%"
        tag_like_exists = exists(
            select(1).where(
                KnowledgeEntryTag.entry_id == KnowledgeEntry.id,
                KnowledgeEntryTag.tag.ilike(like),
            )
        )
        stmt = stmt.where(
            or_(
                KnowledgeEntry.title.ilike(like),
                KnowledgeEntry.summary.ilike(like),
                KnowledgeEntry.applicable_condition.ilike(like),
                KnowledgeEntry.required_materials.ilike(like),
                KnowledgeEntry.process_steps.ilike(like),
                KnowledgeEntry.body_md.ilike(like),
                tag_like_exists,
                KnowledgeSource.source_name.ilike(like),
                KnowledgeSource.issuing_org.ilike(like),
            )
        )
    if tag:
        tag_exists = exists(
            select(1).where(
                KnowledgeEntryTag.entry_id == KnowledgeEntry.id,
                KnowledgeEntryTag.tag == tag,
            )
        )
        stmt = stmt.where(tag_exists)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        stmt.order_by(
            case((KnowledgeSource.is_active.is_(True), 1), else_=0).desc(),
            case((KnowledgeSource.expires_on.is_(None), 1), (KnowledgeSource.expires_on >= today, 1), else_=0).desc(),
            case((KnowledgeSource.is_official.is_(True), 1), else_=0).desc(),
            case((KnowledgeSource.source_url.isnot(None), 1), else_=0).desc(),
            KnowledgeEntry.updated_at.desc(),
        )
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = (await db.execute(stmt)).scalars().unique().all()
    return rows, total


async def list_all_entries_admin(
    db: AsyncSession,
    *,
    q: str | None = None,
    status: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[Sequence[KnowledgeEntry], int]:
    stmt = select(KnowledgeEntry)
    conds = []
    if status:
        conds.append(KnowledgeEntry.status == status)
    if q:
        like = f"%{q}%"
        conds.append(or_(KnowledgeEntry.title.ilike(like), KnowledgeEntry.slug.ilike(like)))
    if conds:
        stmt = stmt.where(and_(*conds))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(KnowledgeEntry.updated_at.desc()).offset((page - 1) * size).limit(size)
    rows = (await db.execute(stmt)).scalars().unique().all()
    return rows, total


async def list_entry_revisions(db: AsyncSession, entry_id: int) -> Sequence[KnowledgeRevision]:
    stmt = (
        select(KnowledgeRevision)
        .where(KnowledgeRevision.entry_id == entry_id)
        .order_by(KnowledgeRevision.occurred_at.desc())
    )
    return (await db.execute(stmt)).scalars().all()


async def add_revision(db: AsyncSession, **fields) -> KnowledgeRevision:
    row = KnowledgeRevision(**fields)
    db.add(row)
    await db.flush()
    return row


# ---------- Template ----------
async def create_template(db: AsyncSession, **fields) -> TemplateAsset:
    row = TemplateAsset(**fields)
    db.add(row)
    await db.flush()
    return row


async def get_template(db: AsyncSession, template_id: int) -> TemplateAsset | None:
    return await db.get(TemplateAsset, template_id)


async def list_templates(
    db: AsyncSession,
    *,
    category_code: str | None = None,
    q: str | None = None,
    include_deprecated: bool = False,
    page: int = 1,
    size: int = 20,
) -> tuple[Sequence[TemplateAsset], int]:
    stmt = select(TemplateAsset)
    if not include_deprecated:
        stmt = stmt.where(TemplateAsset.status == "ACTIVE")
    if category_code:
        stmt = stmt.where(TemplateAsset.category_code == category_code)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                TemplateAsset.template_name.ilike(like),
                TemplateAsset.applicable_scenario.ilike(like),
                cast(TemplateAsset.tags, String).ilike(like),
            )
        )
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(TemplateAsset.uploaded_at.desc()).offset((page - 1) * size).limit(size)
    rows = (await db.execute(stmt)).scalars().all()
    return rows, total


async def list_active_templates_for_student(
    db: AsyncSession,
    *,
    category_code: str | None = None,
    q: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[Sequence[TemplateAsset], int]:
    stmt = select(TemplateAsset).where(TemplateAsset.status == "ACTIVE")
    if category_code:
        stmt = stmt.where(TemplateAsset.category_code == category_code)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                TemplateAsset.template_name.ilike(like),
                TemplateAsset.applicable_scenario.ilike(like),
                cast(TemplateAsset.tags, String).ilike(like),
            )
        )
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    stmt = stmt.order_by(TemplateAsset.uploaded_at.desc()).offset((page - 1) * size).limit(size)
    return (await db.execute(stmt)).scalars().unique().all(), total
