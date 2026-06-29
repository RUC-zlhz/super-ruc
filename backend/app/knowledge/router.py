"""knowledge 路由 — FR-001 / FR-002 / FR-003。

student 侧（前缀 /knowledge）：
- GET /categories           分类列表
- GET /search               搜索已发布条目
- GET /{entry_id}           条目详情
- POST /ai-match            检索式匹配（旧接口名保留）
- GET /templates/{id}/download  模板下载（短期预签名链接）

admin 侧（前缀 /admin/knowledge）：
- Source:   POST / GET /  (以及按 id 查看)
- Entry:    POST / PATCH / publish / deprecate / revisions / GET list
- Template: POST upload (multipart) / GET / DELETE (deprecate)
"""
from __future__ import annotations

from io import BytesIO
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.audit.service import build_audit_detail, log_action
from app.auth.role_codes import ROLE_CODE_COLLABORATOR_ROLES
from app.core.dependencies import CurrentUserDep, DBDep, require_role
from app.core.exceptions import BizError, NotFoundError
from app.core.response import ApiResponse, PageMeta, Paginated, ok
from app.core.uploads import read_upload_file_limited
from app.knowledge import repository as repo
from app.knowledge import service
from app.knowledge.schemas import (
    AiMatchRequest,
    AiMatchResponse,
    CategoryIn,
    CategoryOut,
    EntryBrief,
    EntryCreate,
    EntryDetail,
    EntryStateAction,
    EntryUpdate,
    RevisionOut,
    SourceIn,
    SourceOut,
    SourceUpdate,
    TemplateDownloadLink,
    TemplateOut,
)

# 维护知识内容的角色（L3 及以上）
_KNOWLEDGE_EDITOR_ROLES = (
    "SUPER_ADMIN",
    "COLLEGE_LEADER",
    "COUNSELOR",
    "HEAD_TEACHER",
    "YOUTH_LEAGUE_TEACHER",
    "PARTY_BUILD_TEACHER",
    *ROLE_CODE_COLLABORATOR_ROLES,
)
_EditorRole = require_role(*_KNOWLEDGE_EDITOR_ROLES)
_AdminRole = require_role("SUPER_ADMIN")

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
admin_router = APIRouter(prefix="/admin/knowledge", tags=["knowledge-admin"])


# ========== 学生侧 ==========
@router.get("/categories", response_model=ApiResponse[list[CategoryOut]])
async def list_categories(db: DBDep) -> ApiResponse[list[CategoryOut]]:
    return ok(await service.list_categories_for_student(db))


@router.get("/search", response_model=ApiResponse[Paginated[EntryBrief]])
async def search(
    db: DBDep,
    q: str | None = Query(default=None, description="关键词"),
    category: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[EntryBrief]]:
    items, total = await service.search_for_student(
        db, q=q, category_code=category, tag=tag, page=page, size=size
    )
    return ok(Paginated[EntryBrief](items=items, meta=PageMeta(page=page, size=size, total=total)))


def _template_file_response(data: bytes, filename: str, media_type: str) -> StreamingResponse:
    ascii_filename = "".join(ch if ch.isascii() and ch not in {'"', "\\"} else "_" for ch in filename)
    encoded_filename = quote(filename)
    return StreamingResponse(
        BytesIO(data),
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{encoded_filename}"
            )
        },
    )


@router.get("/templates", response_model=ApiResponse[Paginated[TemplateOut]])
async def list_student_templates(
    db: DBDep,
    _user: CurrentUserDep,
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[TemplateOut]]:
    rows, total = await service.list_templates_for_student(
        db,
        q=q,
        category_code=category,
        page=page,
        size=size,
    )
    items = [TemplateOut.model_validate(row) for row in rows]
    return ok(Paginated[TemplateOut](items=items, meta=PageMeta(page=page, size=size, total=total)))


@router.get("/{entry_id}", response_model=ApiResponse[EntryDetail])
async def get_detail(entry_id: int, db: DBDep) -> ApiResponse[EntryDetail]:
    return ok(await service.get_for_student(db, entry_id))


@router.post("/ai-match", response_model=ApiResponse[AiMatchResponse])
async def ai_match(payload: AiMatchRequest, db: DBDep) -> ApiResponse[AiMatchResponse]:
    return ok(await service.ai_match(db, payload.query, payload.top_k))


@router.get("/templates/{template_id}/download", response_model=ApiResponse[TemplateDownloadLink])
async def download_template(
    template_id: int,
    db: DBDep,
    user: CurrentUserDep,
) -> ApiResponse[TemplateDownloadLink]:
    _, url, minutes = await service.template_download_url(
        db, template_id, operator_id=user.user_id, operator_role=",".join(user.roles)
    )
    return ok(TemplateDownloadLink(template_id=template_id, download_url=url, expires_in_minutes=minutes))


@router.get("/templates/{template_id}/file")
async def download_template_file(
    template_id: int,
    db: DBDep,
    user: CurrentUserDep,
) -> StreamingResponse:
    _, data, filename, media_type = await service.template_download_file(
        db, template_id, operator_id=user.user_id, operator_role=",".join(user.roles)
    )
    return _template_file_response(data, filename, media_type)


# ========== 管理侧：分类 ==========
@admin_router.post("/categories", response_model=ApiResponse[CategoryOut])
async def admin_upsert_category(
    payload: CategoryIn,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[CategoryOut]:
    row = await repo.upsert_category(
        db,
        code=payload.code,
        name=payload.name,
        parent_code=payload.parent_code,
        sort_order=payload.sort_order,
    )
    await db.commit()
    await db.refresh(row)
    await service.invalidate_knowledge_cache()
    return ok(CategoryOut.model_validate(row))


# ========== 管理侧：来源 ==========
def _clean_source_url(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _source_snapshot(row) -> dict:
    return {
        "source_name": row.source_name,
        "source_url": row.source_url,
        "issuing_org": row.issuing_org,
        "version_label": row.version_label,
        "effective_date": row.effective_date.isoformat() if row.effective_date else None,
        "expires_on": row.expires_on.isoformat() if row.expires_on else None,
        "is_official": row.is_official,
        "is_active": row.is_active,
    }


def _source_changes(before: dict, after: dict) -> list[dict]:
    changes: list[dict] = []
    for key, old_value in before.items():
        new_value = after.get(key)
        if old_value != new_value:
            changes.append({"field": key, "before": old_value, "after": new_value})
    return changes


def _assert_official_source_url(*, is_official: bool, source_url: str | None) -> None:
    if is_official and not _clean_source_url(source_url):
        raise BizError("官方知识来源必须填写 source_url", code=40081, http_status=422)


@admin_router.get("/sources", response_model=ApiResponse[list[SourceOut]])
async def admin_list_sources(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
    include_inactive: bool = Query(default=False),
) -> ApiResponse[list[SourceOut]]:
    rows = await repo.list_sources(db, active_only=not include_inactive)
    return ok([SourceOut.model_validate(r) for r in rows])


@admin_router.post("/sources", response_model=ApiResponse[SourceOut])
async def admin_create_source(
    payload: SourceIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[SourceOut]:
    fields = payload.model_dump()
    fields["source_url"] = _clean_source_url(fields.get("source_url"))
    _assert_official_source_url(
        is_official=bool(fields.get("is_official")),
        source_url=fields.get("source_url"),
    )
    row = await repo.create_source(db, **fields)
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="KNOWLEDGE_SOURCE",
        action="CREATE_KNOWLEDGE_SOURCE",
        entity_id=row.id,
        actor_user_id=user.user_id,
        actor_role=",".join(user.roles) or None,
        detail=build_audit_detail(
            target={"source_id": row.id, "source_name": row.source_name},
            refs={"source_url": row.source_url},
            changes={"after": _source_snapshot(row)},
        ),
    )
    await db.commit()
    await db.refresh(row)
    return ok(SourceOut.model_validate(row))


@admin_router.patch("/sources/{source_id}", response_model=ApiResponse[SourceOut])
async def admin_update_source(
    source_id: int,
    payload: SourceUpdate,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[SourceOut]:
    current = await repo.get_source(db, source_id)
    if current is None:
        raise NotFoundError("知识来源不存在")
    before = _source_snapshot(current)
    fields = payload.model_dump(exclude_unset=True)
    if "source_url" in fields:
        fields["source_url"] = _clean_source_url(fields.get("source_url"))
    next_is_official = bool(fields.get("is_official", current.is_official))
    next_source_url = fields.get("source_url", current.source_url)
    _assert_official_source_url(
        is_official=next_is_official,
        source_url=next_source_url,
    )
    row = await repo.update_source(db, source_id, **fields)
    if row is None:
        raise NotFoundError("知识来源不存在")
    after = _source_snapshot(row)
    await log_action(
        db,
        event_type="KNOWLEDGE",
        entity_code="KNOWLEDGE_SOURCE",
        action="UPDATE_KNOWLEDGE_SOURCE",
        entity_id=row.id,
        actor_user_id=user.user_id,
        actor_role=",".join(user.roles) or None,
        detail=build_audit_detail(
            target={"source_id": row.id, "source_name": row.source_name},
            refs={"source_url": row.source_url},
            changes=_source_changes(before, after),
        ),
    )
    await db.commit()
    await db.refresh(row)
    return ok(SourceOut.model_validate(row))


# ========== 管理侧：条目 ==========
@admin_router.get("/entries", response_model=ApiResponse[Paginated[EntryBrief]])
async def admin_list_entries(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
    q: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[EntryBrief]]:
    rows, total = await repo.list_all_entries_admin(db, q=q, status=status, page=page, size=size)
    items = [service.entry_to_brief(r) for r in rows]
    return ok(Paginated[EntryBrief](items=items, meta=PageMeta(page=page, size=size, total=total)))


@admin_router.get("/entries/{entry_id}", response_model=ApiResponse[EntryDetail])
async def admin_get_entry(
    entry_id: int,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[EntryDetail]:
    return ok(await service.get_for_admin(db, entry_id))


@admin_router.post("/entries", response_model=ApiResponse[EntryDetail])
async def admin_create_entry(
    payload: EntryCreate,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[EntryDetail]:
    detail = await service.create_entry(
        db, payload, operator_id=user.user_id, operator_role=",".join(user.roles) or None
    )
    return ok(detail)


@admin_router.patch("/entries/{entry_id}", response_model=ApiResponse[EntryDetail])
async def admin_update_entry(
    entry_id: int,
    payload: EntryUpdate,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[EntryDetail]:
    detail = await service.update_entry(
        db, entry_id, payload, operator_id=user.user_id, operator_role=",".join(user.roles) or None
    )
    return ok(detail)


@admin_router.post("/entries/{entry_id}/publish", response_model=ApiResponse[EntryDetail])
async def admin_publish_entry(
    entry_id: int,
    payload: EntryStateAction,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[EntryDetail]:
    detail = await service.publish_entry(
        db, entry_id, payload.note, operator_id=user.user_id, operator_role=",".join(user.roles) or None
    )
    return ok(detail)


@admin_router.post("/entries/{entry_id}/deprecate", response_model=ApiResponse[EntryDetail])
async def admin_deprecate_entry(
    entry_id: int,
    payload: EntryStateAction,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[EntryDetail]:
    detail = await service.deprecate_entry(
        db, entry_id, payload.note, operator_id=user.user_id, operator_role=",".join(user.roles) or None
    )
    return ok(detail)


@admin_router.get("/entries/{entry_id}/revisions", response_model=ApiResponse[list[RevisionOut]])
async def admin_list_revisions(
    entry_id: int,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[list[RevisionOut]]:
    rows = await repo.list_entry_revisions(db, entry_id)
    return ok([RevisionOut.model_validate(r) for r in rows])


# ========== 管理侧：模板 ==========
@admin_router.get("/templates", response_model=ApiResponse[Paginated[TemplateOut]])
async def admin_list_templates(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
    category: str | None = None,
    q: str | None = None,
    include_deprecated: bool = False,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[TemplateOut]]:
    rows, total = await repo.list_templates(
        db,
        category_code=category,
        q=q,
        include_deprecated=include_deprecated,
        page=page,
        size=size,
    )
    items = [TemplateOut.model_validate(r) for r in rows]
    return ok(Paginated[TemplateOut](items=items, meta=PageMeta(page=page, size=size, total=total)))


@admin_router.post("/templates", response_model=ApiResponse[TemplateOut])
async def admin_upload_template(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
    template_name: Annotated[str, Form()],
    template_type: Annotated[str, Form(description="DOC/DOCX/XLSX/PDF/OTHER")],
    file: Annotated[UploadFile, File()],
    category_code: Annotated[str | None, Form()] = None,
    applicable_scenario: Annotated[str | None, Form()] = None,
    version_label: Annotated[str | None, Form()] = None,
    tags: Annotated[str | None, Form()] = None,
) -> ApiResponse[TemplateOut]:
    content = await read_upload_file_limited(file)
    row = await service.upload_template(
        db,
        filename=file.filename or "template.bin",
        content=content,
        content_type=file.content_type or "application/octet-stream",
        template_name=template_name,
        template_type=template_type,
        category_code=category_code,
        applicable_scenario=applicable_scenario,
        version_label=version_label,
        tags=tags,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(TemplateOut.model_validate(row))


@admin_router.delete("/templates/{template_id}", response_model=ApiResponse[TemplateOut])
async def admin_deprecate_template(
    template_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[TemplateOut]:
    row = await service.deprecate_template(
        db, template_id, operator_id=user.user_id, operator_role=",".join(user.roles) or None
    )
    return ok(TemplateOut.model_validate(row))


@admin_router.get("/templates/{template_id}/download", response_model=ApiResponse[TemplateDownloadLink])
async def admin_download_template(
    template_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[TemplateDownloadLink]:
    _, url, minutes = await service.template_download_url(
        db,
        template_id,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(TemplateDownloadLink(template_id=template_id, download_url=url, expires_in_minutes=minutes))


@admin_router.get("/templates/{template_id}/file")
async def admin_download_template_file(
    template_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> StreamingResponse:
    _, data, filename, media_type = await service.template_download_file(
        db,
        template_id,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return _template_file_response(data, filename, media_type)
