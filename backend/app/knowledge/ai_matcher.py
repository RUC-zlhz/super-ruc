"""知识条目检索匹配工具。

当前产品口径只做检索式回答；Claude 重排序函数保留为历史兼容代码，
但配置层会拒绝启用生成式问答。
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.knowledge.models import KnowledgeEntry

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "你是一个高校学生事务政策匹配助手。根据学生的问题，从下列候选知识条目中挑选最相关的 1-3 条，"
    "按相关度从高到低排序。只能使用给定候选，严禁编造条目。"
    "必须以 JSON 数组返回，每项字段：entry_id, score(0~1), reason(<=40 字)。"
    "若所有候选都不够匹配，返回空数组 []。"
)


def _normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.lower().strip())


def _query_tokens(query: str) -> list[str]:
    normalized = _normalize_query(query)
    if not normalized:
        return []

    parts = [
        token
        for token in re.split(r"[\s,，。.!！？?、:：;；/（）()【】\[\]“”\"'·-]+", normalized)
        if token
    ]
    tokens: list[str] = []
    seen: set[str] = set()
    for token in [normalized, *parts]:
        if len(token) < 2 or token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    return tokens


def _candidate_fields(entry: KnowledgeEntry) -> list[tuple[str, float, bool]]:
    tag_fields = [(tag.tag or "", 2.2, True) for tag in (entry.tags or [])]
    source_name = entry.source.source_name if entry.source else ""
    return [
        (entry.title or "", 3.0, True),
        (entry.summary or "", 1.8, False),
        (entry.applicable_condition or "", 1.2, False),
        (entry.required_materials or "", 1.2, False),
        (entry.process_steps or "", 1.2, False),
        (entry.body_md or "", 0.8, False),
        (source_name or "", 1.0, True),
        *tag_fields,
    ]


def _match_text_score(token: str, text: str, *, allow_reverse: bool = False) -> float:
    normalized_text = text.lower().strip()
    if not normalized_text:
        return 0.0
    if token in normalized_text:
        return 1.0
    if allow_reverse and len(normalized_text) <= 32 and normalized_text in token:
        return 0.75
    return 0.0


def _score_keyword(entry: KnowledgeEntry, query: str) -> float:
    """简易关键词评分：字符串子串命中权重。用于降级与初筛。"""
    tokens = _query_tokens(query)
    if not tokens:
        return 0.0
    score = 0.0
    for tk in tokens:
        for text, weight, allow_reverse in _candidate_fields(entry):
            score += weight * _match_text_score(tk, text, allow_reverse=allow_reverse)
    return score


def explain_keyword_match(entry: KnowledgeEntry, query: str) -> str:
    query_text = _normalize_query(query)
    matched: list[str] = []
    seen: set[str] = set()

    for tag in (entry.tags or []):
        value = (tag.tag or "").strip()
        normalized = value.lower()
        if not value:
            continue
        if normalized in query_text or query_text in normalized:
            if value not in seen:
                matched.append(value)
                seen.add(value)

    if matched:
        return f"命中关键词：{'、'.join(matched[:3])}"

    for tk in _query_tokens(query):
        for text, _, allow_reverse in _candidate_fields(entry):
            if _match_text_score(tk, text, allow_reverse=allow_reverse) > 0:
                if tk not in seen:
                    matched.append(tk)
                    seen.add(tk)
                break

    if matched:
        return f"命中关键词：{'、'.join(matched[:3])}"
    return "检索命中"


def _source_official_rank(entry: KnowledgeEntry) -> int:
    return 1 if entry.source and entry.source.is_official else 0


def rank_by_keyword(entries: list[KnowledgeEntry], query: str, top_k: int) -> list[tuple[KnowledgeEntry, float]]:
    scored = [(e, _score_keyword(e, query)) for e in entries]
    scored.sort(key=lambda x: (x[1], _source_official_rank(x[0]), x[0].id), reverse=True)
    scored = [p for p in scored if p[1] > 0][:top_k]
    return scored


async def rank_by_claude(
    entries: list[KnowledgeEntry], query: str, top_k: int
) -> list[dict[str, Any]] | None:
    """调用 Claude 对候选做语义匹配；失败返回 None 让调用方降级。"""
    if not settings.AI_QA_ENABLED:
        return None
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("AI_QA_ENABLED 已被配置层禁用；返回关键词匹配")
        return None

    try:
        # 延迟导入，避免未安装时启动失败
        import anthropic  # type: ignore
    except ImportError:
        logger.warning("anthropic 包未安装；返回关键词匹配")
        return None

    candidates = [
        {
            "entry_id": e.id,
            "title": e.title,
            "summary": e.summary or "",
            "category": e.category_code or "",
            "applicable_condition": (e.applicable_condition or "")[:280],
            "required_materials": (e.required_materials or "")[:280],
            "process_steps": (e.process_steps or "")[:280],
            "source_name": e.source.source_name if e.source else "",
            "source_is_official": bool(e.source and e.source.is_official),
        }
        for e in entries
    ]
    user_msg = (
        f"问题：{query}\n\n"
        f"候选知识条目（JSON）：\n{json.dumps(candidates, ensure_ascii=False)}\n\n"
        f"请挑选 top {top_k} 个，按 JSON 数组返回。"
    )

    try:
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        resp = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as e:  # 网络/鉴权等
        logger.exception("Claude 调用失败：%s", e)
        return None

    text = "".join(
        getattr(block, "text", "") for block in resp.content if getattr(block, "type", "") == "text"
    ).strip()
    if not text:
        return None
    # 允许模型回传纯 JSON 数组
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取首个 [ ... ] 片段
        start, end = text.find("["), text.rfind("]")
        if start < 0 or end <= start:
            logger.warning("Claude 回复非 JSON：%s", text[:200])
            return None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None

    if not isinstance(parsed, list):
        return None

    # 规范化输出
    normalized: list[dict[str, Any]] = []
    by_id = {e.id: e for e in entries}
    for item in parsed:
        if not isinstance(item, dict):
            continue
        try:
            eid = int(item.get("entry_id"))
        except (TypeError, ValueError):
            continue
        if eid not in by_id:
            continue
        try:
            score = float(item.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        normalized.append(
            {
                "entry_id": eid,
                "score": max(0.0, min(1.0, score)),
                "reason": str(item.get("reason", ""))[:80] or None,
            }
        )
    normalized.sort(
        key=lambda item: (
            item["score"],
            _source_official_rank(by_id[item["entry_id"]]),
        ),
        reverse=True,
    )
    return normalized[:top_k]
