"""notice 业务服务层 — 发布 / 目标解析 / 多通道发送（mock）。

发送策略：
- IN_APP: 直接在 notice_deliveries 插记录，学生端拉取即可。
- EMAIL: 调用 SMTP（此处预留接口，失败写 error_*）。
- SMS: 仅在 settings.SMS_ENABLED=True 时尝试；否则标记为 SKIPPED。
"""
from __future__ import annotations

import logging
import smtplib
import uuid
from datetime import UTC, datetime, timedelta
from email.mime.text import MIMEText
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_action
from app.auth.models import Student, User
from app.core.config import settings
from app.core.exceptions import BizError, ConflictError, NotFoundError
from app.core.security import decrypt_field, mask_phone
from app.notice import repository as repo
from app.notice.models import (
    CHANNEL_EMAIL,
    CHANNEL_IN_APP,
    CHANNEL_SMS,
    CHANNEL_WECHAT_SUBSCRIBE,
    DELIVERY_ATTEMPT_STATUS_FAILED,
    DELIVERY_ATTEMPT_STATUS_SENT,
    DELIVERY_ATTEMPT_STATUS_SKIPPED,
    DELIVERY_STATUS_FAILED,
    DELIVERY_STATUS_SENT,
    DELIVERY_STATUS_SKIPPED,
    INGEST_RUN_STATUS_FAILED,
    INGEST_RUN_STATUS_PARTIAL,
    INGEST_RUN_STATUS_SUCCESS,
    NOTICE_SOURCE_TYPE_RSS,
    NOTICE_SOURCE_TYPE_URL,
    NOTICE_STATUS_ARCHIVED,
    NOTICE_STATUS_DRAFT,
    NOTICE_STATUS_PUBLISHED,
    WECHAT_SUBSCRIBE_SCENE_REQUEST_STATUS,
    WECHAT_SUBSCRIBE_SCENE_WORKFLOW_REMINDER,
    WECHAT_SUBSCRIBE_STATUS_ACCEPT,
    Notice,
    NoticeDelivery,
    NoticeDeliveryBatch,
    NoticeIngestRun,
    NoticeSource,
)
from app.notice.schemas import (
    NoticeBrief,
    NoticeDeliveryAttemptOut,
    NoticeIn,
    NoticeIngestRunOut,
    NoticeOut,
    NoticeSourceIn,
    NoticeSourceOut,
    NoticeSourcePatchIn,
    StudentNoticeItem,
    TargetPreviewResult,
    TargetRule,
    WechatSubscribeAuthorizationOut,
    WechatSubscribeConfigOut,
    WechatSubscribeTemplateOut,
)

logger = logging.getLogger(__name__)

WX_ACCESS_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"  # noqa: S105 - official API path.
WX_SUBSCRIBE_SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/subscribe/send"
WECHAT_SUBSCRIBE_PROVIDER = "wechat_subscribe"

_wechat_access_token: str | None = None
_wechat_access_token_expires_at: datetime | None = None


def _channels_to_str(items: list[str]) -> str:
    return ",".join([c.strip().upper() for c in items if c and c.strip()])


def _str_to_channels(s: str | None) -> list[str]:
    if not s:
        return []
    return [c.strip().upper() for c in s.split(",") if c.strip()]


def _wechat_subscribe_templates() -> list[WechatSubscribeTemplateOut]:
    if not settings.WECHAT_SUBSCRIBE_ENABLED:
        return []
    templates: list[WechatSubscribeTemplateOut] = []
    if settings.WECHAT_SUBSCRIBE_REMINDER_TEMPLATE_ID:
        templates.append(
            WechatSubscribeTemplateOut(
                scene=WECHAT_SUBSCRIBE_SCENE_WORKFLOW_REMINDER,
                template_id=settings.WECHAT_SUBSCRIBE_REMINDER_TEMPLATE_ID,
            )
        )
    if settings.WECHAT_SUBSCRIBE_REQUEST_TEMPLATE_ID:
        templates.append(
            WechatSubscribeTemplateOut(
                scene=WECHAT_SUBSCRIBE_SCENE_REQUEST_STATUS,
                template_id=settings.WECHAT_SUBSCRIBE_REQUEST_TEMPLATE_ID,
            )
        )
    return templates


def _wechat_scene_for_template(template_id: str) -> str | None:
    for template in _wechat_subscribe_templates():
        if template.template_id == template_id:
            return template.scene
    return None


def get_wechat_subscribe_config() -> WechatSubscribeConfigOut:
    templates = _wechat_subscribe_templates()
    return WechatSubscribeConfigOut(enabled=bool(templates), templates=templates)


async def save_wechat_subscribe_authorizations(
    db: AsyncSession,
    *,
    user: User,
    results: list[tuple[str, str]],
) -> list[WechatSubscribeAuthorizationOut]:
    if not settings.WECHAT_SUBSCRIBE_ENABLED:
        return []
    if not user.openid:
        raise BizError("当前账号未绑定微信 openid，无法保存订阅授权", code=40085)
    saved: list[WechatSubscribeAuthorizationOut] = []
    for template_id, status in results:
        scene = _wechat_scene_for_template(template_id)
        if scene is None:
            continue
        row = await repo.upsert_wechat_subscribe_authorization(
            db,
            user_id=user.id,
            student_id=user.student_id,
            openid=user.openid,
            template_id=template_id,
            scene=scene,
            status=status,
        )
        saved.append(
            WechatSubscribeAuthorizationOut(
                template_id=row.template_id,
                scene=row.scene,
                status=row.status,
            )
        )
    await db.commit()
    return saved


def notice_to_out(notice: Notice) -> NoticeOut:
    return NoticeOut(
        id=notice.id,
        title=notice.title,
        body_md=notice.body_md,
        summary=notice.summary,
        category=notice.category,
        status=notice.status,
        source_type=notice.source_type,
        source_url=notice.source_url,
        channels=notice.channels,
        target_rule=notice.target_rule,
        target_summary=notice.target_summary,
        effective_start=notice.effective_start,
        effective_end=notice.effective_end,
        is_pinned=notice.is_pinned,
        published_at=notice.published_at,
        updated_at=notice.updated_at,
        tags=[t.tag for t in (notice.tags or [])],
    )


def notice_to_brief(notice: Notice) -> NoticeBrief:
    return NoticeBrief(
        id=notice.id,
        title=notice.title,
        summary=notice.summary,
        category=notice.category,
        status=notice.status,
        source_type=notice.source_type,
        channels=notice.channels,
        target_summary=notice.target_summary,
        is_pinned=notice.is_pinned,
        published_at=notice.published_at,
        updated_at=notice.updated_at,
        tags=[t.tag for t in (notice.tags or [])],
    )


def source_to_out(source: NoticeSource) -> NoticeSourceOut:
    return NoticeSourceOut.model_validate(source)


def ingest_run_to_out(run: NoticeIngestRun) -> NoticeIngestRunOut:
    return NoticeIngestRunOut.model_validate(run)


def _normalize_source_type(value: str) -> str:
    normalized = (value or "").strip().upper()
    if normalized not in {NOTICE_SOURCE_TYPE_URL, NOTICE_SOURCE_TYPE_RSS}:
        raise BizError("通知抓取来源仅支持公开 URL/RSS", code=40080)
    return normalized


def _ensure_public_http_url(value: str) -> str:
    url = (value or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise BizError("抓取来源必须是公开 http/https URL", code=40081)
    return url


# ---------- Target preview ----------
async def preview_target(
    db: AsyncSession, rule: TargetRule | None
) -> TargetPreviewResult:
    rule_dict = rule.model_dump() if rule else None
    students = await repo.resolve_target_students(db, rule_dict)
    return TargetPreviewResult(
        target_count=len(students),
        sample_student_nos=[s.student_no for s in students[:10]],
    )


# ---------- CRUD ----------
async def create_notice(
    db: AsyncSession, payload: NoticeIn, operator_id: int, operator_role: str | None
) -> NoticeOut:
    row = await repo.create_notice(
        db,
        title=payload.title,
        body_md=payload.body_md,
        summary=payload.summary,
        category=payload.category,
        status=NOTICE_STATUS_DRAFT,
        source_type=payload.source_type,
        source_url=payload.source_url,
        target_rule=payload.target_rule.model_dump() if payload.target_rule else None,
        target_summary=payload.target_summary,
        channels=_channels_to_str(payload.channels) or CHANNEL_IN_APP,
        effective_start=payload.effective_start,
        effective_end=payload.effective_end,
        is_pinned=payload.is_pinned,
        created_by=operator_id,
        updated_by=operator_id,
    )
    await repo.set_notice_tags(db, row.id, payload.tags)
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE",
        action="CREATE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return notice_to_out(row)


async def create_notice_source(
    db: AsyncSession,
    payload: NoticeSourceIn,
    *,
    operator_id: int,
    operator_role: str | None,
) -> NoticeSourceOut:
    row = await repo.create_notice_source(
        db,
        name=payload.name.strip(),
        source_type=_normalize_source_type(payload.source_type),
        source_url=_ensure_public_http_url(payload.source_url),
        category=payload.category,
        target_rule=payload.target_rule.model_dump() if payload.target_rule else None,
        is_active=payload.is_active,
        created_by=operator_id,
        updated_by=operator_id,
    )
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE_SOURCE",
        action="CREATE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return source_to_out(row)


async def update_notice_source(
    db: AsyncSession,
    source_id: int,
    payload: NoticeSourcePatchIn,
    *,
    operator_id: int,
    operator_role: str | None,
) -> NoticeSourceOut:
    row = await repo.get_notice_source(db, source_id)
    if row is None:
        raise NotFoundError("通知抓取来源不存在")
    updates = payload.model_dump(exclude_unset=True)
    if "source_type" in updates and updates["source_type"] is not None:
        updates["source_type"] = _normalize_source_type(updates["source_type"])
    if "source_url" in updates and updates["source_url"] is not None:
        updates["source_url"] = _ensure_public_http_url(updates["source_url"])
    if "target_rule" in updates:
        target_rule = updates["target_rule"]
        updates["target_rule"] = target_rule.model_dump() if target_rule else None
    for key, value in updates.items():
        setattr(row, key, value)
    row.updated_by = operator_id
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE_SOURCE",
        action="UPDATE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return source_to_out(row)


async def update_notice(
    db: AsyncSession,
    notice_id: int,
    payload: NoticeIn,
    operator_id: int,
    operator_role: str | None,
) -> NoticeOut:
    row = await repo.get_notice(db, notice_id)
    if row is None:
        raise NotFoundError("通知不存在")
    if row.status == NOTICE_STATUS_ARCHIVED:
        raise BizError("已归档通知不可编辑", code=40030)

    row.title = payload.title
    row.body_md = payload.body_md
    row.summary = payload.summary
    row.category = payload.category
    row.source_type = payload.source_type
    row.source_url = payload.source_url
    row.target_rule = payload.target_rule.model_dump() if payload.target_rule else None
    row.target_summary = payload.target_summary
    row.channels = _channels_to_str(payload.channels) or row.channels
    row.effective_start = payload.effective_start
    row.effective_end = payload.effective_end
    row.is_pinned = payload.is_pinned
    row.updated_by = operator_id

    await repo.set_notice_tags(db, row.id, payload.tags)
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE",
        action="UPDATE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return notice_to_out(row)


async def publish_notice(
    db: AsyncSession, notice_id: int, operator_id: int, operator_role: str | None
) -> NoticeOut:
    row = await repo.get_notice(db, notice_id)
    if row is None:
        raise NotFoundError("通知不存在")
    if row.status == NOTICE_STATUS_PUBLISHED:
        raise ConflictError("通知已发布")
    if row.status == NOTICE_STATUS_ARCHIVED:
        raise BizError("已归档通知不可重新发布", code=40031)

    row.status = NOTICE_STATUS_PUBLISHED
    row.published_at = datetime.now(UTC)
    row.published_by = operator_id
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE",
        action="PUBLISH",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return notice_to_out(row)


async def archive_notice(
    db: AsyncSession, notice_id: int, operator_id: int, operator_role: str | None
) -> NoticeOut:
    row = await repo.get_notice(db, notice_id)
    if row is None:
        raise NotFoundError("通知不存在")
    if row.status == NOTICE_STATUS_ARCHIVED:
        return notice_to_out(row)
    row.status = NOTICE_STATUS_ARCHIVED
    row.archived_at = datetime.now(UTC)
    row.archived_by = operator_id
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE",
        action="ARCHIVE",
        entity_id=row.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return notice_to_out(row)


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self.title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data.strip())

    @property
    def title(self) -> str | None:
        text = " ".join(part for part in self.title_parts if part).strip()
        return text or None


def _extract_rss_items(content: bytes, fallback_url: str) -> list[dict[str, str | None]]:
    root = ET.fromstring(content)  # noqa: S314 - Sources are admin-configured public RSS URLs.
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    parsed: list[dict[str, str | None]] = []
    for item in items[:50]:
        title = item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title")
        link = item.findtext("link")
        if link is None:
            atom_link = item.find("{http://www.w3.org/2005/Atom}link")
            if atom_link is not None:
                link = atom_link.attrib.get("href")
        summary = (
            item.findtext("description")
            or item.findtext("summary")
            or item.findtext("{http://www.w3.org/2005/Atom}summary")
        )
        parsed.append(
            {
                "title": (title or "未命名通知").strip(),
                "source_url": (link or fallback_url).strip(),
                "summary": (summary or "").strip() or None,
            }
        )
    return parsed


def _extract_url_item(content: bytes, source_url: str) -> list[dict[str, str | None]]:
    parser = _TitleParser()
    try:
        parser.feed(content[:256 * 1024].decode("utf-8", errors="ignore"))
    except Exception as exc:  # noqa: BLE001
        logger.debug("failed to parse notice source title url=%s error=%s", source_url, exc)
    title = parser.title or source_url
    return [{"title": title[:256], "source_url": source_url, "summary": None}]


async def run_notice_source_ingest(
    db: AsyncSession,
    source_id: int,
    *,
    operator_id: int,
    operator_role: str | None,
) -> NoticeIngestRunOut:
    source = await repo.get_notice_source(db, source_id)
    if source is None:
        raise NotFoundError("通知抓取来源不存在")
    if not source.is_active:
        raise BizError("通知抓取来源已停用", code=40082)

    started_at = datetime.now(UTC)
    run = await repo.create_ingest_run(
        db,
        source_id=source.id,
        status=INGEST_RUN_STATUS_SUCCESS,
        started_at=started_at,
        created_by=operator_id,
    )
    fetched = created = skipped = 0
    error_message: str | None = None
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(source.source_url)
            response.raise_for_status()
        content = response.content
        if source.source_type == NOTICE_SOURCE_TYPE_RSS:
            items = _extract_rss_items(content, source.source_url)
        else:
            items = _extract_url_item(content, source.source_url)
        fetched = len(items)
        for item in items:
            item_url = _ensure_public_http_url(item["source_url"] or source.source_url)
            if await repo.get_notice_by_source_url(db, item_url):
                skipped += 1
                continue
            summary = item.get("summary")
            body = (summary or item["title"] or "抓取通知").strip()
            body_md = f"{body}\n\n来源链接：{item_url}"
            await repo.create_notice(
                db,
                title=(item["title"] or "抓取通知")[:256],
                body_md=body_md,
                summary=(summary or item["title"])[:512] if (summary or item["title"]) else None,
                category=source.category,
                status=NOTICE_STATUS_DRAFT,
                source_type="INGESTED",
                source_url=item_url,
                target_rule=source.target_rule,
                target_summary="抓取来源生成草稿，需管理员审核后发布",
                channels=CHANNEL_IN_APP,
                created_by=operator_id,
                updated_by=operator_id,
            )
            created += 1
    except Exception as exc:  # noqa: BLE001
        error_message = str(exc)[:512]
        logger.warning("notice source ingest failed source_id=%s error=%s", source.id, error_message)

    run.fetched_count = fetched
    run.created_count = created
    run.skipped_count = skipped
    run.error_message = error_message
    run.finished_at = datetime.now(UTC)
    if error_message:
        run.status = INGEST_RUN_STATUS_FAILED if created == 0 else INGEST_RUN_STATUS_PARTIAL
    else:
        run.status = INGEST_RUN_STATUS_SUCCESS
    source.last_run_at = run.finished_at
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE_SOURCE",
        action="INGEST_RUN",
        entity_id=source.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={
            "run_id": run.id,
            "fetched": fetched,
            "created": created,
            "skipped": skipped,
            "status": run.status,
        },
    )
    await db.commit()
    await db.refresh(run)
    return ingest_run_to_out(run)


# ---------- Dispatch ----------
def _send_email(to_addr: str, subject: str, body: str) -> tuple[bool, str | None]:
    """简化：直接 SMTP。生产环境应走任务队列。"""
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_addr
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
            if settings.SMTP_USER:
                s.starttls()
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.sendmail(settings.SMTP_FROM, [to_addr], msg.as_string())
        return True, None
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:256]


def _sms_provider_code() -> str:
    return (settings.SMS_PROVIDER or "mock").strip().lower()


def _send_sms(_to_number: str, _body: str) -> tuple[bool, str | None, str | None]:
    """SMS provider 接口。

    一期仅实现 mock/local；真实厂商接入保留到 provider 分支。
    """
    if not settings.SMS_ENABLED:
        return False, "SMS_DISABLED", None
    provider = _sms_provider_code()
    if provider in {"mock", "local"}:
        message_id = f"mock-{uuid.uuid4().hex[:12]}"
        logger.info("[SMS %s] to=%s body_len=%d msg=%s", provider, _to_number, len(_body), message_id)
        return True, None, message_id
    return False, "SMS_PROVIDER_NOT_CONFIGURED", None


def _coerce_sms_result(result: Any) -> tuple[bool, str | None, str | None]:
    """Keep old tests/monkeypatches compatible with the provider result shape."""
    if not isinstance(result, tuple):
        return False, "SMS_PROVIDER_INVALID_RESULT", None
    if len(result) == 2:
        ok, err = result
        return bool(ok), err, None
    if len(result) >= 3:
        ok, err, provider_message_id = result[:3]
        return bool(ok), err, provider_message_id
    return False, "SMS_PROVIDER_INVALID_RESULT", None


def _resolve_sms_number(user, student) -> str | None:
    """Resolve raw phone number for SMS gateway; never returns email fallback."""
    return decrypt_field(getattr(user, "phone_enc", None)) or decrypt_field(
        getattr(student, "phone_enc", None)
    )


async def _record_sms_attempt(
    db: AsyncSession,
    *,
    delivery: NoticeDelivery,
    status: str,
    target_handle: str | None,
    provider_message_id: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    await repo.add_delivery_attempt(
        db,
        delivery_id=delivery.id,
        provider=_sms_provider_code(),
        attempt_no=await repo.next_delivery_attempt_no(db, delivery.id),
        status=status,
        target_handle=target_handle,
        provider_message_id=provider_message_id,
        error_code=error_code,
        error_message=error_message,
    )


async def create_system_in_app_notice_for_student(
    db: AsyncSession,
    *,
    student_id: int,
    user_id: int | None,
    title: str,
    body_md: str,
    summary: str | None = None,
    category: str | None = "WORKFLOW",
    source_type: str = "SYSTEM",
    source_url: str | None = None,
    operator_id: int | None = None,
) -> NoticeDelivery:
    """Create a published one-student in-app notice and delivery in one transaction."""
    now = datetime.now(UTC)
    notice = await repo.create_notice(
        db,
        title=title,
        body_md=body_md,
        summary=summary,
        category=category,
        status=NOTICE_STATUS_PUBLISHED,
        source_type=source_type,
        source_url=source_url,
        target_rule={"student_ids": [student_id]},
        target_summary="单个学生站内通知",
        channels=CHANNEL_IN_APP,
        published_at=now,
        published_by=operator_id,
        created_by=operator_id,
        updated_by=operator_id,
    )
    batch = await repo.create_batch(
        db,
        notice_id=notice.id,
        batch_no=f"NB-{now.strftime('%y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
        channels=CHANNEL_IN_APP,
        target_rule_snapshot=notice.target_rule,
        target_count=1,
        success_count=1,
        failed_count=0,
        status="COMPLETED",
        note="系统自动站内通知",
        finished_at=now,
        created_by=operator_id,
    )
    delivery = await repo.add_delivery(
        db,
        batch_id=batch.id,
        notice_id=notice.id,
        student_id=student_id,
        user_id=user_id,
        channel=CHANNEL_IN_APP,
        status=DELIVERY_STATUS_SENT,
        sent_at=now,
    )
    return delivery


async def _get_wechat_access_token() -> str:
    global _wechat_access_token, _wechat_access_token_expires_at
    now = datetime.now(UTC)
    if (
        _wechat_access_token
        and _wechat_access_token_expires_at
        and _wechat_access_token_expires_at > now
    ):
        return _wechat_access_token
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            WX_ACCESS_TOKEN_URL,
            params={
                "grant_type": "client_credential",
                "appid": settings.WECHAT_APPID,
                "secret": settings.WECHAT_SECRET,
            },
        )
    resp.raise_for_status()
    payload = resp.json()
    errcode = payload.get("errcode")
    if errcode:
        raise BizError(
            f"微信 access_token 获取失败：{payload.get('errmsg') or errcode}",
            code=50202,
            http_status=502,
        )
    token = payload.get("access_token")
    if not token:
        raise BizError("微信 access_token 响应缺少 token", code=50202, http_status=502)
    expires_in = int(payload.get("expires_in") or 7200)
    _wechat_access_token = token
    _wechat_access_token_expires_at = now + timedelta(seconds=max(expires_in - 300, 60))
    return token


def _truncate_wechat_value(value: str | None, limit: int = 20) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _format_wechat_time(value: datetime | None = None) -> str:
    return (value or datetime.now(UTC)).strftime("%Y-%m-%d %H:%M")


def _wechat_request_work_order(*, notice_id: int, source_url: str | None) -> str:
    if source_url and ":" in source_url:
        prefix, value = source_url.split(":", 1)
        if prefix == "request" and value.strip():
            return value.strip()[:32]
    return str(notice_id)[:32]


def _build_wechat_subscribe_payload(
    *,
    openid: str,
    template_id: str,
    title: str,
    summary: str | None,
    scene: str,
    in_app_delivery: NoticeDelivery,
    source_url: str | None,
    page: str | None,
) -> dict[str, Any]:
    if scene == WECHAT_SUBSCRIBE_SCENE_WORKFLOW_REMINDER:
        data = {
            "thing4": {"value": _truncate_wechat_value(title, 20)},
            "thing1": {"value": _truncate_wechat_value(_format_wechat_time(), 20)},
            "thing2": {"value": _truncate_wechat_value(summary or title, 20)},
            "thing5": {"value": "信息学院学生服务"},
            "thing3": {"value": "请进入小程序查看详情"},
        }
    else:
        data = {
            "thing11": {"value": _truncate_wechat_value(title, 20)},
            "thing2": {"value": _truncate_wechat_value(summary or "状态更新", 20)},
            "time12": {"value": _format_wechat_time()},
            "character_string7": {
                "value": _wechat_request_work_order(
                    notice_id=in_app_delivery.notice_id,
                    source_url=source_url,
                )
            },
        }
    payload: dict[str, Any] = {
        "touser": openid,
        "template_id": template_id,
        "data": data,
    }
    if page:
        payload["page"] = page
    return payload


async def _send_wechat_subscribe_message(payload: dict[str, Any]) -> dict[str, Any]:
    access_token = await _get_wechat_access_token()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            WX_SUBSCRIBE_SEND_URL,
            params={"access_token": access_token},
            json=payload,
        )
    resp.raise_for_status()
    return resp.json()


async def send_wechat_subscribe_for_delivery(
    db: AsyncSession,
    *,
    in_app_delivery: NoticeDelivery,
    scene: str,
    title: str,
    summary: str | None,
    page: str | None = None,
) -> NoticeDelivery | None:
    """Send a WeChat Mini Program subscribe message without affecting IN_APP delivery."""
    template_id = (
        settings.WECHAT_SUBSCRIBE_REMINDER_TEMPLATE_ID
        if scene == WECHAT_SUBSCRIBE_SCENE_WORKFLOW_REMINDER
        else settings.WECHAT_SUBSCRIBE_REQUEST_TEMPLATE_ID
    )
    if not settings.WECHAT_SUBSCRIBE_ENABLED or not template_id:
        return None
    if in_app_delivery.user_id is None:
        return None
    user = await db.get(User, in_app_delivery.user_id)
    if user is None or not user.openid:
        return None
    notice = await db.get(Notice, in_app_delivery.notice_id)
    source_url = notice.source_url if notice else None
    auth = await repo.get_wechat_subscribe_authorization(
        db,
        user_id=user.id,
        template_id=template_id,
    )
    now = datetime.now(UTC)
    sent_ok = False
    status = DELIVERY_STATUS_SKIPPED
    err_code: str | None = None
    err_msg: str | None = None
    provider_msg_id: str | None = None
    if auth is None or auth.status != WECHAT_SUBSCRIBE_STATUS_ACCEPT:
        err_code = "WECHAT_SUBSCRIBE_NOT_AUTHORIZED"
    else:
        try:
            result = await _send_wechat_subscribe_message(
                _build_wechat_subscribe_payload(
                    openid=user.openid,
                    template_id=template_id,
                    title=title,
                    summary=summary,
                    scene=scene,
                    in_app_delivery=in_app_delivery,
                    source_url=source_url,
                    page=page,
                )
            )
            errcode = int(result.get("errcode") or 0)
            if errcode == 0:
                sent_ok = True
                status = DELIVERY_STATUS_SENT
                provider_msg_id = str(result.get("msgid") or "") or None
            else:
                status = DELIVERY_STATUS_FAILED
                err_code = str(errcode)
                err_msg = str(result.get("errmsg") or "微信订阅消息发送失败")[:512]
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "wechat subscribe send failed | notice_id=%s user_id=%s error=%s",
                in_app_delivery.notice_id,
                user.id,
                exc,
            )
            status = DELIVERY_STATUS_FAILED
            err_code = "WECHAT_SUBSCRIBE_SEND_FAILED"
            err_msg = str(exc)[:512]

    delivery = await repo.add_delivery(
        db,
        batch_id=in_app_delivery.batch_id,
        notice_id=in_app_delivery.notice_id,
        student_id=in_app_delivery.student_id,
        user_id=user.id,
        channel=CHANNEL_WECHAT_SUBSCRIBE,
        status=status,
        target_handle=user.openid,
        sent_at=now if sent_ok else None,
        error_code=err_code,
        error_message=err_msg,
    )
    await repo.add_delivery_attempt(
        db,
        delivery_id=delivery.id,
        provider=WECHAT_SUBSCRIBE_PROVIDER,
        attempt_no=1,
        status=(
            DELIVERY_ATTEMPT_STATUS_SENT
            if sent_ok
            else (
                DELIVERY_ATTEMPT_STATUS_SKIPPED
                if status == DELIVERY_STATUS_SKIPPED
                else DELIVERY_ATTEMPT_STATUS_FAILED
            )
        ),
        target_handle=user.openid,
        provider_message_id=provider_msg_id,
        error_code=err_code,
        error_message=err_msg,
    )
    return delivery


async def dispatch_notice(
    db: AsyncSession,
    notice_id: int,
    *,
    override_channels: list[str] | None,
    note: str | None,
    operator_id: int,
    operator_role: str | None,
) -> NoticeDeliveryBatch:
    notice = await repo.get_notice(db, notice_id)
    if notice is None:
        raise NotFoundError("通知不存在")
    if notice.status != NOTICE_STATUS_PUBLISHED:
        raise BizError("通知未发布，不能发送", code=40032)

    channels = override_channels or _str_to_channels(notice.channels)
    if not channels:
        raise BizError("未指定发送渠道", code=40033)

    students = await repo.resolve_target_students(db, notice.target_rule)
    batch = await repo.create_batch(
        db,
        notice_id=notice.id,
        batch_no=f"NB-{datetime.now(UTC).strftime('%y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
        channels=",".join(channels),
        target_rule_snapshot=notice.target_rule,
        target_count=len(students),
        note=note,
        created_by=operator_id,
    )

    success = 0
    failed = 0
    for stu in students:
        user = await repo.find_user_by_student_id(db, stu.id)
        for ch in channels:
            sent_ok = False
            err_code: str | None = None
            err_msg: str | None = None
            target_handle: str | None = None
            provider_msg_id: str | None = None

            if ch == CHANNEL_IN_APP:
                sent_ok = True  # 入库即送达
            elif ch == CHANNEL_EMAIL:
                if not stu.email:
                    err_code = "NO_EMAIL"
                else:
                    target_handle = stu.email
                    ok_, err = _send_email(stu.email, notice.title, notice.summary or notice.title)
                    sent_ok = ok_
                    if not ok_:
                        err_code = "SMTP_ERROR"
                        err_msg = err
            elif ch == CHANNEL_SMS:
                if not settings.SMS_ENABLED:
                    err_code = "SMS_DISABLED"
                else:
                    raw_phone = _resolve_sms_number(user, stu)
                    if not raw_phone:
                        err_code = "NO_PHONE"
                    else:
                        target_handle = mask_phone(raw_phone)
                        ok_, err, provider_msg_id = _coerce_sms_result(
                            _send_sms(raw_phone, notice.summary or notice.title)
                        )
                        sent_ok = ok_
                        if not ok_:
                            err_code = err or "SMS_ERROR"
                            err_msg = err
            else:
                err_code = "UNSUPPORTED_CHANNEL"

            status = DELIVERY_STATUS_SENT if sent_ok else (
                DELIVERY_STATUS_SKIPPED if err_code in ("NO_EMAIL", "NO_PHONE", "SMS_DISABLED", "UNSUPPORTED_CHANNEL")
                else DELIVERY_STATUS_FAILED
            )
            if sent_ok:
                success += 1
            elif status == DELIVERY_STATUS_FAILED:
                failed += 1

            delivery = await repo.add_delivery(
                db,
                batch_id=batch.id,
                notice_id=notice.id,
                student_id=stu.id,
                user_id=user.id if user else None,
                channel=ch,
                status=status,
                target_handle=target_handle,
                sent_at=datetime.now(UTC) if sent_ok else None,
                error_code=err_code,
                error_message=err_msg,
            )
            if ch == CHANNEL_SMS:
                await _record_sms_attempt(
                    db,
                    delivery=delivery,
                    status=(
                        DELIVERY_ATTEMPT_STATUS_SENT
                        if sent_ok
                        else (
                            DELIVERY_ATTEMPT_STATUS_SKIPPED
                            if status == DELIVERY_STATUS_SKIPPED
                            else DELIVERY_ATTEMPT_STATUS_FAILED
                        )
                    ),
                    target_handle=target_handle,
                    provider_message_id=provider_msg_id,
                    error_code=err_code,
                    error_message=None if sent_ok else err_msg,
                )

    batch.success_count = success
    batch.failed_count = failed
    batch.finished_at = datetime.now(UTC)
    if failed == 0:
        batch.status = "COMPLETED"
    elif success == 0:
        batch.status = "FAILED"
    else:
        batch.status = "PARTIAL"

    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE_BATCH",
        action="DISPATCH",
        entity_id=batch.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={
            "notice_id": notice.id,
            "channels": channels,
            "target": len(students),
            "success": success,
            "failed": failed,
        },
    )
    await db.commit()
    await db.refresh(batch)
    return batch


async def retry_notice_delivery(
    db: AsyncSession,
    delivery_id: int,
    *,
    operator_id: int,
    operator_role: str | None,
) -> NoticeDelivery:
    delivery = await repo.get_delivery(db, delivery_id)
    if delivery is None:
        raise NotFoundError("投递记录不存在")
    if delivery.channel != CHANNEL_SMS:
        raise BizError("仅 SMS 投递支持重试", code=40083)
    user = await db.get(User, delivery.user_id) if delivery.user_id else None
    student = await db.get(Student, delivery.student_id)
    if student is None:
        raise NotFoundError("投递目标学生不存在")

    raw_phone = _resolve_sms_number(user, student)
    target_handle = mask_phone(raw_phone) if raw_phone else None
    sent_ok = False
    err_code: str | None = None
    err_msg: str | None = None
    provider_msg_id: str | None = None
    if not settings.SMS_ENABLED:
        err_code = "SMS_DISABLED"
    elif not raw_phone:
        err_code = "NO_PHONE"
    else:
        sent_ok, err_msg, provider_msg_id = _coerce_sms_result(
            _send_sms(raw_phone, "通知短信重试")
        )
        if not sent_ok:
            err_code = err_msg or "SMS_ERROR"

    if sent_ok:
        delivery.status = DELIVERY_STATUS_SENT
        delivery.sent_at = datetime.now(UTC)
        delivery.error_code = None
        delivery.error_message = None
        attempt_status = DELIVERY_ATTEMPT_STATUS_SENT
    else:
        delivery.status = DELIVERY_STATUS_SKIPPED if err_code in {"SMS_DISABLED", "NO_PHONE"} else DELIVERY_STATUS_FAILED
        delivery.error_code = err_code
        delivery.error_message = err_msg
        attempt_status = (
            DELIVERY_ATTEMPT_STATUS_SKIPPED
            if delivery.status == DELIVERY_STATUS_SKIPPED
            else DELIVERY_ATTEMPT_STATUS_FAILED
        )
    delivery.target_handle = target_handle
    await _record_sms_attempt(
        db,
        delivery=delivery,
        status=attempt_status,
        target_handle=target_handle,
        provider_message_id=provider_msg_id,
        error_code=err_code,
        error_message=err_msg,
    )
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE_DELIVERY",
        action="RETRY_SMS",
        entity_id=delivery.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"status": delivery.status, "error_code": err_code},
    )
    await db.commit()
    await db.refresh(delivery)
    return delivery


async def mock_delivery_receipt(
    db: AsyncSession,
    delivery_id: int,
    *,
    receipt_status: str,
    operator_id: int,
    operator_role: str | None,
) -> NoticeDeliveryAttemptOut:
    delivery = await repo.get_delivery(db, delivery_id)
    if delivery is None:
        raise NotFoundError("投递记录不存在")
    if delivery.channel != CHANNEL_SMS:
        raise BizError("仅 SMS 投递支持回执回写", code=40084)
    attempts = sorted(delivery.attempts or [], key=lambda row: row.attempt_no, reverse=True)
    if attempts:
        attempt = attempts[0]
    else:
        attempt = await repo.add_delivery_attempt(
            db,
            delivery_id=delivery.id,
            provider=_sms_provider_code(),
            attempt_no=1,
            status=DELIVERY_ATTEMPT_STATUS_SKIPPED,
            target_handle=delivery.target_handle,
            error_code=delivery.error_code,
            error_message=delivery.error_message,
        )
    attempt.receipt_status = receipt_status
    attempt.receipt_at = datetime.now(UTC)
    await log_action(
        db,
        event_type="NOTICE",
        entity_code="NOTICE_DELIVERY",
        action="MOCK_RECEIPT",
        entity_id=delivery.id,
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"attempt_id": attempt.id, "receipt_status": receipt_status},
    )
    await db.commit()
    await db.refresh(attempt)
    return NoticeDeliveryAttemptOut.model_validate(attempt)


# ---------- Student inbox ----------
async def list_student_inbox(
    db: AsyncSession,
    user_id: int,
    student_id: int,
    *,
    unread_only: bool,
    page: int,
    size: int,
) -> tuple[list[StudentNoticeItem], int]:
    rows, total = await repo.list_notices_for_student(
        db, user_id, student_id, unread_only=unread_only, page=page, size=size
    )
    items: list[StudentNoticeItem] = []
    for notice, delivery in rows:
        items.append(
            StudentNoticeItem(
                id=notice.id,
                title=notice.title,
                summary=notice.summary,
                category=notice.category,
                is_pinned=notice.is_pinned,
                published_at=notice.published_at,
                read_at=delivery.read_at if delivery else None,
                delivery_id=delivery.id if delivery else None,
            )
        )
    return items, total


async def mark_read(
    db: AsyncSession, delivery_id: int, student_id: int
) -> None:
    d = await repo.mark_delivery_read(db, delivery_id, student_id)
    if d is None:
        raise NotFoundError("投递记录不存在")
    await db.commit()
