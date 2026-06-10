"""Wrong-book classification, detail extraction, and chart statistics."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.code import AnalysisResult, AnalysisStatus, CodeSubmission
from app.models.learning import KnowledgePoint, WrongQuestionBook
from app.schemas.code_analysis import AnalysisResultData
from app.services.code_helpers import enum_to_str, validate_result_data

CATEGORY_LABELS: dict[str, str] = {
    "syntax_error": "语法错误",
    "semantic_error": "语义与逻辑",
    "runtime_error": "运行与边界",
    "analysis_failed": "分析失败",
    "chat_no_context": "问答无上下文",
    "unknown": "其他",
}

CATEGORY_TIPS: dict[str, str] = {
    "syntax_error": "重点检查括号配对、缩进、关键字拼写与语句结尾符号。",
    "semantic_error": "梳理算法流程，确认循环条件、变量更新与边界是否会导致死循环或错误结果。",
    "runtime_error": "关注数组越界、空指针、除零与输入范围，必要时增加边界样例自测。",
    "analysis_failed": "代码可能过长或格式异常，可拆分函数后重新提交分析。",
    "chat_no_context": "提问时尽量关联课程资料，或先浏览相关章节再向 AI 提问。",
    "unknown": "回到原始记录查看详情，并尝试在代码讲解中复现问题。",
}

SOURCE_LABELS: dict[str, str] = {
    "code_submission": "代码讲解",
    "chat_message": "AI 对话",
}

SOURCE_TYPES_ORDER = ("code_submission", "chat_message")


def detect_category(
    source_type: str,
    *,
    analysis: AnalysisResult | None = None,
) -> str:
    if source_type == "chat_message":
        return "chat_no_context"
    if analysis is None:
        return "unknown"
    if analysis.status == AnalysisStatus.failed:
        return "analysis_failed"
    data = validate_result_data(analysis.result_json)
    if not data:
        return "unknown"
    if data.levels.syntax.score == "error":
        return "syntax_error"
    if data.levels.semantic.score == "error":
        return "semantic_error"
    if data.levels.runtime.score == "error":
        return "runtime_error"
    if data.levels.syntax.score == "warning":
        return "syntax_error"
    if data.levels.semantic.score == "warning":
        return "semantic_error"
    if data.levels.runtime.score == "warning":
        return "runtime_error"
    return "unknown"


def _collect_issues(data: AnalysisResultData) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for level_name in ("syntax", "semantic", "runtime"):
        level = getattr(data.levels, level_name)
        if level.score not in ("error", "warning"):
            continue
        for issue in level.issues:
            issues.append(
                {
                    "level": level_name,
                    "line": issue.line,
                    "message": issue.message,
                    "explanation": issue.explanation or issue.hint,
                }
            )
    return issues


def _collect_suggestions(data: AnalysisResultData) -> list[str]:
    tips: list[str] = []
    for level_name in ("syntax", "semantic", "runtime"):
        level = getattr(data.levels, level_name)
        tips.extend(level.suggestions)
    return tips[:6]


def build_item_detail(
    source_type: str,
    *,
    analysis: AnalysisResult | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    category = detect_category(source_type, analysis=analysis)
    detail: dict[str, Any] = {
        "category": category,
        "category_label": CATEGORY_LABELS.get(category, category),
        "summary": summary,
        "issues": [],
        "suggestions": [],
        "review_tip": CATEGORY_TIPS.get(category, CATEGORY_TIPS["unknown"]),
    }
    if analysis and analysis.status != AnalysisStatus.failed:
        data = validate_result_data(analysis.result_json)
        if data:
            detail["summary"] = detail["summary"] or data.summary
            detail["issues"] = _collect_issues(data)
            detail["suggestions"] = _collect_suggestions(data)
            if data.fixed_code:
                detail["has_fixed_code"] = True
    elif analysis and analysis.status == AnalysisStatus.failed:
        detail["summary"] = analysis.error_message or summary
    elif source_type == "chat_message":
        detail["summary"] = summary or "AI 未能基于课程资料回答，建议补充上下文后重试。"
    return detail


def _load_analysis_map(db: Session, submission_ids: list[int]) -> dict[int, AnalysisResult]:
    if not submission_ids:
        return {}
    rows = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.submission_id.in_(submission_ids), AnalysisResult.deleted == 0)
        .all()
    )
    return {row.submission_id: row for row in rows}


def _load_kp_map(db: Session, kp_ids: list[int]) -> dict[int, str]:
    if not kp_ids:
        return {}
    rows = (
        db.query(KnowledgePoint)
        .filter(KnowledgePoint.id.in_(kp_ids), KnowledgePoint.deleted == 0)
        .all()
    )
    return {row.id: row.name for row in rows}


def enrich_wrong_book_row(
    db: Session,
    row: WrongQuestionBook,
    *,
    analysis_map: dict[int, AnalysisResult] | None = None,
    kp_map: dict[int, str] | None = None,
) -> dict[str, Any]:
    lang: str | None = None
    summary: str | None = None
    analysis: AnalysisResult | None = None

    if row.source_type.value == "code_submission":
        sub = (
            db.query(CodeSubmission)
            .filter(CodeSubmission.id == row.ref_id, CodeSubmission.deleted == 0)
            .first()
        )
        if sub:
            lang = enum_to_str(sub.language)
            if analysis_map is not None:
                analysis = analysis_map.get(row.ref_id)
            else:
                analysis = (
                    db.query(AnalysisResult)
                    .filter(AnalysisResult.submission_id == row.ref_id, AnalysisResult.deleted == 0)
                    .first()
                )
            if analysis:
                from app.services.code_helpers import extract_summary

                summary = extract_summary(analysis.result_json)

    detail = build_item_detail(row.source_type.value, analysis=analysis, summary=summary)
    kp_name = None
    if row.kp_id:
        if kp_map is not None:
            kp_name = kp_map.get(row.kp_id)
        else:
            kp = (
                db.query(KnowledgePoint)
                .filter(KnowledgePoint.id == row.kp_id, KnowledgePoint.deleted == 0)
                .first()
            )
            kp_name = kp.name if kp else None

    return {
        "language": lang,
        "summary": detail.get("summary") or summary,
        "kp_name": kp_name,
        **detail,
    }


def backfill_wrong_book_course_ids(db: Session, user_id: int | None = None) -> None:
    """Fill course_id from knowledge_point for legacy rows (M05 submit without course)."""
    query = db.query(WrongQuestionBook).filter(
        WrongQuestionBook.course_id.is_(None),
        WrongQuestionBook.kp_id.isnot(None),
        WrongQuestionBook.deleted == 0,
    )
    if user_id is not None:
        query = query.filter(WrongQuestionBook.user_id == user_id)
    rows = query.all()
    if not rows:
        return
    kp_ids = {row.kp_id for row in rows if row.kp_id}
    kp_course = {
        kp.id: kp.course_id
        for kp in db.query(KnowledgePoint)
        .filter(KnowledgePoint.id.in_(kp_ids), KnowledgePoint.deleted == 0)
        .all()
    }
    for row in rows:
        course_id = kp_course.get(row.kp_id) if row.kp_id else None
        if course_id is not None:
            row.course_id = course_id
    db.flush()


def apply_wrong_book_course_filter(query, course_id: int | None, db: Session):
    """Match direct course_id or kp-linked rows when course_id was not set on insert."""
    if course_id is None:
        return query
    kp_ids = [
        row[0]
        for row in db.query(KnowledgePoint.id)
        .filter(KnowledgePoint.course_id == course_id, KnowledgePoint.deleted == 0)
        .all()
    ]
    if kp_ids:
        return query.filter(
            or_(
                WrongQuestionBook.course_id == course_id,
                and_(
                    WrongQuestionBook.course_id.is_(None),
                    WrongQuestionBook.kp_id.in_(kp_ids),
                ),
            )
        )
    return query.filter(WrongQuestionBook.course_id == course_id)


def build_wrong_book_stats(
    db: Session,
    user_id: int,
    *,
    course_id: int | None = None,
    days: int = 30,
) -> dict[str, Any]:
    backfill_wrong_book_course_ids(db, user_id=user_id)

    query = db.query(WrongQuestionBook).filter(
        WrongQuestionBook.user_id == user_id,
        WrongQuestionBook.deleted == 0,
    )
    query = apply_wrong_book_course_filter(query, course_id, db)
    rows = query.order_by(WrongQuestionBook.id.desc()).all()

    submission_ids = [
        row.ref_id for row in rows if row.source_type.value == "code_submission"
    ]
    analysis_map = _load_analysis_map(db, submission_ids)
    kp_ids = [row.kp_id for row in rows if row.kp_id]
    kp_map = _load_kp_map(db, kp_ids)

    total = len(rows)
    mastered = sum(1 for row in rows if row.mastered)
    unmastered = total - mastered

    by_category: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "unmastered": 0, "sample_issues": []}
    )
    by_source: dict[str, int] = defaultdict(int)
    by_language: dict[str, int] = defaultdict(int)
    by_kp: dict[int, dict[str, Any]] = defaultdict(lambda: {"total": 0, "unmastered": 0})

    since = datetime.now() - timedelta(days=days - 1)
    trend_map: dict[str, int] = defaultdict(int)
    for i in range(days):
        day = (since + timedelta(days=i)).strftime("%Y-%m-%d")
        trend_map[day] = 0

    for row in rows:
        analysis = (
            analysis_map.get(row.ref_id)
            if row.source_type.value == "code_submission"
            else None
        )
        category = detect_category(row.source_type.value, analysis=analysis)
        by_category[category]["total"] += 1
        if not row.mastered:
            by_category[category]["unmastered"] += 1

        detail = build_item_detail(row.source_type.value, analysis=analysis)
        for issue in detail.get("issues", [])[:2]:
            samples = by_category[category]["sample_issues"]
            msg = issue.get("message")
            if msg and msg not in samples and len(samples) < 3:
                samples.append(msg)

        by_source[row.source_type.value] += 1

        enriched = enrich_wrong_book_row(
            db, row, analysis_map=analysis_map, kp_map=kp_map
        )
        if enriched.get("language"):
            by_language[enriched["language"]] += 1

        if row.kp_id:
            kp_entry = by_kp[row.kp_id]
            kp_entry["kp_id"] = row.kp_id
            kp_entry["kp_name"] = kp_map.get(row.kp_id, f"知识点#{row.kp_id}")
            kp_entry["total"] += 1
            if not row.mastered:
                kp_entry["unmastered"] += 1

        if row.created_at:
            day_key = row.created_at.strftime("%Y-%m-%d")
            if day_key in trend_map:
                trend_map[day_key] += 1

    category_list = []
    for key, label in CATEGORY_LABELS.items():
        stat = by_category.get(key)
        if not stat or stat["total"] == 0:
            continue
        category_list.append(
            {
                "category": key,
                "label": label,
                "total": stat["total"],
                "unmastered": stat["unmastered"],
                "analysis": CATEGORY_TIPS.get(key, ""),
                "sample_issues": stat["sample_issues"],
            }
        )
    category_list.sort(key=lambda x: x["unmastered"], reverse=True)

    return {
        "summary": {
            "total": total,
            "mastered": mastered,
            "unmastered": unmastered,
            "mastery_rate": round(mastered / total * 100, 1) if total else 0,
        },
        "by_category": category_list,
        "by_source": [
            {
                "source_type": key,
                "label": SOURCE_LABELS[key],
                "count": by_source.get(key, 0),
            }
            for key in SOURCE_TYPES_ORDER
        ],
        "by_language": [
            {"language": k, "count": v}
            for k, v in sorted(by_language.items(), key=lambda x: -x[1])
        ],
        "by_kp": sorted(
            list(by_kp.values()),
            key=lambda x: x.get("unmastered", 0),
            reverse=True,
        )[:8],
        "trend": [{"date": d, "count": trend_map[d]} for d in sorted(trend_map.keys())],
        "mastered_pie": [
            {"name": "未掌握", "value": unmastered},
            {"name": "已掌握", "value": mastered},
        ],
    }
