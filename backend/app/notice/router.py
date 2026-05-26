"""notice 路由 — FR-010 / FR-011。

学生侧（/notices）：
- GET /inbox                查看本人收件箱
- POST /read/{delivery_id}  标记已读
- GET /{notice_id}          详情（必须是投递给本人的）

管理侧（/admin/notices）：
- GET / POST / PATCH / 发布 / 归档
- POST /target-preview      目标人群预览（FR-010 发送前确认）
- POST /{notice_id}/dispatch  发送批次（FR-011）
- GET /{notice_id}/batches
- GET /batches/{batch_id}/deliveries
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.auth.models import User
from app.auth.role_codes import ROLE_CODE_COLLABORATOR_ROLES
from app.core.dependencies import CurrentUserDep, DBDep, require_role
from app.core.exceptions import BizError, NotFoundError
from app.core.response import ApiResponse, PageMeta, Paginated, ok
from app.notice import repository as repo
from app.notice import service
from app.notice.schemas import (
    DeliveryDispatchIn,
    NoticeBatchOut,
    NoticeBrief,
    NoticeDeliveryOut,
    NoticeDeliveryReceiptMockIn,
    NoticeIn,
    NoticeIngestRunOut,
    NoticeOut,
    NoticeSourceIn,
    NoticeSourceOut,
    NoticeSourcePatchIn,
    StudentNoticeItem,
    TargetPreviewRequest,
    TargetPreviewResult,
    WechatSubscribeAuthorizationIn,
    WechatSubscribeAuthorizationOut,
    WechatSubscribeConfigOut,
)

_NOTICE_EDITOR_ROLES = (
    "SUPER_ADMIN",
    "COLLEGE_LEADER",
    "COUNSELOR",
    "HEAD_TEACHER",
    "YOUTH_LEAGUE_TEACHER",
    "PARTY_BUILD_TEACHER",
    *ROLE_CODE_COLLABORATOR_ROLES,
)
_EditorRole = require_role(*_NOTICE_EDITOR_ROLES)

router = APIRouter(prefix="/notices", tags=["notice"])
admin_router = APIRouter(prefix="/admin/notices", tags=["notice-admin"])


# ========= 学生侧 =========
@router.get("/inbox", response_model=ApiResponse[Paginated[StudentNoticeItem]])
async def my_inbox(
    db: DBDep,
    user: CurrentUserDep,
    unread_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[StudentNoticeItem]]:
    if user.student_id is None:
        raise BizError("仅学生有通知收件箱", code=40305, http_status=403)
    items, total = await service.list_student_inbox(
        db, user.user_id, user.student_id,
        unread_only=unread_only, page=page, size=size,
    )
    return ok(Paginated[StudentNoticeItem](
        items=items, meta=PageMeta(page=page, size=size, total=total)
    ))


@router.post("/read/{delivery_id}", response_model=ApiResponse[dict])
async def mark_read(
    delivery_id: int, db: DBDep, user: CurrentUserDep
) -> ApiResponse[dict]:
    if user.student_id is None:
        raise BizError("仅学生可标记已读", code=40305, http_status=403)
    await service.mark_read(db, delivery_id, user.student_id)
    return ok({"delivery_id": delivery_id, "status": "READ"})


@router.get(
    "/subscribe-config",
    response_model=ApiResponse[WechatSubscribeConfigOut],
)
async def get_subscribe_config(
    _db: DBDep,
    _user: CurrentUserDep,
) -> ApiResponse[WechatSubscribeConfigOut]:
    return ok(service.get_wechat_subscribe_config())


@router.post(
    "/subscribe-authorizations",
    response_model=ApiResponse[list[WechatSubscribeAuthorizationOut]],
)
async def save_subscribe_authorizations(
    payload: WechatSubscribeAuthorizationIn,
    db: DBDep,
    user: CurrentUserDep,
) -> ApiResponse[list[WechatSubscribeAuthorizationOut]]:
    user_row = await db.get(User, user.user_id)
    if user_row is None:
        raise BizError("当前账号不存在", code=40305, http_status=403)
    saved = await service.save_wechat_subscribe_authorizations(
        db,
        user=user_row,
        results=[(item.template_id, item.status) for item in payload.results],
    )
    return ok(saved)


@router.get("/{notice_id}", response_model=ApiResponse[NoticeOut])
async def get_notice(
    notice_id: int, db: DBDep, user: CurrentUserDep
) -> ApiResponse[NoticeOut]:
    notice = await repo.get_notice(db, notice_id)
    if notice is None:
        raise NotFoundError("通知不存在")
    editor_roles = set(_NOTICE_EDITOR_ROLES)
    is_editor = bool(set(user.roles) & editor_roles)
    if not is_editor:
        if user.student_id is None:
            raise BizError("无权查看该通知", code=40301, http_status=403)
        if notice.status != "PUBLISHED":
            raise NotFoundError("通知不存在或未发布")
        has_delivery = await repo.student_has_notice_delivery(
            db,
            notice_id,
            user.student_id,
            channel="IN_APP",
        )
        if not has_delivery:
            raise NotFoundError("通知不存在或未投递给当前学生")
    return ok(service.notice_to_out(notice))


# ========= 管理侧 =========
@admin_router.get("", response_model=ApiResponse[Paginated[NoticeBrief]])
async def admin_list_notices(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
    q: str | None = None,
    status: str | None = None,
    category: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[NoticeBrief]]:
    rows, total = await repo.list_notices_admin(
        db, q=q, status=status, category=category, page=page, size=size
    )
    items = [service.notice_to_brief(r) for r in rows]
    return ok(Paginated[NoticeBrief](items=items, meta=PageMeta(page=page, size=size, total=total)))


@admin_router.post("", response_model=ApiResponse[NoticeOut])
async def admin_create_notice(
    payload: NoticeIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[NoticeOut]:
    return ok(await service.create_notice(
        db, payload, user.user_id, ",".join(user.roles) or None
    ))


@admin_router.patch("/{notice_id}", response_model=ApiResponse[NoticeOut])
async def admin_update_notice(
    notice_id: int,
    payload: NoticeIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[NoticeOut]:
    return ok(await service.update_notice(
        db, notice_id, payload, user.user_id, ",".join(user.roles) or None
    ))


@admin_router.post("/{notice_id}/publish", response_model=ApiResponse[NoticeOut])
async def admin_publish_notice(
    notice_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[NoticeOut]:
    return ok(await service.publish_notice(
        db, notice_id, user.user_id, ",".join(user.roles) or None
    ))


@admin_router.post("/{notice_id}/archive", response_model=ApiResponse[NoticeOut])
async def admin_archive_notice(
    notice_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[NoticeOut]:
    return ok(await service.archive_notice(
        db, notice_id, user.user_id, ",".join(user.roles) or None
    ))


@admin_router.post("/target-preview", response_model=ApiResponse[TargetPreviewResult])
async def admin_preview_target(
    payload: TargetPreviewRequest,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[TargetPreviewResult]:
    return ok(await service.preview_target(
        db, 
        payload.target_rule,
        viewer_user_id=user.user_id,
        viewer_roles=user.roles,
    ))


@admin_router.post("/{notice_id}/dispatch", response_model=ApiResponse[NoticeBatchOut])
async def admin_dispatch(
    notice_id: int,
    payload: DeliveryDispatchIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[NoticeBatchOut]:
    batch = await service.dispatch_notice(
        db, notice_id,
        override_channels=payload.channels,
        note=payload.note,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
        operator_roles=user.roles,
    )
    return ok(NoticeBatchOut.model_validate(batch))


@admin_router.get("/{notice_id}/batches", response_model=ApiResponse[list[NoticeBatchOut]])
async def admin_list_batches(
    notice_id: int,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[list[NoticeBatchOut]]:
    rows = await repo.list_batches_for_notice(db, notice_id)
    return ok([NoticeBatchOut.model_validate(r) for r in rows])


@admin_router.get("/batches/{batch_id}/deliveries",
                  response_model=ApiResponse[Paginated[NoticeDeliveryOut]])
async def admin_list_deliveries(
    batch_id: int,
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
    status: str | None = None,
    channel: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=500),
) -> ApiResponse[Paginated[NoticeDeliveryOut]]:
    rows, total = await repo.list_deliveries_for_batch(
        db, batch_id, status=status, channel=channel, page=page, size=size
    )
    items = [NoticeDeliveryOut.model_validate(r) for r in rows]
    return ok(Paginated[NoticeDeliveryOut](
        items=items, meta=PageMeta(page=page, size=size, total=total)
    ))


@admin_router.get("/sources", response_model=ApiResponse[Paginated[NoticeSourceOut]])
async def admin_list_notice_sources(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
    is_active: bool | None = None,
    source_type: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[NoticeSourceOut]]:
    rows, total = await repo.list_notice_sources(
        db, is_active=is_active, source_type=source_type, page=page, size=size
    )
    return ok(Paginated[NoticeSourceOut](
        items=[service.source_to_out(row) for row in rows],
        meta=PageMeta(page=page, size=size, total=total),
    ))


@admin_router.post("/sources", response_model=ApiResponse[NoticeSourceOut])
async def admin_create_notice_source(
    payload: NoticeSourceIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[NoticeSourceOut]:
    return ok(await service.create_notice_source(
        db,
        payload,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    ))


@admin_router.patch("/sources/{source_id}", response_model=ApiResponse[NoticeSourceOut])
async def admin_update_notice_source(
    source_id: int,
    payload: NoticeSourcePatchIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[NoticeSourceOut]:
    return ok(await service.update_notice_source(
        db,
        source_id,
        payload,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    ))


@admin_router.post("/sources/{source_id}/run", response_model=ApiResponse[NoticeIngestRunOut])
async def admin_run_notice_source(
    source_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[NoticeIngestRunOut]:
    return ok(await service.run_notice_source_ingest(
        db,
        source_id,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    ))


@admin_router.get("/ingest-runs", response_model=ApiResponse[Paginated[NoticeIngestRunOut]])
async def admin_list_ingest_runs(
    db: DBDep,
    _user: Annotated[CurrentUserDep, Depends(_EditorRole)],
    source_id: int | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[NoticeIngestRunOut]]:
    rows, total = await repo.list_ingest_runs(
        db, source_id=source_id, status=status, page=page, size=size
    )
    return ok(Paginated[NoticeIngestRunOut](
        items=[service.ingest_run_to_out(row) for row in rows],
        meta=PageMeta(page=page, size=size, total=total),
    ))


@admin_router.post("/deliveries/{delivery_id}/retry", response_model=ApiResponse[NoticeDeliveryOut])
async def admin_retry_delivery(
    delivery_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[NoticeDeliveryOut]:
    row = await service.retry_notice_delivery(
        db,
        delivery_id,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(NoticeDeliveryOut.model_validate(row))


@admin_router.post(
    "/deliveries/{delivery_id}/receipt/mock",
    response_model=ApiResponse[dict],
)
async def admin_mock_delivery_receipt(
    delivery_id: int,
    payload: NoticeDeliveryReceiptMockIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_EditorRole)],
) -> ApiResponse[dict]:
    attempt = await service.mock_delivery_receipt(
        db,
        delivery_id,
        receipt_status=payload.receipt_status,
        operator_id=user.user_id,
        operator_role=",".join(user.roles) or None,
    )
    return ok(attempt.model_dump())
