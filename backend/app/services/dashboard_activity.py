from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.learning import KnowledgePoint, LearningEvent

EVENT_META: dict[str, dict[str, str]] = {
    "code_submit": {
        "title": "提交代码讲解",
        "icon": "code",
        "tone": "primary",
    },
    "code_analysis_error": {
        "title": "代码分析发现错误",
        "icon": "warning",
        "tone": "danger",
    },
    "chat_message": {
        "title": "AI 对话互动",
        "icon": "chat",
        "tone": "info",
    },
    "chat_no_context": {
        "title": "AI 对话缺少课程资料",
        "icon": "chat",
        "tone": "warning",
    },
    "material_view": {
        "title": "浏览课程资料",
        "icon": "material",
        "tone": "success",
    },
}

LANGUAGE_LABELS = {
    "python": "Python",
    "java": "Java",
    "cpp": "C++",
    "c": "C",
}


def _event_detail(event_type: str, payload: dict | None) -> str:
    payload = payload or {}
    if event_type == "code_submit":
        lang = payload.get("language")
        label = LANGUAGE_LABELS.get(str(lang), str(lang) if lang else "")
        return f"使用 {label} 提交代码" if label else "完成一次代码讲解提交"
    if event_type == "code_analysis_error":
        return "系统检测到语法/语义/运行问题，已记入错题本"
    if event_type == "chat_no_context":
        return "提问未命中课程资料，建议结合课件或向老师确认"
    if event_type == "chat_message":
        return "与 AI 助教完成一轮问答"
    if event_type == "material_view":
        name = payload.get("material_name") or payload.get("name")
        return f"查看资料：{name}" if name else "浏览了课程学习资料"
    return "学习行为已记录"


def build_recent_events(
    db: Session,
    *,
    user_id: int,
    course_id: int | None = None,
    limit: int = 10,
    days: int = 7,
) -> list[dict]:
    since = datetime.now() - timedelta(days=days)
    query = db.query(LearningEvent).filter(
        LearningEvent.user_id == user_id,
        LearningEvent.deleted == 0,
        LearningEvent.created_at >= since,
    )
    if course_id is not None:
        query = query.filter(LearningEvent.course_id == course_id)

    rows = (
        query.order_by(LearningEvent.created_at.desc(), LearningEvent.id.desc())
        .limit(limit)
        .all()
    )
    if not rows:
        return []

    course_ids = {row.course_id for row in rows if row.course_id}
    kp_ids = {row.kp_id for row in rows if row.kp_id}
    course_map = {
        c.id: c.name
        for c in db.query(Course)
        .filter(Course.id.in_(course_ids), Course.deleted == 0)
        .all()
    }
    kp_map = {
        k.id: k.name
        for k in db.query(KnowledgePoint)
        .filter(KnowledgePoint.id.in_(kp_ids), KnowledgePoint.deleted == 0)
        .all()
    }

    result: list[dict] = []
    for row in rows:
        event_type = row.event_type.value
        meta = EVENT_META.get(event_type, {"title": event_type, "icon": "default", "tone": "info"})
        result.append(
            {
                "event_type": event_type,
                "course_id": row.course_id,
                "course_name": course_map.get(row.course_id) if row.course_id else None,
                "kp_id": row.kp_id,
                "kp_name": kp_map.get(row.kp_id) if row.kp_id else None,
                "title": meta["title"],
                "detail": _event_detail(event_type, row.payload_json),
                "icon": meta["icon"],
                "tone": meta["tone"],
                "created_at": row.created_at,
            }
        )
    return result
