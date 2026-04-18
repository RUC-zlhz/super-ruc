"""理论自测服务 — FR-005。

覆盖三种题型的判题、题库 CRUD、学生抽题与整卷提交。
"""
from __future__ import annotations

import logging
import random
import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_action
from app.core.exceptions import BizError, NotFoundError
from app.workflow.quiz_models import (
    QUIZ_DIFFICULTIES,
    QUIZ_TYPE_JUDGE,
    QUIZ_TYPE_MULTI,
    QUIZ_TYPE_SINGLE,
    QUIZ_TYPES,
    QuizQuestion,
    QuizRecord,
)

logger = logging.getLogger(__name__)


# ======================================================================
# A. 判题
# ======================================================================
def _normalize_keys(raw: str) -> list[str]:
    """把 'a, c,D' 变成 ['A','C','D'] 且去重。"""
    parts = [p.strip().upper() for p in (raw or "").split(",")]
    return sorted({p for p in parts if p})


def _normalize_judge(raw: str) -> str:
    val = (raw or "").strip().upper()
    if val in {"TRUE", "T", "1", "YES", "Y", "对", "正确"}:
        return "TRUE"
    if val in {"FALSE", "F", "0", "NO", "N", "错", "错误"}:
        return "FALSE"
    return val


def grade_answer(question: QuizQuestion, answer: str) -> bool:
    """根据题型对答案判分。"""
    if question.qtype == QUIZ_TYPE_SINGLE:
        return (answer or "").strip().upper() == (question.correct_key or "").strip().upper()
    if question.qtype == QUIZ_TYPE_MULTI:
        return _normalize_keys(answer) == _normalize_keys(question.correct_key)
    if question.qtype == QUIZ_TYPE_JUDGE:
        return _normalize_judge(answer) == _normalize_judge(question.correct_key)
    raise BizError(f"未知题型：{question.qtype}")


# ======================================================================
# B. 校验入参
# ======================================================================
def _validate_question_payload(
    qtype: str,
    options_json: list | None,
    correct_key: str,
    difficulty: str | None,
) -> None:
    if qtype not in QUIZ_TYPES:
        raise BizError(f"题型必须是 {QUIZ_TYPES} 之一")
    if difficulty is not None and difficulty not in QUIZ_DIFFICULTIES:
        raise BizError(f"难度必须是 {QUIZ_DIFFICULTIES} 之一")

    if qtype in (QUIZ_TYPE_SINGLE, QUIZ_TYPE_MULTI):
        if not options_json or len(options_json) < 2:
            raise BizError("选择题至少需要 2 个选项")
        keys = {str(opt.get("key", "")).strip().upper() for opt in options_json}
        if len(keys) != len(options_json) or "" in keys:
            raise BizError("选项 key 必须非空且唯一")
        correct = _normalize_keys(correct_key)
        if not correct:
            raise BizError("correct_key 不能为空")
        if any(k not in keys for k in correct):
            raise BizError("correct_key 必须是 options 中的 key")
        if qtype == QUIZ_TYPE_SINGLE and len(correct) != 1:
            raise BizError("单选题只能有一个正确答案")
        if qtype == QUIZ_TYPE_MULTI and len(correct) < 2:
            raise BizError("多选题至少两个正确答案")
    elif qtype == QUIZ_TYPE_JUDGE:
        if _normalize_judge(correct_key) not in {"TRUE", "FALSE"}:
            raise BizError("判断题正确答案必须是 TRUE 或 FALSE")


# ======================================================================
# C. 题库 CRUD（管理端）
# ======================================================================
async def create_question(
    db: AsyncSession,
    *,
    topic: str,
    qtype: str,
    stem: str,
    options_json: list | None,
    correct_key: str,
    explanation: str | None,
    difficulty: str | None,
    operator_id: int,
    operator_role: str | None,
) -> QuizQuestion:
    _validate_question_payload(qtype, options_json, correct_key, difficulty)
    # 多选正则化后再落库，避免大小写/顺序歧义
    stored_correct = (
        ",".join(_normalize_keys(correct_key))
        if qtype == QUIZ_TYPE_MULTI
        else (_normalize_judge(correct_key) if qtype == QUIZ_TYPE_JUDGE else correct_key.strip().upper())
    )
    row = QuizQuestion(
        topic=topic.strip(),
        qtype=qtype,
        stem=stem.strip(),
        options_json=options_json,
        correct_key=stored_correct,
        explanation=explanation,
        difficulty=difficulty,
        created_by=operator_id,
    )
    db.add(row)
    await db.flush()
    await log_action(
        db,
        event_type="QUIZ",
        entity_code="QUIZ_QUESTION",
        entity_id=row.id,
        action="CREATE",
        actor_user_id=operator_id,
        actor_role=operator_role,
        detail={"topic": topic, "qtype": qtype},
    )
    await db.commit()
    await db.refresh(row)
    return row


async def update_question(
    db: AsyncSession,
    question_id: int,
    *,
    topic: str | None = None,
    qtype: str | None = None,
    stem: str | None = None,
    options_json: list | None = None,
    correct_key: str | None = None,
    explanation: str | None = None,
    difficulty: str | None = None,
    is_active: bool | None = None,
    operator_id: int,
    operator_role: str | None,
) -> QuizQuestion:
    row = await db.get(QuizQuestion, question_id)
    if row is None:
        raise NotFoundError("题目不存在")

    new_qtype = qtype or row.qtype
    new_options = options_json if options_json is not None else row.options_json
    new_correct = correct_key if correct_key is not None else row.correct_key
    new_difficulty = difficulty if difficulty is not None else row.difficulty
    _validate_question_payload(new_qtype, new_options, new_correct, new_difficulty)

    if topic is not None:
        row.topic = topic.strip()
    if qtype is not None:
        row.qtype = qtype
    if stem is not None:
        row.stem = stem.strip()
    if options_json is not None:
        row.options_json = options_json
    if correct_key is not None:
        if new_qtype == QUIZ_TYPE_MULTI:
            row.correct_key = ",".join(_normalize_keys(correct_key))
        elif new_qtype == QUIZ_TYPE_JUDGE:
            row.correct_key = _normalize_judge(correct_key)
        else:
            row.correct_key = correct_key.strip().upper()
    if explanation is not None:
        row.explanation = explanation
    if difficulty is not None:
        row.difficulty = difficulty
    if is_active is not None:
        row.is_active = is_active

    await db.flush()
    await log_action(
        db,
        event_type="QUIZ",
        entity_code="QUIZ_QUESTION",
        entity_id=row.id,
        action="UPDATE",
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete_question(
    db: AsyncSession,
    question_id: int,
    *,
    operator_id: int,
    operator_role: str | None,
) -> None:
    """软删除：把 is_active 置 False，保留历史作答记录的外键完整性。"""
    row = await db.get(QuizQuestion, question_id)
    if row is None:
        raise NotFoundError("题目不存在")
    row.is_active = False
    await db.flush()
    await log_action(
        db,
        event_type="QUIZ",
        entity_code="QUIZ_QUESTION",
        entity_id=row.id,
        action="DELETE",
        actor_user_id=operator_id,
        actor_role=operator_role,
    )
    await db.commit()


async def list_questions(
    db: AsyncSession,
    *,
    topic: str | None = None,
    qtype: str | None = None,
    is_active: bool | None = None,
    keyword: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[QuizQuestion], int]:
    stmt = select(QuizQuestion)
    conds = []
    if topic:
        conds.append(QuizQuestion.topic == topic)
    if qtype:
        conds.append(QuizQuestion.qtype == qtype)
    if is_active is not None:
        conds.append(QuizQuestion.is_active.is_(is_active))
    if keyword:
        conds.append(QuizQuestion.stem.ilike(f"%{keyword}%"))
    if conds:
        stmt = stmt.where(and_(*conds))

    total = (
        await db.execute(
            select(func.count()).select_from(stmt.subquery())
        )
    ).scalar_one()

    rows = (
        await db.execute(
            stmt.order_by(QuizQuestion.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
    ).scalars().all()
    return list(rows), int(total)


# ======================================================================
# D. 学生抽题 + 提交
# ======================================================================
async def draw_quiz(
    db: AsyncSession,
    *,
    topic: str | None,
    qtype: str | None,
    difficulty: str | None,
    limit: int,
) -> tuple[str, list[QuizQuestion]]:
    """随机抽取 limit 道有效题。返回 batch_id 与题目列表（不含答案）。"""
    stmt = select(QuizQuestion).where(QuizQuestion.is_active.is_(True))
    if topic:
        stmt = stmt.where(QuizQuestion.topic == topic)
    if qtype:
        stmt = stmt.where(QuizQuestion.qtype == qtype)
    if difficulty:
        stmt = stmt.where(QuizQuestion.difficulty == difficulty)

    rows = list((await db.execute(stmt)).scalars().all())
    if not rows:
        raise NotFoundError("无匹配题目，请联系管理员补充题库")
    random.shuffle(rows)
    picked = rows[: max(1, min(limit, len(rows)))]
    batch_id = uuid.uuid4().hex
    return batch_id, picked


async def submit_quiz(
    db: AsyncSession,
    *,
    student_id: int,
    batch_id: str,
    answers: list[dict],
    operator_id: int,
) -> dict:
    """整卷提交：逐题判分 + 落 quiz_records + 返回汇总。

    answers = [{"question_id": int, "answer": str}, ...]
    返回 {"batch_id", "total", "correct", "score", "items":[...]}。
    """
    if not answers:
        raise BizError("至少需要提交一道题")

    q_ids = [a["question_id"] for a in answers]
    rows = (
        await db.execute(select(QuizQuestion).where(QuizQuestion.id.in_(q_ids)))
    ).scalars().all()
    q_map = {q.id: q for q in rows}
    missing = set(q_ids) - set(q_map.keys())
    if missing:
        raise NotFoundError(f"题目不存在：{sorted(missing)}")

    now = datetime.now(timezone.utc)
    per_score = 100 // len(answers) if len(answers) else 0
    items: list[dict] = []
    correct_count = 0

    for a in answers:
        q = q_map[a["question_id"]]
        answer_text = str(a.get("answer", ""))
        is_correct = grade_answer(q, answer_text)
        if is_correct:
            correct_count += 1
        record = QuizRecord(
            student_id=student_id,
            question_id=q.id,
            batch_id=batch_id,
            answer=answer_text,
            is_correct=is_correct,
            score=per_score if is_correct else 0,
            submitted_at=now,
        )
        db.add(record)
        items.append(
            {
                "question_id": q.id,
                "is_correct": is_correct,
                "correct_key": q.correct_key,
                "explanation": q.explanation,
            }
        )

    await db.flush()

    total = len(answers)
    score = correct_count * per_score
    await log_action(
        db,
        event_type="QUIZ",
        entity_code="QUIZ_BATCH",
        action="SUBMIT",
        actor_user_id=operator_id,
        detail={
            "batch_id": batch_id,
            "total": total,
            "correct": correct_count,
            "score": score,
        },
    )
    await db.commit()
    return {
        "batch_id": batch_id,
        "total": total,
        "correct": correct_count,
        "score": score,
        "items": items,
    }


async def list_my_records(
    db: AsyncSession,
    *,
    student_id: int,
    batch_id: str | None = None,
    limit: int = 100,
) -> list[QuizRecord]:
    stmt = select(QuizRecord).where(QuizRecord.student_id == student_id)
    if batch_id:
        stmt = stmt.where(QuizRecord.batch_id == batch_id)
    stmt = stmt.order_by(QuizRecord.submitted_at.desc()).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)
