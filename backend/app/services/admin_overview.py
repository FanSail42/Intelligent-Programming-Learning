"""Admin dashboard overview and operation logs (M09)."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.course import Course, CourseStatus, CourseStudent
from app.models.system import OperationLog
from app.models.user import User, UserRole, UserStatus

ACTION_LABELS: dict[str, str] = {
    "login": "用户登录",
    "user_create": "创建账号",
    "user_update": "更新账号",
    "user_delete": "删除账号",
    "ai_config_update": "更新 AI 配置",
}


def _count_users(db: Session, role: UserRole) -> dict[str, int]:
    base = db.query(User).filter(User.deleted == 0, User.role == role)
    total = base.count()
    active = base.filter(User.status == UserStatus.active).count()
    return {"total": total, "active": active, "disabled": total - active}


def build_admin_overview(db: Session) -> dict:
    students = _count_users(db, UserRole.student)
    teachers = _count_users(db, UserRole.teacher)

    course_total = db.query(Course).filter(Course.deleted == 0).count()
    course_published = (
        db.query(Course)
        .filter(Course.deleted == 0, Course.status == CourseStatus.published)
        .count()
    )
    enrollment_total = (
        db.query(CourseStudent)
        .filter(CourseStudent.deleted == 0)
        .count()
    )

    since_7d = datetime.now() - timedelta(days=7)
    login_7d = (
        db.query(OperationLog)
        .filter(
            OperationLog.deleted == 0,
            OperationLog.action == "login",
            OperationLog.created_at >= since_7d,
        )
        .count()
    )

    recent_logs = _list_operation_logs(db, page_num=1, page_size=8)[0]

    return {
        "students": students,
        "teachers": teachers,
        "courses": {
            "total": course_total,
            "published": course_published,
        },
        "enrollment_total": enrollment_total,
        "login_events_7d": login_7d,
        "recent_logs": recent_logs,
    }


def _log_to_dict(row: OperationLog, username: str | None) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "username": username,
        "action": row.action,
        "action_label": ACTION_LABELS.get(row.action, row.action),
        "ip": row.ip,
        "detail": row.detail,
        "created_at": row.created_at,
    }


def _list_operation_logs(
    db: Session,
    *,
    action: str | None = None,
    username: str | None = None,
    page_num: int = 1,
    page_size: int = 10,
) -> tuple[list[dict], int]:
    query = db.query(OperationLog, User.username).outerjoin(
        User, User.id == OperationLog.user_id
    ).filter(OperationLog.deleted == 0)

    if action and action.strip():
        query = query.filter(OperationLog.action == action.strip())
    if username and username.strip():
        query = query.filter(User.username.like(f"%{username.strip()}%"))

    total = query.count()
    rows = (
        query.order_by(OperationLog.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [_log_to_dict(log, uname) for log, uname in rows]
    return items, total


def list_operation_logs(
    db: Session,
    *,
    action: str | None = None,
    username: str | None = None,
    page_num: int = 1,
    page_size: int = 10,
) -> tuple[list[dict], int]:
    return _list_operation_logs(
        db,
        action=action,
        username=username,
        page_num=page_num,
        page_size=page_size,
    )
