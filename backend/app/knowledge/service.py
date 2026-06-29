"""knowledge 业务服务层。"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_action
from app.core.cache import cache_delete_prefix, cache_get_text, cache_set_text
from app.core.config import settings
from app.core.exceptions import BizError, ConflictError, NotFoundError
from app.core.storage import get_object_bytes, presigned_get, put_object
from app.knowledge import ai_matcher
from app.knowledge import repository as repo
from app.knowledge.models import (
    ENTRY_STATUS_DEPRECATED,
    ENTRY_STATUS_DRAFT,
    ENTRY_STATUS_PUBLISHED,
    REVISION_DEPRECATE,
    REVISION_PUBLISH,
    REVISION_UPDATE,
    TEMPLATE_STATUS_ACTIVE,
    TEMPLATE_STATUS_DEPRECATED,
    KnowledgeEntry,
    TemplateAsset,
)
from app.knowledge.schemas import (
    AiMatchCandidate,
    AiMatchResponse,
    CategoryOut,
    EntryBrief,
    EntryCreate,
    EntryDetail,
    EntryTemplateRef,
    EntryUpdate,
    SourceOut,
)

logger = logging.getLogger(__name__)

# ---------- 知识库热点只读缓存（公开已发布内容；写操作即清空命名空间）----------
_KNOWLEDGE_CACHE_PREFIX = "knowledge:"
_CATEGORIES_CACHE_KEY = "knowledge:categories:v1"
_category_list_adapter = TypeAdapter(list[CategoryOut])


def _entry_cache_key(entry_id: int) -> str:
    return f"knowledge:entry:v1:{entry_id}"


async def invalidate_knowledge_cache() -> None:
    """任何知识写操作后清空知识缓存命名空间（分类 + 条目详情）。

    知识写操作（管理端）频率低，整命名空间清空足够简单且保证一致，
    避免逐键失效的耦合。"""
    await cache_delete_prefix(_KNOWLEDGE_CACHE_PREFIX)


# ---------- 展示转换 ----------
def _entry_source_is_official(entry: KnowledgeEntry) -> bool:
    return bool(entry.source and entry.source.is_official)


def entry_to_brief(entry: KnowledgeEntry) -> EntryBrief:
    return EntryBrief(
        id=entry.id,
        slug=entry.slug,
        title=entry.title,
        summary=entry.summary,
        category_code=entry.category_code,
        applicable_condition=entry.applicable_condition,
        required_materials=entry.required_materials,
        process_steps=entry.process_steps,
        status=entry.status,
        ambiguity_flag=entry.ambiguity_flag,
        version_label=entry.version_label,
        updated_at=entry.updated_at,
        tags=[t.tag for t in (entry.tags or [])],
        source_name=entry.source.source_name if entry.source else None,
        source_url=entry.source.source_url if entry.source else None,
        source_is_official=_entry_source_is_official(entry),
    )


def entry_to_detail(entry: KnowledgeEntry) -> EntryDetail:
    templates: list[EntryTemplateRef] = []
    for et in entry.templates or []:
        if et.template and et.template.status == TEMPLATE_STATUS_ACTIVE:
            templates.append(
                EntryTemplateRef(
                    template_id=et.template.id,
                    template_name=et.template.template_name,
                    template_type=et.template.template_type,
                    version_label=et.template.version_label,
                )
            )
    return EntryDetail(
        id=entry.id,
        slug=entry.slug,
        title=entry.title,
        summary=entry.summary,
        category_code=entry.category_code,
        applicable_condition=entry.applicable_condition,
        required_materials=entry.required_materials,
        process_steps=entry.process_steps,
        body_md=entry.body_md,
        status=entry.status,
        version_label=entry.version_label,
        ambiguity_flag=entry.ambiguity_flag,
        manual_consult_hint=entry.manual_consult_hint,
        published_at=entry.published_at,
        updated_at=entry.updated_at,
        tags=[t.tag for t in (entry.tags or [])],
        source=SourceOut.model_validate(entry.source) if entry.source else None,
        templates=templates,
    )


def _entry_answer_preview(entry: KnowledgeEntry) -> str | None:
    for value in (
        entry.summary,
        entry.applicable_condition,
        entry.required_materials,
        entry.process_steps,
        entry.body_md,
    ):
        if value and value.strip():
            snippet = " ".join(value.strip().split())
            return snippet[:180]
    return None


def _snapshot(entry: KnowledgeEntry) -> dict[str, Any]:
    return {
        "title": entry.title,
        "summary": entry.summary,
        "category_code": entry.category_code,
        "applicable_condition": entry.applicable_condition,
        "required_materials": entry.required_materials,
        "process_steps": entry.process_steps,
        "body_md": entry.body_md,
        "version_label": entry.version_label,
        "source_id": entry.source_id,
        "ambiguity_flag": entry.ambiguity_flag,
    }


# ---------- 搜索 ----------
async def search_for_student(
    db: AsyncSession,
    *,
    q: str | None,
    category_code: str | None,
    tag: str | None,
    page: int,
    size: int,
) -> tuple[list[EntryBrief], int]:
    rows, total = await repo.search_published_entries(
        db, q=q, category_code=category_code, tag=tag, page=page, size=size
    )
    return [entry_to_brief(r) for r in rows], total


async def list_templates_for_student(
    db: AsyncSession,
    *,
    q: str | None,
    category_code: str | None,
    page: int,
    size: int,
) -> tuple[list[TemplateAsset], int]:
    rows, total = await repo.list_active_templates_for_student(
        db,
        q=q,
        category_code=category_code,
        page=page,
        size=size,
    )
    return list(rows), total


async def list_categories_for_student(db: AsyncSession) -> list[CategoryOut]:
    """知识分类列表（公开、变更稀疏）——带缓存，写分类时整命名空间失效。"""
    cached = await cache_get_text(_CATEGORIES_CACHE_KEY)
    if cached is not None:
        try:
            return _category_list_adapter.validate_json(cached)
        except Exception as exc:  # noqa: BLE001 — 缓存损坏则直查覆盖
            logger.warning("knowledge categories cache parse failed: %s", exc)
    rows = await repo.list_categories(db)
    result = [CategoryOut.model_validate(r) for r in rows]
    await cache_set_text(
        _CATEGORIES_CACHE_KEY,
        _category_list_adapter.dump_json(result).decode("utf-8"),
        settings.KNOWLEDGE_CACHE_TTL_SECONDS,
    )
    return result


async def get_for_student(db: AsyncSession, entry_id: int) -> EntryDetail:
    cache_key = _entry_cache_key(entry_id)
    cached = await cache_get_text(cache_key)
    if cached is not None:
        try:
            return EntryDetail.model_validate_json(cached)
        except Exception as exc:  # noqa: BLE001 — 缓存损坏则直查覆盖
            logger.warning("knowledge entry cache parse failed id=%s: %s", entry_id, exc)
    entry = await repo.get_entry(db, entry_id)
    if entry is None or entry.status != ENTRY_STATUS_PUBLISHED:
        raise NotFoundError("知识条目不存在或未发布")
    result = entry_to_detail(entry)
    await cache_set_text(
        cache_key, result.model_dump_json(), settings.KNOWLEDGE_CACHE_TTL_SECONDS
    )
    return result


async def get_for_admin(db: AsyncSession, entry_id: int) -> EntryDetail:
    entry = await repo.get_entry(db, entry_id)
    if entry is None:
        raise NotFoundError("知识条目不存在")
    return entry_to_detail(entry)


# ---------- 检索式知识匹配 ----------
async def ai_match(db: AsyncSession, query: str, top_k: int) -> AiMatchResponse:
    # 兼容旧接口名；当前产品口径只做检索式匹配，不调用生成式模型。
    prefetched, _ = await repo.search_published_entries(db, q=query, page=1, size=20)
    if not prefetched:
        # 自然语言问法不一定能被 SQL 级整句 LIKE 命中；未命中时回退到已发布条目集合做关键词重排。
        prefetched, _ = await repo.search_published_entries(db, q=None, page=1, size=200)
    if not prefetched:
        return AiMatchResponse(
            engine="retrieval",
            candidates=[],
            manual_consult_required=True,
            manual_consult_hint="知识库中暂无已发布条目，建议先由老师发布知识后再检索",
        )

    candidates: list[AiMatchCandidate] = []

    scored = ai_matcher.rank_by_keyword(list(prefetched), query, top_k)
    for e, score in scored:
        norm = min(1.0, score / 10.0)
        candidates.append(
            AiMatchCandidate(
                entry_id=e.id,
                slug=e.slug,
                title=e.title,
                summary=_entry_answer_preview(e),
                score=round(norm, 3),
                reason=ai_matcher.explain_keyword_match(e, query),
                source_name=e.source.source_name if e.source else None,
                source_url=e.source.source_url if e.source else None,
                source_is_official=_entry_source_is_official(e),
                version_label=e.version_label,
                ambiguity_flag=e.ambiguity_flag,
            )
        )

    manual = not candidates or any(c.ambiguity_flag for c in candidates)
    hint = None
    if manual:
        matched_hint = next(
            (c for c in candidates if c.ambiguity_flag),
            None,
        )
        hint = "检测到模糊/特殊情形，建议转人工咨询" if matched_hint else "未找到充分匹配条目"

    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="KNOWLEDGE_QUERY",
        action="AI_MATCH",
        detail={"query": query[:200], "engine": "retrieval", "count": len(candidates)},
    )
    await db.commit()
    return AiMatchResponse(
        engine="retrieval",
        candidates=candidates,
        manual_consult_required=manual,
        manual_consult_hint=hint,
    )


# ---------- 条目管理 ----------
async def create_entry(
    db: AsyncSession, payload: EntryCreate, operator_id: int, operator_role: str | None = None
) -> EntryDetail:
    existing = await repo.get_entry_by_slug(db, payload.slug)
    if existing is not None:
        raise ConflictError(f"slug 已存在：{payload.slug}")
    if payload.source_id is not None and (await repo.get_source(db, payload.source_id)) is None:
        raise NotFoundError(f"知识来源不存在：{payload.source_id}")

    entry = await repo.create_entry(
        db,
        slug=payload.slug,
        title=payload.title,
        summary=payload.summary,
        category_code=payload.category_code,
        applicable_condition=payload.applicable_condition,
        required_materials=payload.required_materials,
        process_steps=payload.process_steps,
        body_md=payload.body_md,
        source_id=payload.source_id,
        version_label=payload.version_label,
        ambiguity_flag=payload.ambiguity_flag,
        manual_consult_hint=payload.manual_consult_hint,
        status=ENTRY_STATUS_DRAFT,
        created_by=operator_id,
        updated_by=operator_id,
    )
    await repo.set_entry_tags(db, entry.id, payload.tags)
    await repo.set_entry_templates(db, entry.id, payload.template_ids)
    await repo.add_revision(
        db,
        entry_id=entry.id,
        action=REVISION_UPDATE,
        version_label=entry.version_label,
        status_before=None,
        status_after=entry.status,
        snapshot=_snapshot(entry),
        operator_id=operator_id,
        operator_role=operator_role,
        note="create draft",
    )
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="KNOWLEDGE_ENTRY",
        action="CREATE",
        entity_id=entry.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(entry)
    await invalidate_knowledge_cache()
    return entry_to_detail(entry)


async def update_entry(
    db: AsyncSession,
    entry_id: int,
    payload: EntryUpdate,
    operator_id: int,
    operator_role: str | None = None,
) -> EntryDetail:
    entry = await repo.get_entry(db, entry_id)
    if entry is None:
        raise NotFoundError("条目不存在")
    if entry.status == ENTRY_STATUS_DEPRECATED:
        raise BizError("已停用的条目不可再编辑，请新建新版本", code=40010)

    changed = payload.model_dump(exclude_unset=True, exclude={"tags", "template_ids"})
    for k, v in changed.items():
        setattr(entry, k, v)
    entry.updated_by = operator_id

    if payload.tags is not None:
        await repo.set_entry_tags(db, entry.id, payload.tags)
    if payload.template_ids is not None:
        await repo.set_entry_templates(db, entry.id, payload.template_ids)

    await repo.add_revision(
        db,
        entry_id=entry.id,
        action=REVISION_UPDATE,
        version_label=entry.version_label,
        status_before=entry.status,
        status_after=entry.status,
        snapshot=_snapshot(entry),
        operator_id=operator_id,
        operator_role=operator_role,
    )
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="KNOWLEDGE_ENTRY",
        action="UPDATE",
        entity_id=entry.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(entry)
    await invalidate_knowledge_cache()
    return entry_to_detail(entry)


async def publish_entry(
    db: AsyncSession, entry_id: int, note: str | None, operator_id: int, operator_role: str | None
) -> EntryDetail:
    entry = await repo.get_entry(db, entry_id)
    if entry is None:
        raise NotFoundError("条目不存在")
    if not entry.source_id:
        raise BizError("发布前必须指定权威来源（FR-002）", code=40011)
    if not entry.applicable_condition and not entry.process_steps and not entry.body_md:
        raise BizError("发布前必须至少填写适用条件/办理步骤/正文之一", code=40012)

    status_before = entry.status
    entry.status = ENTRY_STATUS_PUBLISHED
    entry.published_at = datetime.now(UTC)
    entry.published_by = operator_id
    entry.deprecated_at = None
    entry.deprecated_by = None
    entry.updated_by = operator_id

    await repo.add_revision(
        db,
        entry_id=entry.id,
        action=REVISION_PUBLISH,
        version_label=entry.version_label,
        status_before=status_before,
        status_after=entry.status,
        snapshot=_snapshot(entry),
        operator_id=operator_id,
        operator_role=operator_role,
        note=note,
    )
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="KNOWLEDGE_ENTRY",
        action="PUBLISH",
        entity_id=entry.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"version_label": entry.version_label, "note": note},
    )
    await db.commit()
    await db.refresh(entry)
    await invalidate_knowledge_cache()
    return entry_to_detail(entry)


async def deprecate_entry(
    db: AsyncSession, entry_id: int, note: str | None, operator_id: int, operator_role: str | None
) -> EntryDetail:
    entry = await repo.get_entry(db, entry_id)
    if entry is None:
        raise NotFoundError("条目不存在")
    status_before = entry.status
    entry.status = ENTRY_STATUS_DEPRECATED
    entry.deprecated_at = datetime.now(UTC)
    entry.deprecated_by = operator_id
    entry.updated_by = operator_id

    await repo.add_revision(
        db,
        entry_id=entry.id,
        action=REVISION_DEPRECATE,
        version_label=entry.version_label,
        status_before=status_before,
        status_after=entry.status,
        snapshot=_snapshot(entry),
        operator_id=operator_id,
        operator_role=operator_role,
        note=note,
    )
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="KNOWLEDGE_ENTRY",
        action="DEPRECATE",
        entity_id=entry.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"note": note},
    )
    await db.commit()
    await db.refresh(entry)
    await invalidate_knowledge_cache()
    return entry_to_detail(entry)


# ---------- 模板 ----------
def normalize_template_tags(raw: list[str] | str | None) -> list[str]:
    if raw is None:
        return []
    values: list[str]
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            values = parsed if isinstance(parsed, list) else [text]
        except json.JSONDecodeError:
            values = text.replace("\n", ",").split(",")
    else:
        values = raw
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        tag = str(value or "").strip()
        if not tag or tag in seen:
            continue
        normalized.append(tag[:64])
        seen.add(tag)
    return normalized


async def upload_template(
    db: AsyncSession,
    *,
    filename: str,
    content: bytes,
    content_type: str,
    template_name: str,
    template_type: str,
    category_code: str | None,
    applicable_scenario: str | None,
    version_label: str | None,
    tags: list[str] | str | None,
    operator_id: int,
    operator_role: str | None,
) -> TemplateAsset:
    max_bytes = settings.UPLOAD_MAX_SIZE_BYTES
    if len(content) > max_bytes:
        raise BizError(
            f"文件超过大小上限 {settings.UPLOAD_MAX_SIZE_MB} MB", code=41300, http_status=413
        )
    checksum = hashlib.sha256(content).hexdigest()
    bucket = settings.MINIO_BUCKET_TEMPLATE
    object_key = f"templates/{uuid.uuid4().hex}_{filename}"
    try:
        put_object(
            bucket=bucket,
            object_key=object_key,
            data=content,
            length=len(content),
            content_type=content_type or "application/octet-stream",
        )
    except Exception as e:
        logger.exception("MinIO 上传失败")
        raise BizError(f"模板上传失败：{e}", code=50002, http_status=500) from e

    row = await repo.create_template(
        db,
        template_name=template_name,
        template_type=template_type,
        category_code=category_code,
        applicable_scenario=applicable_scenario,
        version_label=version_label,
        tags=normalize_template_tags(tags),
        object_bucket=bucket,
        object_key=object_key,
        file_size=len(content),
        mime_type=content_type,
        checksum_sha256=checksum,
        status=TEMPLATE_STATUS_ACTIVE,
        uploaded_by=operator_id,
    )
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="TEMPLATE",
        action="UPLOAD",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"name": template_name, "size": len(content)},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def deprecate_template(
    db: AsyncSession, template_id: int, operator_id: int, operator_role: str | None
) -> TemplateAsset:
    tpl = await repo.get_template(db, template_id)
    if tpl is None:
        raise NotFoundError("模板不存在")
    tpl.status = TEMPLATE_STATUS_DEPRECATED
    tpl.deprecated_at = datetime.now(UTC)
    tpl.deprecated_by = operator_id
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="TEMPLATE",
        action="DEPRECATE",
        entity_id=tpl.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(tpl)
    return tpl


async def template_download_url(
    db: AsyncSession,
    template_id: int,
    operator_id: int | None = None,
    operator_role: str | None = None,
) -> tuple[TemplateAsset, str, int]:
    tpl = await repo.get_template(db, template_id)
    if tpl is None or tpl.status != TEMPLATE_STATUS_ACTIVE:
        raise NotFoundError("模板不存在或已停用")
    expires_minutes = 10
    try:
        url = presigned_get(tpl.object_bucket, tpl.object_key, expires_minutes=expires_minutes)
    except Exception as e:
        raise BizError(f"生成下载链接失败：{e}", code=50003, http_status=500) from e
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="TEMPLATE",
        action="DOWNLOAD",
        entity_id=tpl.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    return tpl, url, expires_minutes


def _template_download_filename(tpl: TemplateAsset) -> str:
    suffix = PurePosixPath(tpl.object_key).suffix
    if suffix and not tpl.template_name.endswith(suffix):
        return f"{tpl.template_name}{suffix}"
    return tpl.template_name


async def template_download_file(
    db: AsyncSession,
    template_id: int,
    operator_id: int | None = None,
    operator_role: str | None = None,
) -> tuple[TemplateAsset, bytes, str, str]:
    tpl = await repo.get_template(db, template_id)
    if tpl is None or tpl.status != TEMPLATE_STATUS_ACTIVE:
        raise NotFoundError("模板不存在或已停用")
    try:
        data = get_object_bytes(tpl.object_bucket, tpl.object_key)
    except Exception as e:
        raise BizError(f"下载模板文件失败：{e}", code=50003, http_status=500) from e
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="TEMPLATE",
        action="DOWNLOAD",
        entity_id=tpl.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"mode": "stream"},
    )
    await db.commit()
    return tpl, data, _template_download_filename(tpl), tpl.mime_type or "application/octet-stream"
