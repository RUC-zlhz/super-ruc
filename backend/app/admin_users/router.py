"""Admin backend-account bulk import endpoints."""
from __future__ import annotations

from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.admin_users import repository as repo
from app.admin_users import service
from app.admin_users.schemas import (
    AdminUserImportBatchBrief,
    AdminUserImportBatchDetail,
    AdminUserImportCommitIn,
    AdminUserImportCommitResult,
    AdminUserImportPreviewResult,
    AdminUserImportRowOut,
)
from app.core.dependencies import CurrentUserDep, DBDep, require_role
from app.core.response import ApiResponse, PageMeta, Paginated, ok

_IMPORT_ROLES = tuple(sorted(service.IMPORTER_ROLES))
_ImporterRole = require_role(*_IMPORT_ROLES)

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def _file_response(data: bytes, filename: str, media_type: str) -> StreamingResponse:
    return StreamingResponse(
        BytesIO(data),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/import-template")
async def download_import_template(
    user: Annotated[CurrentUserDep, Depends(_ImporterRole)],
    format: str = Query(default="xlsx", pattern="^(xlsx|csv)$"),
) -> StreamingResponse:
    service.ensure_import_permission(user.roles)
    data, filename, media_type = service.build_template_file(format)
    return _file_response(data, filename, media_type)


@router.post(
    "/import-preview",
    response_model=ApiResponse[AdminUserImportPreviewResult],
)
async def import_preview(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_ImporterRole)],
    file: Annotated[UploadFile, File()],
) -> ApiResponse[AdminUserImportPreviewResult]:
    content = await file.read()
    batch = await service.preview_import(
        db,
        filename=file.filename or "admin-users.xlsx",
        file_bytes=content,
        mime_type=file.content_type,
        actor_user_id=user.user_id,
        actor_roles=user.roles,
    )
    rows = await repo.list_batch_rows(db, batch.id, limit=500)
    return ok(
        AdminUserImportPreviewResult(
            batch=AdminUserImportBatchDetail.model_validate(batch),
            rows=[AdminUserImportRowOut.model_validate(row) for row in rows],
        )
    )


@router.post(
    "/import-commit",
    response_model=ApiResponse[AdminUserImportCommitResult],
)
async def import_commit(
    payload: AdminUserImportCommitIn,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_ImporterRole)],
) -> ApiResponse[AdminUserImportCommitResult]:
    batch, credentials = await service.commit_import(
        db,
        batch_id=payload.batch_id,
        actor_user_id=user.user_id,
        actor_roles=user.roles,
        note=payload.note,
    )
    rows = await repo.list_batch_rows(db, batch.id, limit=500)
    return ok(
        AdminUserImportCommitResult(
            batch=AdminUserImportBatchDetail.model_validate(batch),
            rows=[AdminUserImportRowOut.model_validate(row) for row in rows],
            credentials=credentials,
        )
    )


@router.get(
    "/imports",
    response_model=ApiResponse[Paginated[AdminUserImportBatchBrief]],
)
async def list_imports(
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_ImporterRole)],
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[Paginated[AdminUserImportBatchBrief]]:
    service.ensure_import_permission(user.roles)
    rows, total = await repo.list_batches(db, page=page, size=size)
    return ok(
        Paginated[AdminUserImportBatchBrief](
            items=[AdminUserImportBatchBrief.model_validate(row) for row in rows],
            meta=PageMeta(page=page, size=size, total=total),
        )
    )


@router.get(
    "/imports/{batch_id}",
    response_model=ApiResponse[AdminUserImportPreviewResult],
)
async def get_import(
    batch_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_ImporterRole)],
) -> ApiResponse[AdminUserImportPreviewResult]:
    service.ensure_import_permission(user.roles)
    batch = await repo.get_batch(db, batch_id)
    if batch is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("批次不存在")
    rows = await repo.list_batch_rows(db, batch.id, limit=1000)
    return ok(
        AdminUserImportPreviewResult(
            batch=AdminUserImportBatchDetail.model_validate(batch),
            rows=[AdminUserImportRowOut.model_validate(row) for row in rows],
        )
    )


@router.get("/imports/{batch_id}/error-report")
async def download_error_report(
    batch_id: int,
    db: DBDep,
    user: Annotated[CurrentUserDep, Depends(_ImporterRole)],
) -> StreamingResponse:
    service.ensure_import_permission(user.roles)
    data, filename = await service.build_error_report(db, batch_id)
    return _file_response(
        data,
        filename,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
